# Copyright 2016 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import time
from collections import namedtuple

import dns
from oslo_config import cfg
from oslo_log import log as logging

from designate.i18n import _LI
from designate.i18n import _LW
from designate.worker import utils as wutils
from designate.worker.tasks import base
from designate import exceptions
from designate import utils

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def percentage(part, whole):
    if whole == 0:
        return 0
    return 100 * float(part) / float(whole)


class ThresholdMixin(object):
    @property
    def threshold(self):
        if not hasattr(self, '_threshold') or self._threshold is None:
            self._threshold = CONF['service:worker'].threshold_percentage
        return self._threshold

    def _compare_threshold(self, successes, total):
        p = percentage(successes, total)
        return p >= self.threshold


######################
# CRUD Zone Operations
######################

class ZoneActionOnTarget(base.Task):
    """
    Perform a Create/Update/Delete of the zone on a pool target

    :return: Success/Failure of the target action (bool)
    """
    def __init__(self, executor, context, zone, target):
        super(ZoneActionOnTarget, self).__init__(executor)
        self.zone = zone
        self.action = zone.action
        self.target = target
        self.context = context
        self.task_name = 'ZoneActionOnTarget-%s' % self.action.title()

    def __call__(self):
        LOG.debug("Attempting %(action)s zone %(zone)s on %(target)s",
                  {'action': self.action, 'zone': self.zone.name,
                   'target': self.target})

        for retry in range(0, self.max_retries):
            try:
                if self.action == 'CREATE':
                    self.target.backend.create_zone(self.context, self.zone)
                    SendNotify(self.executor, self.zone, self.target)()
                elif self.action == 'UPDATE':
                    self.target.backend.update_zone(self.context, self.zone)
                    SendNotify(self.executor, self.zone, self.target)()
                elif self.action == 'DELETE':
                    self.target.backend.delete_zone(self.context, self.zone)

                LOG.debug("Successful %s zone %s on %s",
                          self.action, self.zone.name, self.target)
                return True
            except Exception as e:
                LOG.info(_LI('Failed to %(action)s zone %(zone)s on '
                             'target %(target)s on attempt %(attempt)d, '
                             'Error: %(error)s.'), {'action': self.action,
                             'zone': self.zone.name, 'target': self.target.id,
                             'attempt': retry + 1, 'error': str(e)})
                time.sleep(self.retry_interval)

        return False


class SendNotify(base.Task):
    """
    Send a NOTIFY packet and retry on failure to receive

    :raises: Various exceptions from dnspython
    :return: Success/Failure delivering the notify (bool)
    """
    def __init__(self, executor, zone, target):
        super(SendNotify, self).__init__(executor)
        self.zone = zone
        self.target = target

    def __call__(self):
        if not CONF['service:worker'].notify:
            # TODO(timsim): Remove this someday
            return True

        host = self.target.options.get('host')
        port = int(self.target.options.get('port'))

        try:
            wutils.notify(self.zone.name, host, port=port)
            LOG.debug('Sent NOTIFY to %(host)s:%(port)s for zone '
                      '%(zone)s', {'host': host,
                      'port': port, 'zone': self.zone.name})
            return True
        except dns.exception.Timeout as e:
            LOG.info(_LI('Timeout on NOTIFY to %(host)s:%(port)s for zone '
                      '%(zone)s'), {'host': host,
                      'port': port, 'zone': self.zone.name})
            raise e

        return False


class ZoneActor(base.Task, ThresholdMixin):
    """
    Orchestrate the Create/Update/Delete action on targets and update status
    if it fails. We would only update status here on an error to perform the
    necessary backend CRUD action. If there's a failure in propagating all
    the way to the nameservers, that will be picked up in a ZonePoller.

    :return: Whether the ActionOnTarget got to a satisfactory number
             of targets (bool)
    """
    def __init__(self, executor, context, pool, zone):
        self.executor = executor
        self.context = context
        self.pool = pool
        self.zone = zone

    def _validate_action(self, action):
        if action not in ['CREATE', 'UPDATE', 'DELETE']:
            raise Exception('Bad Action')

    def _execute(self):
        results = self.executor.run([
            ZoneActionOnTarget(self.executor, self.context, self.zone, target)
            for target in self.pool.targets
        ])
        return results

    def _update_status(self):
        task = UpdateStatus(self.executor, self.context, self.zone)
        task()

    def _threshold_met(self, results):
        # If we don't meet threshold for action, update status
        met_action_threshold = self._compare_threshold(
            results.count(True), len(results))

        if not met_action_threshold:
            LOG.info(_LI('Could not %(action)s %(zone)s on enough targets. '
                     'Updating status to ERROR'),
                     {'action': self.zone.action, 'zone': self.zone.name})
            self.zone.status = 'ERROR'
            self._update_status()
            return False
        return True

    def __call__(self):
        self._validate_action(self.zone.action)
        results = self._execute()
        return self._threshold_met(results)


class ZoneAction(base.Task):
    """
    Orchestrate a complete Create/Update/Delete of the specified zone on the
    pool and the polling for the change

    :return: Success/Failure of the change propagating to a satisfactory
             number of nameservers (bool)
    """
    def __init__(self, executor, context, pool, zone, action):
        super(ZoneAction, self).__init__(executor)
        self.context = context
        self.pool = pool
        self.zone = zone
        self.action = action
        self.task_name = 'ZoneAction-%s' % self.action.title()

    def _wait_for_nameservers(self):
        """
        Pause to give the nameservers a chance to update
        """
        time.sleep(self.delay)

    def _zone_action_on_targets(self):
        actor = ZoneActor(
            self.executor, self.context, self.pool, self.zone
        )
        return actor()

    def _poll_for_zone(self):
        poller = ZonePoller(self.executor, self.context, self.pool, self.zone)
        return poller()

    def __call__(self):
        LOG.info(_LI('Attempting %(action)s on zone %(name)s'),
                {'action': self.action, 'name': self.zone.name})

        if not self._zone_action_on_targets():
            return False

        self._wait_for_nameservers()

        if self.action == 'DELETE':
            self.zone.serial = 0

        if not self._poll_for_zone():
            return False

        return True


##############
# Zone Polling
##############

DNSQueryResult = namedtuple(
    'DNSQueryResult', [
        'positives',
        'no_zones',
        'consensus_serial',
        'results'
    ]
)


def parse_query_results(results, zone):
    """
    results is a [serial/None, ...]
    """
    delete = zone.action == 'DELETE'
    positives = 0
    no_zones = 0
    low_serial = 0

    for serial in results:
        if serial is None:
            # Intentionally don't handle None
            continue
        if delete:
            if serial == 0:
                no_zones += 1
                positives += 1
        else:
            if serial >= zone.serial:
                positives += 1

                # Update the lowest valid serial aka the consensus
                # serial
                if low_serial == 0 or serial < low_serial:
                    low_serial = serial
            else:
                if serial == 0:
                    no_zones += 1

    result = DNSQueryResult(positives, no_zones, low_serial, results)
    LOG.debug('Results for polling %(zone)s-%(serial)d: %(tup)s',
              {'zone': zone.name, 'serial': zone.serial, 'tup': result})
    return result


class PollForZone(base.Task):
    """
    Send SOA queries to a nameserver for the zone. This could be a serial
    number, or that the zone does not exist.

    :return: A serial number if the zone exists (int), None if the zone
    does not exist
    """
    def __init__(self, executor, zone, ns):
        super(PollForZone, self).__init__(executor)
        self.zone = zone
        self.ns = ns

    def _get_serial(self):
        return wutils.get_serial(
            self.zone.name,
            self.ns.host,
            port=self.ns.port
        )

    def __call__(self):
        LOG.debug('Polling for zone %(zone)s serial %(serial)s on %(ns)s',
                  {'zone': self.zone.name, 'serial': self.zone.serial,
                  'ns': self.ns})

        try:
            serial = self._get_serial()
            LOG.debug('Found serial %(serial)d on %(host)s for zone '
                      '%(zone)s', {'serial': serial, 'host': self.ns.host,
                      'zone': self.zone.name})
            return serial
            # TODO(timsim): cache if it's higher than cache
        except dns.exception.Timeout:
            LOG.info(_LI('Timeout polling for serial %(serial)d '
                '%(host)s for zone %(zone)s'), {'serial': self.zone.serial,
                'host': self.ns.host, 'zone': self.zone.name})
        except Exception as e:
            LOG.warning(_LW('Unexpected failure polling for serial %(serial)d '
                '%(host)s for zone %(zone)s. Error: %(error)s'),
                {'serial': self.zone.serial, 'host': self.ns.host,
                 'zone': self.zone.name, 'error': str(e)})

        return None


class ZonePoller(base.Task, ThresholdMixin):
    """
    Orchestrate polling for a change across the nameservers in a pool
    and compute the proper zone status, and update it.

    :return: Whether the change was successfully polled for on a satisfactory
             number of nameservers in the pool
    """
    def __init__(self, executor, context, pool, zone):
        self.executor = executor
        self.context = context
        self.pool = pool
        self.zone = zone

    def _update_status(self):
        task = UpdateStatus(self.executor, self.context, self.zone)
        task()

    def _do_poll(self):
        """
        Poll nameservers, compute basic success, return detailed query results
        for further computation. Retry on failure to poll (meet threshold for
        success).

        :return: a DNSQueryResult object with the results of polling
        """
        nameservers = self.pool.nameservers

        retry_interval = self.retry_interval
        query_result = DNSQueryResult(0, 0, 0, 0)
        results = []
        for retry in range(0, self.max_retries):
            results = self.executor.run([
                PollForZone(self.executor, self.zone, ns)
                for ns in nameservers
            ])

            query_result = parse_query_results(results, self.zone)

            if self._compare_threshold(query_result.positives, len(results)):
                LOG.debug('Successful poll for %(zone)s',
                         {'zone': self.zone.name})
                break

            LOG.debug('Unsuccessful poll for %(zone)s on attempt %(n)d',
                      {'zone': self.zone.name, 'n': retry + 1})
            time.sleep(retry_interval)

        return query_result

    def _on_failure(self, error_status):
        LOG.info(_LI('Could not find %(serial)s for %(zone)s on enough '
                     'nameservers.'),
                 {'serial': self.zone.serial, 'zone': self.zone.name})

        self.zone.status = error_status

        if error_status == 'NO_ZONE':
            self.zone.action = 'CREATE'

        return False

    def _on_success(self, query_result, status):
        # TODO(timsim): Change this back to active, so dumb central
        self.zone.status = status
        LOG.debug('Found success for %(zone)s at serial %(serial)d',
                  {'zone': self.zone.name, 'serial': self.zone.serial})

        self.zone.serial = query_result.consensus_serial
        return True

    def _threshold_met(self, query_result):
        """
        Compute whether the thresholds were met. Provide an answer,
        and an error status if there was a failure.

        The error status should be either:

         - ERROR: the operation failed
         - NO_ZONE: the zone doesn't exist on enough name servers

        :return: Whether the polling was successful, and a status
                 describing the state (bool, str)
        """

        total = len(query_result.results)
        is_not_delete = self.zone.action != 'DELETE'

        # Ensure if we don't have too many nameservers that
        # don't have the zone.
        over_no_zone_threshold = self._compare_threshold(
            (total - query_result.no_zones), total
        )

        if not over_no_zone_threshold and is_not_delete:
            return False, 'NO_ZONE'

        # The action should have been pushed out to a minimum
        # number of nameservers.
        if not self._compare_threshold(query_result.positives, total):
            return False, 'ERROR'

        # We have success of the action on the nameservers and enough
        # nameservers have the zone to call this a success.
        return True, 'SUCCESS'

    def __call__(self):
        query_result = self._do_poll()
        result = None
        success, status = self._threshold_met(query_result)
        if success:
            result = self._on_success(query_result, status)
        else:
            result = self._on_failure(status)

        self._update_status()
        return result


###################
# Status Management
###################

class UpdateStatus(base.Task):
    """
    Inspect the zone object and call central's update_status method.
    Some logic is applied that could be removed when central's logic
    for updating status is sane

    :return: No return value
    """
    def __init__(self, executor, context, zone):
        super(UpdateStatus, self).__init__(executor)
        self.zone = zone
        self.context = context

    def __call__(self):
        # TODO(timsim): Fix this when central's logic is sane
        if self.zone.action == 'DELETE' and self.zone.status != 'ERROR':
            self.zone.action = 'NONE'
            self.zone.status = 'NO_ZONE'

        if self.zone.status == 'SUCCESS':
            self.zone.action = 'NONE'

        # This log message will always have action as NONE and then we
        # don't use the action in the update_status call.
        LOG.debug('Updating status for %(zone)s to %(status)s:%(action)s',
                  {'zone': self.zone.name, 'status': self.zone.status,
                   'action': self.zone.action})

        self.central_api.update_status(
            self.context,
            self.zone.id,
            self.zone.status,
            self.zone.serial
        )


###################
# Periodic Recovery
###################

class RecoverShard(base.Task):
    """
    Given a beginning and ending shard, create the work to recover any
    zones in an undesirable state within those shards.

    :return: No return value
    """
    def __init__(self, executor, context, begin, end):
        super(RecoverShard, self).__init__(executor)
        self.context = context
        self.begin_shard = begin
        self.end_shard = end

    def _get_zones(self):
        criterion = {
            'shard': "BETWEEN %s,%s" % (self.begin_shard, self.end_shard),
            'status': 'ERROR'
        }
        error_zones = self.storage.find_zones(self.context, criterion)

        # Include things that have been hanging out in PENDING
        # status for longer than they should
        # Generate the current serial, will provide a UTC Unix TS.
        current = utils.increment_serial()
        stale_criterion = {
            'shard': "BETWEEN %s,%s" % (self.begin_shard, self.end_shard),
            'status': 'PENDING',
            'serial': "<%s" % (current - self.max_prop_time)
        }

        stale_zones = self.storage.find_zones(self.context, stale_criterion)
        if stale_zones:
            LOG.warn(_LW('Found %(len)d zones PENDING for more than %(sec)d '
                         'seconds'), {'len': len(stale_zones),
                                      'sec': self.max_prop_time})
            error_zones.extend(stale_zones)

        return error_zones

    def __call__(self):
        zones = self._get_zones()

        for zone in zones:
            if zone.action == 'CREATE':
                self.worker_api.create_zone(self.context, zone)
            elif zone.action == 'UPDATE':
                self.worker_api.update_zone(self.context, zone)
            elif zone.action == 'DELETE':
                self.worker_api.delete_zone(self.context, zone)


##############
# Zone Exports
##############

class ExportZone(base.Task):
    """
    Given a zone, determine the proper method, based on size, and
    perform the necessary actions to Export the zone, and update the
    export row in storage via central.
    """
    def __init__(self, executor, context, zone, export):
        super(ExportZone, self).__init__(executor)
        self.context = context
        self.zone = zone
        self.export = export

    def _synchronous_export(self):
        return CONF['service:worker'].export_synchronous

    def _determine_export_method(self, context, export, size):
        # NOTE(timsim):
        # The logic here with swift will work like this:
        #     cfg.CONF.export_swift_enabled:
        #         An export will land in their swift container, even if it's
        #         small, but the link that comes back will be the synchronous
        #         link (unless export_syncronous is False, in which case it
        #         will behave like the next option)
        #     cfg.CONF.export_swift_preffered:
        #         The link that the user gets back will always be the swift
        #         container, and status of the export resource will depend
        #         on the Swift process.
        #     If the export is too large for synchronous, or synchronous is not
        #     enabled and swift is not enabled, it will fall through to ERROR
        # swift = False
        synchronous = self._synchronous_export()

        if synchronous:
            try:
                self.quota.limit_check(
                        context, context.tenant, api_export_size=size)
            except exceptions.OverQuota:
                LOG.debug('Zone Export too large to perform synchronously')
                export.status = 'ERROR'
                export.message = 'Zone is too large to export'
                return export

            export.location = \
                'designate://v2/zones/tasks/exports/%(eid)s/export' % \
                {'eid': export.id}

            export.status = 'COMPLETE'
        else:
            LOG.debug('No method found to export zone')
            export.status = 'ERROR'
            export.message = 'No suitable method for export'

        return export

    def __call__(self):
        criterion = {'zone_id': self.zone.id}
        count = self.storage.count_recordsets(self.context, criterion)

        export = self._determine_export_method(
            self.context, self.export, count)

        self.central_api.update_zone_export(self.context, export)

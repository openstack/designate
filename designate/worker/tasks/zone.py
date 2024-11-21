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
from collections import namedtuple
import errno
import time

import dns
from oslo_log import log as logging
from oslo_utils import timeutils

from designate.common import constants
import designate.conf
from designate import dnsutils
from designate import exceptions
from designate import objects
from designate.worker.tasks import base


LOG = logging.getLogger(__name__)
CONF = designate.conf.CONF

######################
# CRUD Zone Operations
######################


class ZoneActionOnTarget(base.Task):
    """
    Perform a Create/Update/Delete of the zone on a pool target

    :return: Success/Failure of the target action (bool)
    """

    def __init__(self, executor, context, zone, target, zone_params):
        super().__init__(executor)
        self.zone = zone
        self.action = zone.action
        self.target = target
        self.context = context
        self.task_name = 'ZoneActionOnTarget-%s' % self.action.title()
        self.zone_params = zone_params

    def __call__(self):
        LOG.debug(
            'Attempting to %(action)s zone_name=%(zone_name)s '
            'zone_id=%(zone_id)s on target=%(target)s',
            {
                'action': self.action,
                'zone_name': self.zone.name,
                'zone_id': self.zone.id,
                'target': self.target,
            }
        )

        # Check whether a catalog zone exists for this pool
        catalog_zone = None
        pool = self.storage.find_pool(
            self.context, criterion={'id': self.zone.pool_id})
        try:
            catalog_zone = self.storage.get_catalog_zone(
                self.context, pool)
        except exceptions.ZoneNotFound:
            pass

        for retry in range(0, self.max_retries):
            try:
                if catalog_zone is None:
                    if self.action == 'CREATE':
                        self.target.backend.create_zone(
                            self.context, self.zone)
                        SendNotify(self.executor, self.zone, self.target)()
                    elif self.action == 'DELETE' and catalog_zone is None:
                        self.target.backend.delete_zone(
                            self.context, self.zone, self.zone_params)
                    else:
                        self.target.backend.update_zone(
                            self.context, self.zone)
                        SendNotify(self.executor, self.zone, self.target)()
                else:
                    if (
                        self.action == 'CREATE' or self.action == 'DELETE' or
                        self.zone.type == constants.ZONE_CATALOG
                    ):
                        # Member zone created or deleted, or catalog zone
                        # itself modified, NOTIFY via catalog
                        SendNotify(self.executor, catalog_zone, self.target)()
                    else:
                        # Member zone updated
                        SendNotify(self.executor, self.zone, self.target)()

                LOG.debug(
                    'Successfully performed %(action)s for '
                    'zone_name=%(zone_name)s zone_id=%(zone_id)s '
                    'on target=%(target)s',
                    {
                        'action': self.action,
                        'zone_name': self.zone.name,
                        'zone_id': self.zone.id,
                        'target': self.target,
                    }
                )
                return True
            except Exception as e:
                LOG.info(
                    'Failed to %(action)s zone_name=%(zone_name)s '
                    'zone_id=%(zone_id)s on target=%(target)s on '
                    'attempt=%(attempt)d Error=%(error)s',
                    {
                        'action': self.action,
                        'zone_name': self.zone.name,
                        'zone_id': self.zone.id,
                        'target': self.target,
                        'attempt': retry + 1,
                        'error': str(e),
                    }
                )

            time.sleep(self.retry_interval)

        return False


class SendNotify(base.Task):
    """
    Send a NOTIFY packet and retry on failure to receive

    :raises: Various exceptions from dnspython
    :return: Success/Failure delivering the notify (bool)
    """

    def __init__(self, executor, zone, target):
        super().__init__(executor)
        self.zone = zone
        self.target = target

    def __call__(self):
        host = self.target.options.get('host', '127.0.0.1')
        port = int(self.target.options.get('port', '53'))

        try:
            dnsutils.notify(self.zone.name, host, port=port)
            LOG.debug(
                'Sent NOTIFY to host=%(host)s:%(port)s for '
                'zone_name=%(zone_name)s zone_id=%(zone_id)s',
                {
                    'host': host,
                    'port': port,
                    'zone_name': self.zone.name,
                    'zone_id': self.zone.id,
                }
            )

            return True
        except dns.exception.Timeout as e:
            LOG.info(
                'Timeout on NOTIFY to host=%(host)s:%(port)s for '
                'zone_name=%(zone_name)s zone_id=%(zone_id)s',
                {
                    'host': host,
                    'port': port,
                    'zone_name': self.zone.name,
                    'zone_id': self.zone.id,
                }
            )
            raise e

        return False


class ZoneXfr(base.Task):
    """
    Perform AXFR on Zone
    """

    def __init__(self, executor, context, zone, servers=None):
        super().__init__(executor)
        self.context = context
        self.zone = zone
        self.servers = servers

    def __call__(self):
        if self.zone.type != constants.ZONE_SECONDARY:
            return

        servers = self.servers or self.zone.masters
        if isinstance(servers, objects.ListObjectMixin):
            servers = servers.to_list()

        try:
            dnspython_zone = dnsutils.do_axfr(self.zone.name, servers)
        except exceptions.XFRFailure as e:
            LOG.warning(e)
            return

        self.zone.update(dnsutils.from_dnspython_zone(dnspython_zone))
        self.zone.transferred_at = timeutils.utcnow()
        self.zone.obj_reset_changes(['name', 'masters'], recursive=True)
        self.central_api.update_zone(
            self.context, self.zone, increment_serial=False
        )


class ZoneActor(base.Task):
    """
    Orchestrate the Create/Update/Delete action on targets and update status
    if it fails. We would only update status here on an error to perform the
    necessary backend CRUD action. If there's a failure in propagating all
    the way to the nameservers, that will be picked up in a ZonePoller.

    :return: Whether the ActionOnTarget got to a satisfactory number
             of targets (bool)
    """

    def __init__(self, executor, context, pool, zone, zone_params=None):
        super().__init__(executor)
        self.context = context
        self.pool = pool
        self.zone = zone
        self.zone_params = zone_params

    def _execute(self):
        results = self.executor.run([
            ZoneActionOnTarget(self.executor, self.context, self.zone, target,
                               self.zone_params)
            for target in self.pool.targets
        ])
        return results

    def _update_status(self):
        task = UpdateStatus(self.executor, self.context, self.zone)
        task()

    def _threshold_met(self, results):
        # If we don't meet threshold for action, update status
        success = results.count(True)
        total = len(results)
        met_action_threshold = self.compare_threshold(success, total)

        if not met_action_threshold:
            LOG.info(
                'Could not %(action)s zone_name=%(zone_name)s '
                'zone_id=%(zone_id)s success=%(success)s '
                'total=%(total)s on enough targets. Updating status to ERROR',
                {
                    'action': self.zone.action,
                    'zone_name': self.zone.name,
                    'zone_id': self.zone.id,
                    'success': success,
                    'total': total,
                }
            )
            self.zone.status = 'ERROR'
            self._update_status()
            return False
        return True

    def __call__(self):
        results = self._execute()
        return self._threshold_met(results)


class ZoneAction(base.Task):
    """
    Orchestrate a complete Create/Update/Delete of the specified zone on the
    pool and the polling for the change

    :return: Success/Failure of the change propagating to a satisfactory
             number of nameservers (bool)
    """

    def __init__(self, executor, context, pool, zone, action,
                 zone_params=None):
        super().__init__(executor)
        self.context = context
        self.pool = pool
        self.zone = zone
        self.action = action
        self.task_name = 'ZoneAction-%s' % self.action.title()
        self.zone_params = zone_params

    def _wait_for_nameservers(self):
        """
        Pause to give the nameservers a chance to update
        """
        time.sleep(self.delay)

    def _zone_action_on_targets(self):
        actor = ZoneActor(
            self.executor, self.context, self.pool, self.zone, self.zone_params
        )
        return actor()

    def _poll_for_zone(self):
        poller = ZonePoller(self.executor, self.context, self.pool, self.zone)
        return poller()

    def __call__(self):
        LOG.info(
            'Attempting to %(action)s zone_name=%(zone_name)s '
            'zone_id=%(zone_id)s',
            {
                'action': self.action,
                'zone_name': self.zone.name,
                'zone_id': self.zone.id,
            }
        )

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
    LOG.debug(
        'Results for polling zone_name=%(zone_name)s zone_id=%(zone_id)s '
        'action=%(action)s serial=%(serial)d query=%(query)s',
        {
            'zone_name': zone.name,
            'zone_id': zone.id,
            'action': zone.action,
            'serial': zone.serial,
            'query': result,
        }
    )
    return result


class PollForZone(base.Task):
    """
    Send SOA queries to a nameserver for the zone. This could be a serial
    number, or that the zone does not exist.

    :return: A serial number if the zone exists (int), None if the zone
    does not exist
    """

    def __init__(self, executor, zone, ns):
        super().__init__(executor)
        self.zone = zone
        self.ns = ns

    def _get_serial(self):
        return dnsutils.get_serial(
            self.zone.name,
            self.ns.host,
            port=self.ns.port
        )

    def __call__(self):
        LOG.debug(
            'Polling serial=%(serial)d for zone_name=%(zone_name)s '
            'zone_id=%(zone_id)s action=%(action)s on ns=%(ns)s',
            {
                'serial': self.zone.serial,
                'zone_name': self.zone.name,
                'zone_id': self.zone.id,
                'action': self.zone.action,
                'ns': self.ns,
            }
        )

        try:
            serial = self._get_serial()

            LOG.debug(
                'Found serial=%(serial)d for zone_name=%(zone_name)s '
                'zone_id=%(zone_id)s action=%(action)s on ns=%(ns)s',
                {
                    'serial': serial,
                    'zone_name': self.zone.name,
                    'zone_id': self.zone.id,
                    'action': self.zone.action,
                    'ns': self.ns,
                }
            )
            return serial
            # TODO(timsim): cache if it's higher than cache
        except dns.exception.Timeout:
            LOG.info(
                'Timeout polling serial=%(serial)d for '
                'zone_name=%(zone_name)s zone_id=%(zone_id)s '
                'action=%(action)s on ns=%(ns)s',
                {
                    'serial': self.zone.serial,
                    'zone_name': self.zone.name,
                    'zone_id': self.zone.id,
                    'action': self.zone.action,
                    'ns': self.ns,
                }
            )

        except Exception as e:
            LOG.warning(
                'Unexpected failure polling serial=%(serial)d for '
                'zone_name=%(zone_name)s zone_id=%(zone_id)s '
                'action=%(action)s on ns=%(ns)s Error=%(error)s',
                {
                    'serial': self.zone.serial,
                    'zone_name': self.zone.name,
                    'zone_id': self.zone.id,
                    'action': self.zone.action,
                    'ns': self.ns,
                    'error': str(e),
                }
            )

        return None


class ZonePoller(base.Task):
    """
    Orchestrate polling for a change across the nameservers in a pool
    and compute the proper zone status, and update it.

    :return: Whether the change was successfully polled for on a satisfactory
             number of nameservers in the pool
    """

    def __init__(self, executor, context, pool, zone):
        super().__init__(executor)
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
        for retry in range(0, self.max_retries):
            results = self.executor.run([
                PollForZone(self.executor, self.zone, ns)
                for ns in nameservers
            ])

            query_result = parse_query_results(results, self.zone)

            if self.compare_threshold(query_result.positives, len(results)):
                LOG.debug(
                    'Successful poll for zone_name=%(zone_name)s '
                    'zone_id=%(zone_id)s action=%(action)s',
                    {
                        'zone_name': self.zone.name,
                        'zone_id': self.zone.id,
                        'action': self.zone.action,
                    }
                )
                break
            LOG.debug(
                'Unsuccessful poll for zone_name=%(zone_name)s '
                'zone_id=%(zone_id)s action=%(action)s on attempt=%(attempt)d',
                {
                    'zone_name': self.zone.name,
                    'zone_id': self.zone.id,
                    'action': self.zone.action,
                    'attempt': retry + 1,
                }
            )

            time.sleep(retry_interval)

            if not self.is_current_action_valid(self.context, self.zone.action,
                                                self.zone):
                break

        return query_result

    def _on_failure(self, error_status):
        LOG.info(
            'Could not find serial=%(serial)d for zone_name=%(zone_name)s '
            'zone_id=%(zone_id)s action=%(action)s on enough nameservers',
            {
                'serial': self.zone.serial,
                'zone_name': self.zone.name,
                'zone_id': self.zone.id,
                'action': self.zone.action,
            }
        )

        self.zone.status = error_status

        if error_status == 'NO_ZONE':
            self.zone.action = 'CREATE'

        return False

    def _on_success(self, query_result, status):
        # TODO(timsim): Change this back to active, so dumb central
        self.zone.status = status
        LOG.debug(
            'Found success for zone_name=%(zone_name)s '
            'zone_id=%(zone_id)s action=%(action)s at serial=%(serial)d',
            {
                'zone_name': self.zone.name,
                'zone_id': self.zone.id,
                'action': self.zone.action,
                'serial': self.zone.serial,
            }
        )

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
        over_no_zone_threshold = self.compare_threshold(
            (total - query_result.no_zones), total
        )

        if not over_no_zone_threshold and is_not_delete:
            return False, 'NO_ZONE'

        # The action should have been pushed out to a minimum
        # number of nameservers.
        if not self.compare_threshold(query_result.positives, total):
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


class GetZoneSerial(base.Task):
    """
    Get zone serial number from a resolver using retries.
    """
    def __init__(self, executor, context, zone, host, port):
        super().__init__(executor)
        self.context = context
        self.zone = zone
        self.host = host
        self.port = port
        self.serial_max_retries = CONF['service:worker'].serial_max_retries
        self.serial_retry_delay = CONF['service:worker'].serial_retry_delay
        self.serial_timeout = CONF['service:worker'].serial_timeout

    def __call__(self):
        LOG.debug(
            'Sending SOA for zone_name=%(zone)s to %(server)s:%(port)d.',
            {
                'zone': self.zone.name,
                'server': self.host,
                'port': self.port,
            }
        )
        actual_serial = None
        status = 'ERROR'
        for retry in range(0, self.serial_max_retries):
            response = self._make_and_send_soa_message(
                self.zone.name, self.host, self.port
            )
            if not response:
                pass
            elif (response.rcode() in (
                    dns.rcode.NXDOMAIN,
                    dns.rcode.REFUSED,
                    dns.rcode.SERVFAIL) or not bool(response.answer)):
                status = 'NO_ZONE'
                if (self.zone.serial == 0 and
                        self.zone.action in ('DELETE', 'NONE')):
                    actual_serial = 0
                    break
            elif not (response.flags & dns.flags.AA):
                LOG.warning(
                    'Unable to get serial for zone_name=%(zone)s '
                    'to %(server)s:%(port)d. '
                    'Unable to get an Authoritative Answer from server.',
                    {
                        'zone': self.zone.name,
                        'server': self.host,
                        'port': self.port,
                    }
                )
                break
            elif dns.rcode.from_flags(
                    response.flags, response.ednsflags) != dns.rcode.NOERROR:
                pass
            elif (len(response.answer) == 1 and
                  str(response.answer[0].name) == self.zone.name and
                  response.answer[0].rdclass == dns.rdataclass.IN and
                  response.answer[0].rdtype == dns.rdatatype.SOA):
                rrset = response.answer[0]
                actual_serial = list(rrset.to_rdataset().items)[0].serial

            if actual_serial is not None:
                status = 'SUCCESS'
                break
            time.sleep(self.serial_retry_delay)

        if actual_serial is None:
            LOG.warning(
                'Unable to get serial for zone_name=%(zone)s'
                'to %(server)s:%(port)d.',
                {
                    'zone': self.zone.name,
                    'server': self.host,
                    'port': self.port,
                }
            )

        return status, actual_serial

    def _make_and_send_soa_message(self, zone_name, host, port):
        """
        Generate and send a SOA message.

        :param zone_name: The zone name.
        :param host: The destination host for the dns message.
        :param port: The destination port for the dns message.
        """
        try:
            return dnsutils.soa_query(
                zone_name, host, port, timeout=self.serial_timeout
            )
        except OSError as e:
            if e.errno != errno.EAGAIN:
                raise
            LOG.info(
                'Got EAGAIN while trying to send SOA for '
                'zone_name=%(zone_name)s to %(server)s:%(port)d. '
                'timeout=%(timeout)d seconds.',
                {
                    'zone_name': zone_name,
                    'server': host,
                    'port': port,
                    'timeout': self.serial_timeout
                }
            )
        except dns.exception.Timeout:
            LOG.warning(
                'Got Timeout while trying to send SOA for '
                'zone_name=%(zone_name)s to %(server)s:%(port)d. '
                'timeout=%(timeout)d seconds.',
                {
                    'zone_name': zone_name,
                    'server': host,
                    'port': port,
                    'timeout': self.serial_timeout
                }
            )
        except dns.query.BadResponse:
            LOG.warning(
                'Got BadResponse while trying to send SOA '
                'for zone_name=%(zone_name)s to %(server)s:%(port)d.',
                {
                    'zone_name': zone_name,
                    'server': host,
                    'port': port,
                }
            )


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
        super().__init__(executor)
        self.zone = zone
        self.context = context

    def __call__(self):
        LOG.debug(
            'Updating status for zone_name=%(zone_name)s '
            'zone_id=%(zone_id)s to action=%(action)s serial=%(serial)d',
            {
                'zone_name': self.zone.name,
                'zone_id': self.zone.id,
                'action': self.zone.action,
                'serial': self.zone.serial,
            }
        )

        self.central_api.update_status(
            self.context,
            self.zone.id,
            self.zone.status,
            self.zone.serial,
            self.zone.action,
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
        super().__init__(executor)
        self.context = context
        self.begin_shard = begin
        self.end_shard = end

    def _get_zones(self):
        criterion = {
            'shard': f'BETWEEN {self.begin_shard},{self.end_shard}',
            'status': 'ERROR'
        }
        error_zones = self.storage.find_zones(self.context, criterion)

        # Include things that have been hanging out in PENDING
        # status for longer than they should
        # Generate the current serial, will provide a UTC Unix TS.
        stale_criterion = {
            'shard': f'BETWEEN {self.begin_shard},{self.end_shard}',
            'status': 'PENDING',
            'serial': '<%s' % (timeutils.utcnow_ts() - self.max_prop_time)
        }

        stale_zones = self.storage.find_zones(self.context, stale_criterion)
        if stale_zones:
            LOG.warning('Found %(len)d zones PENDING for more than %(sec)d '
                        'seconds', {
                            'len': len(stale_zones),
                            'sec': self.max_prop_time
                        })
            error_zones.extend(stale_zones)

        return error_zones

    def __call__(self):
        zones = self._get_zones()
        for zone in zones:
            LOG.debug(
                'Trying to recover zone_name=%(zone_name)s '
                'zone_id=%(zone_id)s action=%(action)s status=%(status)s',
                {
                    'zone_name': zone.name,
                    'zone_id': zone.id,
                    'action': zone.action,
                    'status': zone.status,
                }
            )

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
        super().__init__(executor)
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
                    context, context.project_id, api_export_size=size)
            except exceptions.OverQuota:
                LOG.debug('Zone Export too large to perform synchronously')
                export.status = 'ERROR'
                export.message = 'Zone is too large to export'
                return export

            export.location = (
                    'designate://v2/zones/tasks/exports/%(eid)s/export' %
                    {'eid': export.id}
            )

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

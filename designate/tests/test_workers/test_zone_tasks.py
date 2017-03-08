# Copyright 2016 Rackspace Inc.
#
# Author: Eric Larson <eric.larson@rackspace.com>
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
# under the License.mport threading
from unittest import TestCase

import mock
import testtools
from oslo_config import cfg

import designate.tests.test_utils as utils
from designate import exceptions
from designate.worker.tasks import zone
from designate.worker import processing


class TestZoneAction(TestCase):

    def setUp(self):
        self.context = mock.Mock()
        self.pool = 'default_pool'
        self.executor = mock.Mock()
        self.task = zone.ZoneAction(
            self.executor, self.context, self.pool, mock.Mock(), 'CREATE'
        )
        self.task._wait_for_nameservers = mock.Mock()

    def test_constructor(self):
        assert self.task

    def test_call(self):
        self.task._zone_action_on_targets = mock.Mock(return_value=True)
        self.task._poll_for_zone = mock.Mock(return_value=True)
        result = self.task()
        assert result is True

        assert self.task._wait_for_nameservers.called
        assert self.task._zone_action_on_targets.called
        assert self.task._poll_for_zone.called

    def test_call_on_delete(self):
        myzone = mock.Mock()
        task = zone.ZoneAction(
            self.executor, self.context, self.pool, myzone, 'DELETE'
        )
        task._zone_action_on_targets = mock.Mock(return_value=True)
        task._poll_for_zone = mock.Mock(return_value=True)
        task._wait_for_nameservers = mock.Mock()

        assert task()

        assert myzone.serial == 0

    def test_call_fails_on_zone_targets(self):
        self.task._zone_action_on_targets = mock.Mock(return_value=False)
        assert not self.task()

    def test_call_fails_on_poll_for_zone(self):
        self.task._zone_action_on_targets = mock.Mock(return_value=False)
        assert not self.task()

    @mock.patch.object(zone, 'time')
    def test_wait_for_nameservers(self, time):
        # It is just a time.sleep :(
        task = zone.ZoneAction(
            self.executor, self.context, self.pool, mock.Mock(), 'CREATE'
        )
        task._wait_for_nameservers()
        time.sleep.assert_called_with(task.delay)


class TestZoneActor(TestCase):
    """The zone actor runs actions for zones in multiple threads and
    ensures the result meets the required thresholds for calling it
    done.
    """

    def setUp(self):
        self.context = mock.Mock()
        self.pool = mock.Mock()
        self.executor = mock.Mock()
        self.actor = zone.ZoneActor(
            self.executor,
            self.context,
            self.pool,
            mock.Mock(action='CREATE'),
        )

    def test_invalid_action(self):
        with testtools.ExpectedException(Exception, "Bad Action"):
            self.actor._validate_action('BAD')

    def test_threshold_from_config(self):
        actor = zone.ZoneActor(
            self.executor, self.context, self.pool, mock.Mock(action='CREATE')
        )

        default = cfg.CONF['service:worker'].threshold_percentage
        assert actor.threshold == default

    def test_execute(self):
        self.pool.targets = ['target 1']
        self.actor.executor.run.return_value = ['foo']

        results = self.actor._execute()

        assert results == ['foo']

    def test_call(self):
        self.actor.pool.targets = ['target 1']
        self.actor.executor.run.return_value = [True]
        assert self.actor() is True

    def test_threshold_met_true(self):
        self.actor._threshold = 80

        results = [True for i in range(8)] + [False, False]

        assert self.actor._threshold_met(results)

    def test_threshold_met_false(self):
        self.actor._threshold = 90
        self.actor._update_status = mock.Mock()

        results = [False] + [True for i in range(8)] + [False]

        assert not self.actor._threshold_met(results)
        assert self.actor._update_status.called
        assert self.actor.zone.status == 'ERROR'


QUERY_RESULTS = {
    'delete_success_all': {
        'case': {
            'action': 'DELETE',
            'results': [0, 0, 0, 0],
            'zone_serial': 1,
            'positives': 4,
            'no_zones': 4,
            'consensus_serial': 0
        }
    },
    'delete_success_half': {
        'case': {
            'action': 'DELETE',
            'results': [1, 0, 1, 0],
            'zone_serial': 1,
            'positives': 2,
            'no_zones': 2,
            'consensus_serial': 0
        },
    },
    'update_success_all': {
        'case': {
            'action': 'UPDATE',
            'results': [2, 2, 2, 2],
            'zone_serial': 2,
            'positives': 4,
            'no_zones': 0,
            'consensus_serial': 2
        },
    },
    'update_fail_all': {
        'case': {
            'action': 'UPDATE',
            'results': [1, 1, 1, 1],
            'zone_serial': 2,
            'positives': 0,
            'no_zones': 0,
            # The consensus serial is never updated b/c the nameserver
            # serials are less than the zone serial.
            'consensus_serial': 0
        },
    },
    'update_success_with_higher_serial': {
        'case': {
            'action': 'UPDATE',
            'results': [2, 1, 0, 3],
            'zone_serial': 2,
            'positives': 2,
            'no_zones': 1,
            'consensus_serial': 2
        },
    },
    'update_success_all_higher_serial': {
        'case': {
            'action': 'UPDATE',
            'results': [3, 3, 3, 3],
            'zone_serial': 2,
            'positives': 4,
            'no_zones': 0,
            'consensus_serial': 3,
        }
    },
}


@utils.parameterized_class
class TestParseQueryResults(TestCase):

    @utils.parameterized(QUERY_RESULTS)
    def test_result_cases(self, case):
        z = mock.Mock(action=case['action'])
        if case.get('zone_serial'):
            z.serial = case['zone_serial']

        result = zone.parse_query_results(
            case['results'], z
        )

        assert result.positives == case['positives']
        assert result.no_zones == case['no_zones']
        assert result.consensus_serial == case['consensus_serial']


class TestZonePoller(TestCase):

    def setUp(self):
        self.context = mock.Mock()
        self.pool = mock.Mock()
        self.zone = mock.Mock(name='example.com.', serial=1)
        self.threshold = 80
        self.executor = mock.Mock()
        self.poller = zone.ZonePoller(
            self.executor,
            self.context,
            self.pool,
            self.zone,
        )
        self.poller._threshold = self.threshold

    def test_constructor(self):
        assert self.poller
        assert self.poller.threshold == self.threshold

    def test_call_on_success(self):
        ns_results = [2 for i in range(8)] + [0, 0]
        result = zone.DNSQueryResult(
            positives=8,
            no_zones=2,
            consensus_serial=2,
            results=ns_results,
        )
        self.poller.zone.action = 'UPDATE'
        self.poller.zone.serial = 2
        self.poller._do_poll = mock.Mock(return_value=result)
        self.poller._on_success = mock.Mock(return_value=True)
        self.poller._update_status = mock.Mock()

        assert self.poller()

        self.poller._on_success.assert_called_with(result, 'SUCCESS')
        self.poller._update_status.called
        self.poller.zone.serial = 2
        self.poller.zone.status = 'SUCCESS'

    def test_threshold_met_true(self):
        ns_results = [2 for i in range(8)] + [0, 0]
        result = zone.DNSQueryResult(
            positives=8,
            no_zones=2,
            consensus_serial=2,
            results=ns_results,
        )

        success, status = self.poller._threshold_met(result)

        assert success
        assert status == 'SUCCESS'

    def test_threshold_met_false_low_positives(self):
        # 6 positives, 4 behind the serial (aka 0 no_zones)
        ns_results = [2 for i in range(6)] + [1 for i in range(4)]
        result = zone.DNSQueryResult(
            positives=6,
            no_zones=0,
            consensus_serial=2,
            results=ns_results,
        )

        success, status = self.poller._threshold_met(result)

        assert not success
        assert status == 'ERROR'

    def test_threshold_met_true_no_zones(self):
        # Change is looking for serial 2
        # 4 positives, 4 no zones, 2 behind the serial
        ns_results = [2 for i in range(4)] + [0 for i in range(4)] + [1, 1]
        result = zone.DNSQueryResult(
            positives=4,
            no_zones=4,
            consensus_serial=1,
            results=ns_results,
        )

        # Set the threshold to 30%
        self.poller._threshold = 30
        self.poller.zone.action = 'UPDATE'

        success, status = self.poller._threshold_met(result)

        assert success
        assert status == 'SUCCESS'

    def test_threshold_met_false_no_zones(self):
        # Change is looking for serial 2
        # 4 positives, 4 no zones
        ns_results = [2 for i in range(4)] + [0 for i in range(4)]
        result = zone.DNSQueryResult(
            positives=4,
            no_zones=4,
            consensus_serial=2,
            results=ns_results,
        )

        # Set the threshold to 100%
        self.poller._threshold = 100
        self.poller.zone.action = 'UPDATE'

        success, status = self.poller._threshold_met(result)

        assert not success
        assert status == 'NO_ZONE'

    def test_threshold_met_false_no_zones_one_result(self):
        # Change is looking for serial 2
        # 4 positives, 4 no zones
        ns_results = [0]
        result = zone.DNSQueryResult(
            positives=0,
            no_zones=1,
            consensus_serial=2,
            results=ns_results,
        )

        # Set the threshold to 100%
        self.poller._threshold = 100
        self.poller.zone.action = 'UPDATE'

        success, status = self.poller._threshold_met(result)

        assert not success
        assert status == 'NO_ZONE'

    def test_on_success(self):
        query_result = mock.Mock(consensus_serial=10)

        result = self.poller._on_success(query_result, 'FOO')

        assert result is True
        assert self.zone.serial == 10
        assert self.zone.status == 'FOO'

    def test_on_error_failure(self):
        result = self.poller._on_failure('FOO')

        assert result is False
        assert self.zone.status == 'FOO'

    def test_on_no_zones_failure(self):
        result = self.poller._on_failure('NO_ZONE')

        assert result is False
        assert self.zone.status == 'NO_ZONE'
        assert self.zone.action == 'CREATE'


class TestZonePollerPolling(TestCase):

    def setUp(self):
        self.executor = processing.Executor()
        self.context = mock.Mock()
        self.zone = mock.Mock(name='example.com.', action='UPDATE', serial=10)
        self.pool = mock.Mock(nameservers=['ns1', 'ns2'])
        self.threshold = 80

        self.poller = zone.ZonePoller(
            self.executor,
            self.context,
            self.pool,
            self.zone,
        )

        self.max_retries = 4
        self.retry_interval = 2
        self.poller._max_retries = self.max_retries
        self.poller._retry_interval = self.retry_interval

    @mock.patch.object(zone, 'PollForZone')
    def test_do_poll(self, PollForZone):
        PollForZone.return_value = mock.Mock(return_value=10)
        result = self.poller._do_poll()

        assert result

        assert result.positives == 2
        assert result.no_zones == 0
        assert result.results == [10, 10]

    @mock.patch.object(zone, 'time', mock.Mock())
    def test_do_poll_with_retry(self):
        exe = mock.Mock()
        exe.run.side_effect = [
            [0, 0], [10, 10]
        ]
        self.poller.executor = exe

        result = self.poller._do_poll()

        assert result

        zone.time.sleep.assert_called_with(self.retry_interval)

        # retried once
        assert len(zone.time.sleep.mock_calls) == 1

    @mock.patch.object(zone, 'time', mock.Mock())
    def test_do_poll_with_retry_until_fail(self):
        exe = mock.Mock()
        exe.run.return_value = [0, 0]

        self.poller.executor = exe

        self.poller._do_poll()

        assert len(zone.time.sleep.mock_calls) == self.max_retries


class TestUpdateStatus(TestCase):

    def setUp(self):
        self.executor = processing.Executor()
        self.task = zone.UpdateStatus(self.executor, mock.Mock(), mock.Mock())
        self.task._central_api = mock.Mock()

    def test_call_on_delete(self):
        self.task.zone.action = 'DELETE'

        self.task()

        assert self.task.zone.action == 'NONE'
        assert self.task.zone.status == 'NO_ZONE'
        assert self.task.central_api.update_status.called

    def test_call_on_success(self):
        self.task.zone.status = 'SUCCESS'

        self.task()

        assert self.task.zone.action == 'NONE'
        assert self.task.central_api.update_status.called

    def test_call_central_call(self):
        self.task.zone.status = 'SUCCESS'

        self.task()

        self.task.central_api.update_status.assert_called_with(
            self.task.context,
            self.task.zone.id,
            self.task.zone.status,
            self.task.zone.serial,
        )

    def test_call_on_delete_error(self):
        self.task.zone.action = 'DELETE'
        self.task.zone.status = 'ERROR'

        self.task()

        assert self.task.zone.action == 'DELETE'
        assert self.task.zone.status == 'ERROR'
        assert self.task.central_api.update_status.called

    def test_call_on_create_error(self):
        self.task.zone.action = 'CREATE'
        self.task.zone.status = 'ERROR'

        self.task()

        assert self.task.zone.action == 'CREATE'
        assert self.task.zone.status == 'ERROR'
        assert self.task.central_api.update_status.called

    def test_call_on_update_error(self):
        self.task.zone.action = 'UPDATE'
        self.task.zone.status = 'ERROR'

        self.task()

        assert self.task.zone.action == 'UPDATE'
        assert self.task.zone.status == 'ERROR'
        assert self.task.central_api.update_status.called


class TestPollForZone(TestCase):

    def setUp(self):
        self.zone = mock.Mock(serial=1)
        self.zone.name = 'example.org.'
        self.executor = processing.Executor()

        self.ns = mock.Mock(host='ns.example.org', port=53)
        self.task = zone.PollForZone(self.executor, self.zone, self.ns)
        self.task._max_retries = 3
        self.task._retry_interval = 2

    @mock.patch.object(zone.wutils, 'get_serial', mock.Mock(return_value=10))
    def test_get_serial(self):
        assert self.task._get_serial() == 10

        zone.wutils.get_serial.assert_called_with(
            'example.org.',
            'ns.example.org',
            port=53
        )

    def test_call(self):
        self.task._get_serial = mock.Mock(return_value=10)

        result = self.task()

        assert result == 10


class TestExportZone(TestCase):

    def setUp(self):
        self.zone = mock.Mock(name='example.com.', serial=1)
        self.export = mock.Mock()
        self.export.id = '1'
        self.executor = processing.Executor()
        self.context = mock.Mock()

        self.task = zone.ExportZone(
            self.executor, self.context, self.zone, self.export)
        self.task._central_api = mock.Mock()
        self.task._storage = mock.Mock()
        self.task._quota = mock.Mock()

        self.task._quota.limit_check = mock.Mock()
        self.task._storage.count_recordsets = mock.Mock(return_value=1)
        self.task._synchronous_export = mock.Mock(return_value=True)

    def test_sync_export_right_size(self):
        self.task()
        assert self.export.status == 'COMPLETE'
        s = "designate://v2/zones/tasks/exports/%s/export" % self.export.id
        assert self.export.location == s

    def test_sync_export_wrong_size_fails(self):
        self.task._quota.limit_check = mock.Mock(
            side_effect=exceptions.OverQuota)

        self.task()
        assert self.export.status == 'ERROR'

    def test_async_export_fails(self):
        self.task._synchronous_export = mock.Mock(return_value=False)

        self.task()
        assert self.export.status == 'ERROR'

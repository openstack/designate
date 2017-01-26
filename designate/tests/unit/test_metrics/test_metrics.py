#
# Copyright (C) 2016 Red Hat, Inc.
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
#

import mock
import monascastatsd

from designate.metrics import Metrics
from designate.metrics_client import noop
from designate.tests import TestCase

from oslo_config import cfg
from oslo_config import fixture as cfg_fixture


class TestNoopMetrics(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf
        self.metrics = Metrics()
        self.metrics._client = noop.Client()

    def test_noop_metrics_enabled(self):
        self.CONF.set_override('enabled', True, 'monasca:statsd')
        with mock.patch('designate.metrics_client.noop.LOG') as log_mock:
            self.metrics.init()
            log_mock.error.assert_called_once_with(
                "Using noop metrics client. Metrics will be ignored.")

    def test_noop_metrics_disabled(self):
        with mock.patch('designate.metrics_client.noop.LOG') as log_mock:
            self.metrics.init()
            log_mock.error.assert_not_called()

    def test_noop_metrics_client_getters(self):
        self.CONF.set_override('enabled', True, 'monasca:statsd')
        self.metrics.init()
        self.assertIsInstance(self.metrics.counter('name'), noop.NoopCounter)
        self.assertIsInstance(self.metrics.gauge(), noop.NoopGauge)
        self.assertIsInstance(self.metrics.timer(), noop.NoopTimer)
        self.assertIsNotNone(self.metrics.timed.__self__)

    def test_noop_metrics_client_timed(self):
        timer = self.metrics._client.get_timer()

        @timer.timed('timed.test')
        def func(a):
            return a
        result = func(1)
        self.assertEqual(result, 1)


class TestMonascaMetrics(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf
        self.metrics = Metrics()

    def test_monasca_metrics_enabled(self):
        self.CONF.set_override('enabled', True, 'monasca:statsd')
        with mock.patch('designate.metrics.LOG') as log_mock:
            self.metrics.init()
            log_mock.info.assert_called_once_with(
                "Statsd reports to 127.0.0.1 8125")

    def test_monasca_metrics_disabled(self):
        with mock.patch('designate.metrics.LOG') as log_mock:
            self.metrics.init()
            log_mock.info.assert_called_once_with(
                "Statsd disabled")

    @mock.patch('socket.socket.connect')
    @mock.patch('socket.socket.send')
    def test_monasca_metrics_client_getters(self, conn_mock, send_mock):
        self.CONF.set_override('enabled', True, 'monasca:statsd')
        self.metrics.init()
        self.assertIsInstance(self.metrics.counter('name'),
                              monascastatsd.counter.Counter)
        self.assertIsInstance(self.metrics.gauge(),
                              monascastatsd.gauge.Gauge)
        self.assertIsInstance(self.metrics.timer(),
                              monascastatsd.timer.Timer)
        self.assertIsNotNone(self.metrics.timed.__self__)

    def test_monasca_metrics_client_timed(self):
        timer = self.metrics._client.get_timer()

        @timer.timed('timed.test')
        def func(a):
            return a
        result = func(1)
        self.assertEqual(result, 1)

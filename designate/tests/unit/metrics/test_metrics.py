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
import time
from unittest import mock

import monascastatsd
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture

from designate import metrics
from designate.metrics_client import noop
from designate.tests import fixtures
from designate.tests import TestCase


class TestNoopMetrics(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.stdlog = fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf
        self.CONF.set_override('enabled', False, 'monasca:statsd')

    def test_monasca_metrics_disabled(self):
        self.metrics = metrics.Metrics()
        self.assertIsInstance(self.metrics.client, noop.Client)
        self.assertIn('Statsd disabled', self.stdlog.logger.output)

    def test_noop_metrics_client_getters(self):
        self.metrics = metrics.Metrics()
        self.assertIsInstance(self.metrics.counter('name'), noop.NoopCounter)
        self.assertIsInstance(self.metrics.gauge(), noop.NoopGauge)
        self.assertIsInstance(self.metrics.timer(), noop.NoopTimer)
        self.assertIsNotNone(self.metrics.timer.__self__)

    def test_noop_metrics_client_timed(self):
        self.metrics = metrics.Metrics()
        timer = self.metrics.client.get_timer()

        def func(a):
            start_time = time.time()
            try:
                return a
            finally:
                timer.timing('mdns.xfr.zone_sync', time.time() - start_time)

        result = func(1)
        self.assertEqual(result, 1)


class TestMonascaMetrics(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.stdlog = fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf
        self.CONF.set_override('enabled', True, 'monasca:statsd')

    @mock.patch('socket.socket.connect')
    def test_monasca_metrics_enabled(self, conn_mock):
        self.metrics = metrics.Metrics()

        self.assertIsInstance(self.metrics.client, monascastatsd.client.Client)
        self.assertIn('Statsd reports to 127.0.0.1:8125',
                      self.stdlog.logger.output)
        self.assertTrue(conn_mock.called)

    @mock.patch('socket.socket.connect')
    def test_monasca_metrics_client_getters(self, conn_mock):
        self.metrics = metrics.Metrics()

        self.assertIsInstance(self.metrics.counter('name'),
                              monascastatsd.counter.Counter)
        self.assertIsInstance(self.metrics.gauge(),
                              monascastatsd.gauge.Gauge)
        self.assertIsInstance(self.metrics.timer(),
                              monascastatsd.timer.Timer)
        self.assertIsNotNone(self.metrics.timer.__self__)

        self.assertTrue(conn_mock.called)

    @mock.patch('socket.socket.send')
    @mock.patch('socket.socket.connect')
    def test_monasca_metrics_client_timed(self, conn_mock, send_mock):
        self.metrics = metrics.Metrics()
        timer = self.metrics.client.get_timer()

        def func(a):
            start_time = time.time()
            try:
                return a
            finally:
                timer.timing('mdns.xfr.zone_sync', time.time() - start_time)

        result = func(1)
        self.assertEqual(result, 1)
        self.assertTrue(conn_mock.called)
        self.assertTrue(send_mock.called)

    def test_monasca_enabled_but_client_not_installed(self):
        restore = metrics.monascastatsd
        try:
            metrics.monascastatsd = None
            self.metrics = metrics.Metrics()
            self.assertIsInstance(self.metrics.client, noop.Client)
            self.assertIn(
                'monasca-statsd client not installed. '
                'Metrics will be ignored.',
                self.stdlog.logger.output
            )
        finally:
            metrics.monascastatsd = restore

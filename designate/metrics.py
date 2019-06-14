# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

import designate.conf
from designate.metrics_client import noop

monascastatsd = importutils.try_import('monascastatsd')

CFG_GROUP_NAME = 'monasca:statsd'
CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)

# Global metrics client to be imported by other modules
metrics = None


class Metrics(object):
    def __init__(self):
        self._client = None

    def init(self):
        conf = cfg.CONF[CFG_GROUP_NAME]
        if conf.enabled and monascastatsd:
            LOG.info(
                'Statsd reports to %(host)s:%(port)d',
                {
                    'host': conf.hostname,
                    'port': conf.port
                }
            )
            self._client = monascastatsd.Client(
                host=conf.hostname, port=conf.port,
                dimensions={
                    'service_name': 'dns'
                })
            return

        if conf.enabled and not monascastatsd:
            LOG.error('monasca-statsd client not installed. '
                      'Metrics will be ignored.')
        else:
            LOG.info('Statsd disabled')

        self._client = noop.Client()

    def counter(self, *a, **kw):
        return self.client.get_counter(*a, **kw)

    def gauge(self, *a, **kw):
        return self.client.get_gauge(*a, **kw)

    @property
    def timing(self):
        return self.client.get_timer().timing

    def timer(self):
        return self.client.get_timer()

    @property
    def client(self):
        if not self._client:
            self.init()
        return self._client


metrics = Metrics()

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

"""
Monasca-Statsd based metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Based on metrics-and-stats blueprint

Usage examples:

.. code-block:: python

    from designate.metrics import metrics

    @metrics.timed('dot.separated.name')
    def your_function():
        pass

    with metrics.time('dot.separated.name'):
        pass

    # Increment and decrement a counter.
    metrics.counter(name='foo.bar').increment()
    metrics.counter(name='foo.bar') -= 10

"""

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

from designate.i18n import _LI

stats_client = importutils.import_any('monascastatsd',
                                      'designate.metrics_client.noop')

LOG = logging.getLogger(__name__)

CFG_GROUP = 'monasca:statsd'
metrics_group = cfg.OptGroup(
    name=CFG_GROUP, title="Configuration for Monasca Statsd"
)

metrics_opts = [
    cfg.BoolOpt('enabled', default=False, help='enable'),
    cfg.IntOpt('port', default=8125, help='UDP port'),
    cfg.StrOpt('hostname', default='127.0.0.1', help='hostname')
]

cfg.CONF.register_group(metrics_group)
cfg.CONF.register_opts(metrics_opts, group=metrics_group)


# Global metrics client to be imported by other modules
metrics = None


class Metrics(object):

    def __init__(self):
        """Initialize Monasca-Statsd client with its default configuration.
        Do not start sending metrics yet.
        """
        self._client = stats_client.Client(dimensions={
            'service_name': 'dns'
        })
        # cfg.CONF is not available at this time
        # Buffer all metrics until init() is called
        # https://bugs.launchpad.net/monasca/+bug/1616060
        self._client.connection.open_buffer()
        self._client.connection.max_buffer_size = 50000

    def init(self):
        """Setup client connection or disable metrics based on configuration.
        This is called once the cfg.CONF is ready.
        """
        conf = cfg.CONF[CFG_GROUP]
        if conf.enabled:
            LOG.info(_LI("Statsd reports to %(host)s %(port)d") % {
                'host': conf.hostname,
                'port': conf.port
            })
            self._client.connection._flush_buffer()
            self._client.connection.close_buffer()
            self._client.connection.connect(conf.hostname, conf.port)
        else:
            LOG.info(_LI("Statsd disabled"))
            # The client cannot be disabled: mock out report()
            self._client.connection.report = lambda *a, **kw: None
            # There's no clean way to drain the outgoing buffer

    def counter(self, *a, **kw):
        return self._client.get_counter(*a, **kw)

    def gauge(self, *a, **kw):
        return self._client.get_gauge(*a, **kw)

    @property
    def timed(self):
        return self._client.get_timer().timed

    def timer(self):
        return self._client.get_timer()


metrics = Metrics()

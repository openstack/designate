# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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
import sys

from oslo_config import cfg
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr
import debtcollector

from designate import service
from designate import utils
from designate import version
from designate import hookpoints
from designate.pool_manager import service as pool_manager_service

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
CONF.import_opt('workers', 'designate.pool_manager',
                group='service:pool_manager')
CONF.import_opt('threads', 'designate.pool_manager',
                group='service:pool_manager')


def main():
    utils.read_config('designate', sys.argv)

    logging.setup(CONF, 'designate')
    gmr.TextGuruMeditation.setup_autorun(version)

    # NOTE(timsim): This is to ensure people don't start the wrong
    #               services when the worker model is enabled.
    if cfg.CONF['service:worker'].enabled:
        LOG.error('You have designate-worker enabled, starting '
                  'designate-pool-manager is incompatible with '
                  'designate-worker. You need to start '
                  'designate-worker instead.')
        sys.exit(1)

    debtcollector.deprecate('designate-pool-manager is deprecated in favor of '
                            'designate-worker', version='newton',
                            removal_version='rocky')

    server = pool_manager_service.Service(
        threads=CONF['service:pool_manager'].threads
    )

    hookpoints.log_hook_setup()

    service.serve(server, workers=CONF['service:pool_manager'].workers)
    service.wait()

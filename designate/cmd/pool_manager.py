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

from designate import service
from designate import utils
from designate import version
from designate import hookpoints
from designate.pool_manager import service as pool_manager_service


CONF = cfg.CONF
CONF.import_opt('workers', 'designate.pool_manager',
                group='service:pool_manager')
CONF.import_opt('threads', 'designate.pool_manager',
                group='service:pool_manager')


def main():
    utils.read_config('designate', sys.argv)

    logging.setup(CONF, 'designate')
    gmr.TextGuruMeditation.setup_autorun(version)

    server = pool_manager_service.Service(
        threads=CONF['service:pool_manager'].threads
    )

    hookpoints.log_hook_setup()

    service.serve(server, workers=CONF['service:pool_manager'].workers)
    service.wait()

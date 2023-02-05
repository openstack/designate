# Copyright 2014 Rackspace Inc.
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
import sys
import warnings

from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr

from designate.agent import service as agent_service
import designate.conf
from designate import heartbeat_emitter
from designate import service
from designate import utils
from designate import version


CONF = designate.conf.CONF
CONF.import_opt('workers', 'designate.agent', group='service:agent')


def main():
    utils.read_config('designate', sys.argv)
    logging.setup(CONF, 'designate')
    gmr.TextGuruMeditation.setup_autorun(version)

    warnings.warn('The designate agent process is deprecated as of the '
                  'Antelope (2023.1) release and will be removed in the '
                  '"C" release.', DeprecationWarning)

    server = agent_service.Service()
    heartbeat = heartbeat_emitter.get_heartbeat_emitter(server.service_name)
    service.serve(server, workers=CONF['service:agent'].workers)
    heartbeat.start()
    service.wait()

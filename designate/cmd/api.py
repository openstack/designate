# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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

from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr
from oslo_reports import opts as gmr_opts

from designate.api import service as api_service
import designate.conf
from designate import heartbeat_emitter
from designate import service
from designate import utils
from designate import version


CONF = designate.conf.CONF
CONF.import_group('keystone_authtoken', 'keystonemiddleware.auth_token')


def main():
    utils.read_config('designate', sys.argv)
    logging.setup(CONF, 'designate')
    gmr_opts.set_defaults(CONF)
    gmr.TextGuruMeditation.setup_autorun(version, conf=CONF)

    server = api_service.Service()
    heartbeat = heartbeat_emitter.get_heartbeat_emitter(server.service_name)
    service.serve(server, workers=CONF['service:api'].workers)
    heartbeat.start()
    service.wait()

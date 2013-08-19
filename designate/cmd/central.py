# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate.openstack.common import service
from designate import utils
from designate.central import service as central_service

CONF = cfg.CONF
CONF.import_opt('workers', 'designate.central', group='service:central')


def main():
    utils.read_config('designate', sys.argv)
    logging.setup('designate')
    launcher = service.launch(central_service.Service(),
                              CONF['service:central'].workers)
    launcher.wait()

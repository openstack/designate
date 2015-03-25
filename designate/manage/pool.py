# Copyright 2015 Hewlett-Packard Development Company, L.P.
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
import pprint

from oslo.config import cfg
from oslo_log import log as logging

from designate.manage import base
from designate import objects

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class PoolCommands(base.Commands):
    def show_config(self):
        print('*' * 100)
        print('Pool Configuration:')
        print('*' * 100)
        pprint.pprint(objects.Pool.from_config(CONF).to_dict())

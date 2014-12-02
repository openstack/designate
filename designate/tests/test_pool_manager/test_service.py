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
from oslo.config import cfg

from designate.tests.test_pool_manager import PoolManagerTestCase


class PoolManagerServiceTest(PoolManagerTestCase):
    def setUp(self):
        super(PoolManagerServiceTest, self).setUp()

        section_name = 'backend:fake:*'
        server_opts = [
            cfg.StrOpt('masters', default='127.0.0.1:5354')
        ]
        cfg.CONF.register_group(cfg.OptGroup(name=section_name))
        cfg.CONF.register_opts(server_opts, group=section_name)

        section_name = 'backend:fake:f278782a-07dc-4502-9177-b5d85c5f7c7e'
        server_opts = [
            cfg.StrOpt('host', default='127.0.0.1'),
            cfg.IntOpt('port', default=53)
        ]
        cfg.CONF.register_group(cfg.OptGroup(name=section_name))
        cfg.CONF.register_opts(server_opts, group=section_name)

        self.service = self.start_service('pool_manager')

    def test_stop(self):
        # NOTE: Start is already done by the fixture in start_service()
        self.service.stop()

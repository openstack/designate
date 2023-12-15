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


from oslo_log import log as logging
import oslotest.base

from designate.common.decorators import rpc
import designate.conf
from designate.tests import base_fixtures


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


@rpc.rpc_logging(LOG, 'test')
class RPCLog:
    RPC_LOGGING_DISALLOW = ['ignore']

    @classmethod
    def test(cls):
        return None

    @classmethod
    def ignore(cls):
        return None


class TestRPCLogging(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

    def test_rpc_logging(self):
        RPCLog.test()

        self.assertIn(
            'Calling designate.test.test() over RPC', self.stdlog.logger.output
        )

    def test_rpc_disallow_logging(self):
        RPCLog.ignore()

        self.assertFalse(self.stdlog.logger.output)

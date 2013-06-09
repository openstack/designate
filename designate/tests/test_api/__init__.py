# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from designate.openstack.common import log as logging
from designate.openstack.common import jsonutils as json
from designate.tests import TestCase


LOG = logging.getLogger(__name__)


class ApiTestCase(TestCase):
    __test__ = False

    def get(self, path, **kw):
        expected_status_code = kw.pop('status_code', 200)

        resp = self.client.get(path=path)

        LOG.debug('Response Body: %r' % resp.data)

        self.assertEqual(resp.status_code, expected_status_code)

        try:
            resp.json = json.loads(resp.data)
        except ValueError:
            resp.json = None

        return resp

    def post(self, path, data, content_type="application/json", **kw):
        expected_status_code = kw.pop('status_code', 200)

        content = json.dumps(data)
        resp = self.client.post(path=path, content_type=content_type,
                                data=content)

        LOG.debug('Response Body: %r' % resp.data)

        self.assertEqual(resp.status_code, expected_status_code)

        try:
            resp.json = json.loads(resp.data)
        except ValueError:
            resp.json = None

        return resp

    def put(self, path, data, content_type="application/json", **kw):
        expected_status_code = kw.pop('status_code', 200)

        content = json.dumps(data)
        resp = self.client.put(path=path, content_type=content_type,
                               data=content)

        LOG.debug('Response Body: %r' % resp.data)

        self.assertEqual(resp.status_code, expected_status_code)

        try:
            resp.json = json.loads(resp.data)
        except ValueError:
            resp.json = None

        return resp

    def delete(self, path, **kw):
        expected_status_code = kw.pop('status_code', 200)

        resp = self.client.delete(path=path)

        LOG.debug('Response Body: %r' % resp.data)

        self.assertEqual(resp.status_code, expected_status_code)

        return resp

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
import webtest
from webtest.compat import dumps


class TestApp(webtest.TestApp):
    def patch(self, url, params='', headers=None, extra_environ=None,
              status=None, upload_files=None, expect_errors=False,
              content_type=None):
            return self._gen_request('PATCH', url, params=params,
                                     headers=headers,
                                     extra_environ=extra_environ,
                                     status=status,
                                     upload_files=upload_files,
                                     expect_errors=expect_errors,
                                     content_type=content_type)

    def patch_json(self, url, params='', headers=None, extra_environ=None,
                   status=None, expect_errors=False):
        content_type = 'application/json'
        if params:
            params = dumps(params)
        return self._gen_request('PATCH', url, params=params, headers=headers,
                                 extra_environ=extra_environ, status=status,
                                 upload_files=None,
                                 expect_errors=expect_errors,
                                 content_type=content_type)


webtest.TestApp = TestApp

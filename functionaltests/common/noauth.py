"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import copy
import re

from six.moves.urllib import parse
from tempest_lib.auth import AuthProvider


class NoAuthAuthProvider(AuthProvider):

    def __init__(self, creds, override_url):
        super(NoAuthAuthProvider, self).__init__(creds)
        self.override_url = override_url

    @classmethod
    def check_credentials(cls, credentials):
        return True

    def base_url(self, *args, **kwargs):
        return self.override_url

    def _decorate_request(self, filters, method, url, headers=None, body=None,
                          auth_data=None):
        base_url = self.base_url(filters=filters, auth_data=auth_data)
        # build the unauthenticated request
        _headers = copy.deepcopy(headers) if headers is not None else {}
        _headers['X-Auth-Project-ID'] = self.credentials.tenant_id
        if url is None or url == "":
            _url = base_url
        else:
            # Join base URL and url, and remove multiple contiguous slashes
            _url = "/".join([base_url, url])
            parts = [x for x in parse.urlparse(_url)]
            parts[2] = re.sub("/{2,}", "/", parts[2])
            _url = parse.urlunparse(parts)
        # no change to method or body
        return str(_url), _headers, body

    def _get_auth(self):
        return None

    def is_expired(self):
        return False

    def _fill_credentials(self):
        pass

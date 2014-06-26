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
from inspect import ismethod
from inspect import getargspec

import pecan.core

from designate import exceptions
from designate.openstack.common import jsonutils


JSON_TYPES = ('application/json', 'application/json-patch+json')


class Request(pecan.core.Request):
    @property
    def body_dict(self):
        """
        Returns the body content as a dictonary, deserializing per the
        Content-Type header.

        We add this method to ease future XML support, so the main code
        is not hardcoded to call pecans "request.json()" method.
        """
        if self.content_type in JSON_TYPES:
            try:
                return jsonutils.load(self.body_file)
            except ValueError as valueError:
                raise exceptions.InvalidJson(valueError.message)
        else:
            raise Exception('TODO: Unsupported Content Type')

__init__ = pecan.core.Pecan.__base__.__init__
if not ismethod(__init__) or 'request_cls' not in getargspec(__init__).args:
    # only attempt to monkey patch `pecan.Request` in older versions of pecan;
    # newer versions support specifying a custom request implementation in the
    # `pecan.core.Pecan` constructor via the `request_cls` argument
    pecan.core.Request = Request

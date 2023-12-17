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
from oslo_serialization import jsonutils
import pecan.core

from designate import exceptions

JSON_TYPES = ('application/json', 'application/json-patch+json')


class Request(pecan.core.Request):
    @property
    def body_dict(self):
        """
        Returns the body content as a dictionary, deserializing per the
        Content-Type header.

        We add this method to ease future XML support, so the main code
        is not hardcoded to call pecans "request.json" method.
        """
        if self.content_type not in JSON_TYPES:
            raise exceptions.UnsupportedContentType(
                'Content-type must be application/json'
            )

        try:
            json_dict = jsonutils.load(self.body_file)
            if json_dict is None:
                # NOTE(kiall): Somehow, json.load(fp) is returning None.
                raise exceptions.EmptyRequestBody('Request Body is empty')
            return json_dict
        except ValueError as e:
            if not self.body:
                raise exceptions.EmptyRequestBody('Request Body is empty')
            else:
                raise exceptions.InvalidJson(str(e))

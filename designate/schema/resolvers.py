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
import jsonschema
from oslo_log import log as logging

from designate import utils


LOG = logging.getLogger(__name__)


class LocalResolver(jsonschema.RefResolver):
    def __init__(self, base_uri, referrer):
        super(LocalResolver, self).__init__(base_uri, referrer, (), True)
        self.api_version = None

    @classmethod
    def from_schema(cls, api_version, schema, *args, **kwargs):
        resolver = cls(schema.get("id", ""), schema, *args, **kwargs)
        resolver.api_version = api_version

        return resolver

    def resolve_remote(self, uri):
        LOG.debug('Loading remote schema: %s' % uri)
        return utils.load_schema(self.api_version, uri)

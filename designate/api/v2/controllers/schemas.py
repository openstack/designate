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
import os
import pecan
from designate import exceptions
from designate import utils
from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class SchemasController(object):
    @pecan.expose(template='json:', content_type='application/schema+json')
    def _default(self, *remainder):
        if len(remainder) == 0:
            pecan.abort(404)

        try:
            schema_name = os.path.join(*remainder)
            schema_json = utils.load_schema('v2', schema_name)
        except exceptions.ResourceNotFound:
            pecan.abort(404)

        return schema_json

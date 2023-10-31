# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hpe.com>
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

from pecan import expose

from designate import exceptions


class ErrorsController:

    @expose(content_type='text/plain')
    @expose(content_type='text/dns')
    @expose(content_type='application/json')
    def not_found(self):
        raise exceptions.NotFound('resource not found')

    @expose(content_type='text/plain')
    @expose(content_type='text/dns')
    @expose(content_type='application/json')
    def method_not_allowed(self):
        raise exceptions.MethodNotAllowed()

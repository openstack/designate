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
from moniker.backend import base
from moniker.agent import api as agent_api


class RPCBackend(base.Backend):
    def create_domain(self, *args, **kw):
        return agent_api.create_domain(*args, **kw)

    def update_domain(self, *args, **kw):
        return agent_api.update_domain(*args, **kw)

    def delete_domain(self, *args, **kw):
        return agent_api.delete_domain(*args, **kw)

    def create_record(self, *args, **kw):
        return agent_api.create_record(*args, **kw)

    def update_record(self, *args, **kw):
        return agent_api.update_record(*args, **kw)

    def delete_record(self, *args, **kw):
        return agent_api.delete_record(*args, **kw)

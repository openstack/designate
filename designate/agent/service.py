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
from oslo.config import cfg

from designate.openstack.common import log as logging
from designate import backend
from designate import service
from designate.central import rpcapi as central_rpcapi


LOG = logging.getLogger(__name__)


class Service(service.Service):
    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)

        central_api = central_rpcapi.CentralAPI()

        endpoint = backend.get_backend(
            cfg.CONF['service:agent'].backend_driver,
            central_service=central_api)

        kwargs['endpoints'] = [endpoint]

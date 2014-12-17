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
from designate.backend.base import PoolBackend

LOG = logging.getLogger(__name__)


def get_backend(backend_driver, backend_options):
    LOG.debug("Loading backend driver: %s" % backend_driver)
    cls = PoolBackend.get_driver(backend_driver)

    return cls(backend_options)


def get_server_object(backend_driver, server_id):
    LOG.debug("Loading backend driver: %s" % backend_driver)
    cls = PoolBackend.get_driver(backend_driver)

    return cls.get_server_object(backend_driver, server_id)

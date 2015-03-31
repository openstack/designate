# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hp.com>
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
from oslo_log import log as logging

from designate.api.v2.controllers import rest
from designate.api.v2.controllers.zones.tasks.transfer_requests \
    import TransferRequestsController as TRC
from designate.api.v2.controllers.zones.tasks.transfer_accepts \
    import TransferAcceptsController as TRA
from designate.api.v2.controllers.zones.tasks import abandon
from designate.api.v2.controllers.zones.tasks.xfr import XfrController

LOG = logging.getLogger(__name__)


class TasksController(rest.RestController):

    transfer_accepts = TRA()
    transfer_requests = TRC()
    abandon = abandon.AbandonController()
    xfr = XfrController()

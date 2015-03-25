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
from oslo_log import log as logging

from designate.backend.base import Backend

LOG = logging.getLogger(__name__)


def get_backend(type_, target):
    # TODO(kiall): Type is attached to the target, use it.
    LOG.debug("Loading backend driver: %s" % type_)

    cls = Backend.get_driver(type_)

    return cls(target)

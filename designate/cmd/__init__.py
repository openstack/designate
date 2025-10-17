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

from oslo_service import backend
from oslo_service.backend import exceptions as backend_exceptions

# Only initialize backend if not already set
try:
    backend.init_backend(backend.BackendType.THREADING)
except backend_exceptions.BackendAlreadySelected:
    # Backend already initialized, this is fine
    pass

from oslo_log import log  # noqa
from oslo_concurrency import lockutils  # noqa
import oslo_messaging as messaging  # noqa

_EXTRA_DEFAULT_LOG_LEVELS = [
    'kazoo.client=WARN',
    'keystone=INFO',
    'oslo_service.loopingcall=WARN',
]

# Set some Oslo Log defaults
log.set_defaults(default_log_levels=log.get_default_log_levels() +
                 _EXTRA_DEFAULT_LOG_LEVELS)

# Set some Oslo RPC defaults
messaging.set_transport_defaults('designate')

# Set some Oslo Concurrency defaults
lockutils.set_defaults(lock_path='$state_path')

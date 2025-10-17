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

import os

# Disable eventlet's greendns monkey patching to prevent dnspython
# compatibility issues. Without this, dnspython's zone parsing fails with
# errors like "TypeError: add(): expected an Rdata" due to conflicts between
# eventlet's patched DNS resolver and dnspython's native implementation.
os.environ['EVENTLET_NO_GREENDNS'] = 'yes'

from oslo_service import backend as oslo_service_backend # noqa
try:
    oslo_service_backend.init_backend(
        oslo_service_backend.BackendType.THREADING)
except oslo_service_backend.exceptions.BackendAlreadySelected:
    # Backend already initialized, this is fine
    pass

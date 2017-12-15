# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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

from oslo_middleware import cors
from oslo_policy import opts as policy_opts

import designate.conf


def set_defaults():
    """Override all default values from upstream packages"""

    cors.set_defaults(
        allow_headers=['X-Auth-Token',
                       'X-Auth-Sudo-Tenant-ID',
                       'X-Auth-Sudo-Project-ID',
                       'X-Auth-All-Projects',
                       'X-Designate-Pool-ID',
                       'X-Designate-Edit-Managed-Records',
                       'X-Designate-Hard-Delete',
                       'OpenStack-DNS-Hide-Counts'],
        expose_headers=['X-OpenStack-Request-ID',
                        'Host'],
        allow_methods=['GET',
                       'PUT',
                       'POST',
                       'DELETE',
                       'PATCH',
                       'HEAD']
    )
    # TODO(gmann): Remove setting the default value of config policy_file
    # once oslo_policy change the default value to 'policy.yaml'.
    # https://github.com/openstack/oslo.policy/blob/a626ad12fe5a3abd49d70e3e5b95589d279ab578/oslo_policy/opts.py#L49
    DEFAULT_POLICY_FILE = 'policy.yaml'
    policy_opts.set_defaults(designate.conf.CONF, DEFAULT_POLICY_FILE)

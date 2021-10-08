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

import dns.zone


def create_dnspy_zone(name):
    if not name.endswith('.'):
        name = name + '.'
    zone_text = (
        '$ORIGIN %(name)s\n%(name)s 3600 IN SOA %(ns)s email.email.com. '
        '1421777854 3600 600 86400 3600\n%(name)s 3600 IN NS %(ns)s\n'
    )

    return dns.zone.from_text(
        zone_text % {'name': name, 'ns': 'ns1.designate.com'},
        check_origin=False
    )

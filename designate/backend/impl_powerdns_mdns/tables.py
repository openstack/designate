# Copyright 2012-2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from designate.backend.impl_powerdns import tables


# NOTE(kiall): We import the domains table object here in order to ensure
#              the PowerDNS mDNS based driver uses only this one table. When
#              the original PowerDNS driver is removed, we'll move the domains
#              table definition here.
domains = tables.domains

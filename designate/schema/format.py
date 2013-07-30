# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
import re
import jsonschema
import netaddr
from designate.openstack.common import log as logging

LOG = logging.getLogger(__name__)

RE_DOMAINNAME = r'^(?!.{255,})((?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-)\.)+$'
RE_HOSTNAME = r'^(?!.{255,})((^\*|(?!\-)[A-Za-z0-9_\-]{1,63})(?<!\-)\.)+$'


@jsonschema._checks_drafts(draft3='ip-address', draft4='ipv4')
def is_ipv4(instance):
    try:
        address = netaddr.IPAddress(instance, version=4)
        # netaddr happly accepts, and expands "127.0" into "127.0.0.0"
        if str(address) != instance:
            return False
    except netaddr.AddrFormatError:
        return False

    if instance == '0.0.0.0':  # RFC5735
        return False

    return True


@jsonschema._checks_drafts('ipv6')
def is_ipv6(instance):
    try:
        netaddr.IPAddress(instance, version=6)
    except netaddr.AddrFormatError:
        return False

    return True


@jsonschema._checks_drafts(draft3="host-name", draft4="hostname")
def is_hostname(instance):
    if not re.match(RE_HOSTNAME, instance):
        return False

    return True


@jsonschema._checks_drafts(draft3="domain-name", draft4="domainname")
def is_domainname(instance):
    if not re.match(RE_DOMAINNAME, instance):
        return False

    return True


@jsonschema._checks_drafts("email")
def is_email(instance):
    # A valid email address. We use the RFC1035 version of "valid".
    if instance.count('@') != 1:
        return False

    rname = instance.replace('@', '.', 1)

    if not re.match(RE_DOMAINNAME, "%s." % rname):
        return False

    return True


draft3_format_checker = jsonschema.FormatChecker(
    jsonschema._draft_checkers["draft3"])

draft4_format_checker = jsonschema.FormatChecker(
    jsonschema._draft_checkers["draft4"])

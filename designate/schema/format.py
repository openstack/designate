# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from jsonschema import compat
import netaddr


# NOTE(kiall): All of the below regular expressions are terminated with
#              "\Z", rather than simply "$" to ensure a string with a
#              trailing newline is NOT matched. See bug #1471158.

RE_ZONENAME = r'^(?!.{255,})(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-)\.)+\Z'
RE_HOSTNAME = r'^(?!.{255,})(?:(?:^\*|(?!\-)[A-Za-z0-9_\-]{1,63})(?<!\-)\.)+\Z'

RE_SRV_HOST_NAME = r'^(?:(?!\-)(?:\_[A-Za-z0-9_\-]{1,63}\.){2})(?!.{255,})' \
                   r'(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-)\.)+\Z'

# The TLD name will not end in a period.
RE_TLDNAME = r'^(?!.{255,})(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-))' \
             r'(?:\.(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-)))*\Z'

RE_UUID = r'^(?:[0-9a-fA-F]){8}-(?:[0-9a-fA-F]){4}-(?:[0-9a-fA-F]){4}-' \
          r'(?:[0-9a-fA-F]){4}-(?:[0-9a-fA-F]){12}\Z'

RE_IP_AND_PORT = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}' \
                 r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)' \
                 r'(?::(?:6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}' \
                 r'|[1-5]\d{4}|[1-9]\d{0,3}|0))?\Z'

RE_FIP_ID = r'^(?P<region>[A-Za-z0-9\.\-_]{1,100}):' \
            r'(?P<id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-' \
            r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\Z'

RE_SSHFP_FINGERPRINT = r'^([0-9A-Fa-f]{10,40}|[0-9A-Fa-f]{64})\Z'


draft3_format_checker = jsonschema.draft3_format_checker
draft4_format_checker = jsonschema.draft4_format_checker


@draft3_format_checker.checks("ip-address")
@draft4_format_checker.checks("ipv4")
def is_ipv4(instance):
    if not isinstance(instance, compat.str_types):
        return True

    try:
        address = netaddr.IPAddress(instance, version=4)
        # netaddr happly accepts, and expands "127.0" into "127.0.0.0"
        if str(address) != instance:
            return False
    except Exception:
        return False

    if instance == '0.0.0.0':  # RFC5735
        return False

    return True


@draft3_format_checker.checks("ipv6")
@draft4_format_checker.checks("ipv6")
def is_ipv6(instance):
    if not isinstance(instance, compat.str_types):
        return True

    try:
        netaddr.IPAddress(instance, version=6)
    except Exception:
        return False

    return True


@draft3_format_checker.checks("host-name")
@draft4_format_checker.checks("hostname")
def is_hostname(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_HOSTNAME, instance):
        return False

    return True


@draft4_format_checker.checks("ns-hostname")
def is_ns_hostname(instance):
    if not isinstance(instance, compat.str_types):
        return True

    # BIND doesn't like *.host.com. see bug #1533299
    if not re.match(RE_ZONENAME, instance):
        return False

    return True


@draft3_format_checker.checks("ip-or-host")
@draft4_format_checker.checks("ip-or-host")
def is_ip_or_host(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_ZONENAME, instance)\
            and not is_ipv4(instance)\
            and not is_ipv6(instance):
        return False

    return True


@draft3_format_checker.checks("domain-name")
@draft4_format_checker.checks("domainname")
@draft3_format_checker.checks("zone-name")
@draft4_format_checker.checks("zonename")
def is_zonename(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_ZONENAME, instance):
        return False

    return True


@draft4_format_checker.checks("srv-hostname")
def is_srv_hostname(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_SRV_HOST_NAME, instance):
        return False

    return True


@draft4_format_checker.checks("txt-data")
def is_txt_data(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if instance.endswith('\\'):
        return False

    return True


@draft3_format_checker.checks("tld-name")
@draft4_format_checker.checks("tldname")
def is_tldname(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_TLDNAME, instance):
        return False

    return True


@draft3_format_checker.checks("email")
@draft4_format_checker.checks("email")
def is_email(instance):
    if not isinstance(instance, compat.str_types):
        return True

    # A valid email address. We use the RFC1035 version of "valid".
    if instance.count('@') != 1:
        return False

    rname = instance.replace('@', '.', 1)

    if not re.match(RE_ZONENAME, "%s." % rname):
        return False

    return True


@draft4_format_checker.checks("sshfp")
def is_sshfp_fingerprint(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_SSHFP_FINGERPRINT, instance):
        return False

    return True


@draft3_format_checker.checks("uuid")
@draft4_format_checker.checks("uuid")
def is_uuid(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_UUID, instance):
        return False

    return True


@draft3_format_checker.checks("floating-ip-id")
@draft4_format_checker.checks("floating-ip-id")
def is_floating_ip_id(instance):
    # TODO(kiall): Apparently, this is used in exactly zero places outside the
    #              tests. Determine if we should remove this code...
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_FIP_ID, instance):
        return False

    return True


@draft3_format_checker.checks("ip-and-port")
@draft4_format_checker.checks("ipandport")
def is_ip_and_port(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_IP_AND_PORT, instance):
        return False

    return True

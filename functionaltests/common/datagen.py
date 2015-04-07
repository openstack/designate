"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import random

from functionaltests.api.v2.models.zone_model import ZoneModel
from functionaltests.api.v2.models.recordset_model import RecordsetModel


def random_ip():
    return ".".join(str(random.randrange(0, 256)) for _ in range(4))


def random_ipv6():
    def hexes(n):
        return "".join(random.choice("1234567890abcdef") for _ in range(n))
    result = ":".join(hexes(4) for _ in range(8))
    return result.replace("0000", "0")


def random_string(prefix='rand', n=8, suffix=''):
    """Return a string containing random digits

    :param prefix: the exact text to start the string. Defaults to "rand"
    :param n: the number of random digits to generate
    :param suffix: the exact text to end the string
    """
    digits = "".join(str(random.randrange(0, 10)) for _ in range(n))
    return prefix + digits + suffix


def random_zone_data(name=None, email=None, ttl=None, description=None):
    """Generate random zone data, with optional overrides

    :return: A ZoneModel
    """
    if name is None:
        name = random_string(prefix='testdomain', suffix='.com.')
    if email is None:
        email = ("admin@" + name).strip('.')
    if description is None:
        description = random_string(prefix='Description ')
    if ttl is None:
        ttl = random.randint(1200, 8400),
    return ZoneModel.from_dict({
        'name': name,
        'email': email,
        'ttl': random.randint(1200, 8400),
        'description': description})


def random_recordset_data(record_type, zone_name, name=None, records=None,
                          ttl=None):
    """Generate random recordset data, with optional overrides

    :return: A RecordsetModel
    """
    if name is None:
        name = random_string(prefix=record_type, suffix='.' + zone_name)
    if records is None:
        records = [random_ip()]
    if ttl is None:
        ttl = random.randint(1200, 8400)
    return RecordsetModel.from_dict({
        'type': record_type,
        'name': name,
        'records': records,
        'ttl': ttl})


def random_a_recordset(zone_name, ip=None, **kwargs):
    if ip is None:
        ip = random_ip()
    return random_recordset_data('A', zone_name, records=[ip], **kwargs)


def random_aaaa_recordset(zone_name, ip=None, **kwargs):
    if ip is None:
        ip = random_ipv6()
    return random_recordset_data('AAAA', zone_name, records=[ip], **kwargs)


def random_cname_recordset(zone_name, cname=None, **kwargs):
    if cname is None:
        cname = zone_name
    return random_recordset_data('CNAME', zone_name, records=[cname], **kwargs)


def random_mx_recordset(zone_name, pref=None, host=None, **kwargs):
    if pref is None:
        pref = str(random.randint(0, 65535))
    if host is None:
        host = random_string(prefix='mail', suffix='.' + zone_name)
    data = "{0} {1}".format(pref, host)
    return random_recordset_data('MX', zone_name, records=[data], **kwargs)

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
import uuid
import random

from functionaltests.api.v2.models.blacklist_model import BlacklistModel
from functionaltests.api.v2.models.pool_model import PoolModel
from functionaltests.api.v2.models.transfer_requests_model import \
    TransferRequestsModel
from functionaltests.api.v2.models.transfer_accepts_model import \
    TransferAcceptsModel
from functionaltests.api.v2.models.recordset_model import RecordsetModel
from functionaltests.api.v2.models.zone_model import ZoneModel
from functionaltests.api.v2.models.tld_model import TLDModel


def random_ip():
    return ".".join(str(random.randrange(0, 256)) for _ in range(4))


def random_ipv6():
    def hexes(n):
        return "".join(random.choice("1234567890abcdef") for _ in range(n))
    result = ":".join(hexes(4) for _ in range(8))
    return result.replace("0000", "0")


def random_uuid():
    return uuid.uuid4()


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


def random_transfer_request_data(description=None, target_project_id=None):
    """Generate random zone data, with optional overrides

    :return: A TransferRequestModel
    """

    data = {}

    if description is None:
        data['description'] = random_string(prefix='Description ')

    if target_project_id:
        data['target_project_id'] = target_project_id

    return TransferRequestsModel.from_dict(data)


def random_transfer_accept_data(key=None, zone_transfer_request_id=None):
    """Generate random zone data, with optional overrides

    :return: A TransferRequestModel
    """
    if key is None:
        key = random_string()
    if zone_transfer_request_id is None:
        zone_transfer_request_id = random_uuid()
    return TransferAcceptsModel.from_dict({
        'key': key,
        'zone_transfer_request_id': zone_transfer_request_id})


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


def random_blacklist_data():
    data = {
        "pattern": random_string()
    }
    return BlacklistModel.from_dict(data)


def random_pool_data():
    ns_zone = random_zone_data().name
    data = {
        "name": random_string(),
    }
    records = []
    for i in range(0, 2):
        records.append("ns%s.%s" % (i, ns_zone))
    ns_records = [{"hostname": x, "priority": random.randint(1, 999)}
                  for x in records]
    data["ns_records"] = ns_records

    return PoolModel.from_dict(data)


def random_zonefile_data(name=None, ttl=None):
    """Generate random zone data, with optional overrides

    :return: A ZoneModel
    """
    zone_base = ('$ORIGIN &\n& # IN SOA ns.& nsadmin.& # # # # #\n'
                 '& # IN NS ns.&\n& # IN MX 10 mail.&\nns.& 360 IN A 1.0.0.1')
    if name is None:
        name = random_string(prefix='testdomain', suffix='.com.')
    if ttl is None:
        ttl = str(random.randint(1200, 8400))

    return zone_base.replace('&', name).replace('#', ttl)


def random_spf_recordset(zone_name, data=None, **kwargs):
    data = data or "v=spf1 +all"
    return random_recordset_data('SPF', zone_name, records=[data], **kwargs)


def random_srv_recordset(zone_name, data=None):
    data = data or "10 0 8080 %s.%s" % (random_string(), zone_name)
    return random_recordset_data('SRV', zone_name,
                                 name="_sip._tcp.%s" % zone_name,
                                 records=[data])


def random_sshfp_recordset(zone_name, algorithm_number=None,
                           fingerprint_type=None, fingerprint=None,
                           **kwargs):
    algorithm_number = algorithm_number or 2
    fingerprint_type = fingerprint_type or 1
    fingerprint = fingerprint or \
        "123456789abcdef67890123456789abcdef67890"

    data = "%s %s %s" % (algorithm_number, fingerprint_type, fingerprint)
    return random_recordset_data('SSHFP', zone_name, records=[data], **kwargs)


def random_txt_recordset(zone_name, data=None, **kwargs):
    data = data or "v=spf1 +all"
    return random_recordset_data('TXT', zone_name, records=[data], **kwargs)


def random_tld_data():
    data = {
        "name": random_string(prefix='tld')
    }
    return TLDModel.from_dict(data)


def wildcard_ns_recordset(zone_name):
    name = "*.{0}".format(zone_name)
    records = ["ns.example.com."]
    return random_recordset_data('NS', zone_name, name, records)

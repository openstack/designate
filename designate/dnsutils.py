# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
from dns import rdatatype

from designate import exceptions
from designate import objects


def from_dnspython_zone(dnspython_zone):
    # dnspython never builds a zone with more than one SOA, even if we give
    # it a zonefile that contains more than one
    soa = dnspython_zone.get_rdataset(dnspython_zone.origin, 'SOA')
    if soa is None:
        raise exceptions.BadRequest('An SOA record is required')
    email = soa[0].rname.to_text().rstrip('.')
    email = email.replace('.', '@', 1)
    values = {
        'name': dnspython_zone.origin.to_text(),
        'email': email,
        'ttl': soa.ttl
    }

    zone = objects.Domain(**values)

    rrsets = dnspyrecords_to_recordsetlist(dnspython_zone.nodes)
    zone.recordsets = rrsets
    return zone


def dnspyrecords_to_recordsetlist(dnspython_records):
    rrsets = objects.RecordList()

    for rname in dnspython_records.keys():
        for rdataset in dnspython_records[rname]:
            rrset = dnspythonrecord_to_recordset(rname, rdataset)

            if rrset is None:
                continue

            rrsets.append(rrset)
    return rrsets


def dnspythonrecord_to_recordset(rname, rdataset):
    record_type = rdatatype.to_text(rdataset.rdtype)

    # Create the other recordsets
    values = {
        'name': rname.to_text(),
        'type': record_type
    }

    if rdataset.ttl != 0L:
        values['ttl'] = rdataset.ttl

    rrset = objects.RecordSet(**values)
    rrset.records = objects.RecordList()

    for rdata in rdataset:
        rr = objects.Record(data=rdata.to_text())
        rrset.records.append(rr)
    return rrset

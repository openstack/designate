# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from designate.objects.record import Record
from designate.objects.record import RecordList


class SOA(Record):
    """
    SOA Resource Record Type
    Defined in: RFC1035
    """
    FIELDS = {
        'mname': {
            'schema': {
                'type': 'string',
                'format': 'domainname',
                'maxLength': 255,
            },
            'required': True
        },
        'rname': {
            'schema': {
                'type': 'string',
                'format': 'domainname',
                'maxLength': 255,
            },
            'required': True
        },
        'serial': {
            'schema': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 4294967295,
            },
            'required': True
        },
        'refresh': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 2147483647
            },
            'required': True
        },
        'retry': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 2147483647
            },
            'required': True
        },
        'expire': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 2147483647
            },
            'required': True
        },
        'minimum': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 2147483647
            },
            'required': True
        },
    }

    def _to_string(self):
        return ("%(mname)s %(rname)s %(serial)s %(refresh)s %(retry)s "
                "%(expire)s %(minimum)s" % self)

    def _from_string(self, v):
        mname, rname, serial, refresh, retry, expire, minimum = v.split(' ')
        self.mname = mname
        self.rname = rname
        self.serial = int(serial)
        self.refresh = int(refresh)
        self.retry = int(retry)
        self.expire = int(expire)
        self.minimum = int(minimum)

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 6


class SOAList(RecordList):

    LIST_ITEM_TYPE = SOA

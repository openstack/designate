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
from designate.objects import base
from designate.objects import fields
from designate.objects.record import Record
from designate.objects.record import RecordList


@base.DesignateRegistry.register
class SOA(Record):
    """
    SOA Resource Record Type
    Defined in: RFC1035
    """

    fields = {
        'mname': fields.DomainField(maxLength=255),
        'rname': fields.DomainField(maxLength=255),
        'serial': fields.IntegerFields(minimum=1, maximum=4294967295),
        'refresh': fields.IntegerFields(minimum=0, maximum=2147483647),
        'retry': fields.IntegerFields(minimum=0, maximum=2147483647),
        'expire': fields.IntegerFields(minimum=0, maximum=2147483647),
        'minimum': fields.IntegerFields(minimum=0, maximum=2147483647)
    }

    def from_string(self, value):
        mname, rname, serial, refresh, retry, expire, minimum = (
            value.split(' ')
        )
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


@base.DesignateRegistry.register
class SOAList(RecordList):

    LIST_ITEM_TYPE = SOA

    fields = {
        'objects': fields.ListOfObjectsField('SOA'),
    }

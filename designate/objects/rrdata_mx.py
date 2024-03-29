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
class MX(Record):
    """
    MX Resource Record Type
    Defined in: RFC1035
    """
    fields = {
        'priority': fields.IntegerFields(minimum=0, maximum=65535),
        'exchange': fields.StringFields(maxLength=255),
    }

    def from_string(self, value):
        priority, exchange = value.split(' ')

        if repr(int(priority)) != priority:
            raise ValueError('Value is not an integer')

        if not exchange.endswith('.'):
            raise ValueError('Domain %s does not end with a dot' % exchange)

        self.priority = int(priority)
        self.exchange = exchange

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 15


@base.DesignateRegistry.register
class MXList(RecordList):

    LIST_ITEM_TYPE = MX

    fields = {
        'objects': fields.ListOfObjectsField('MX'),
    }

# Copyright 2018 Canonical Ltd.
#
# Author: Tytus Kurek <tytus.kurek@canonical.com>
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
class NAPTR(Record):
    """
    NAPTR Resource Record Type
    Defined in: RFC2915
    """
    fields = {
        'order': fields.IntegerFields(minimum=0, maximum=65535),
        'preference': fields.IntegerFields(minimum=0, maximum=65535),
        'flags': fields.NaptrFlagsField(),
        'service': fields.NaptrServiceField(),
        'regexp': fields.NaptrRegexpField(),
        'replacement': fields.DomainField(maxLength=255)
    }

    @staticmethod
    def _strip_double_quotes(value):
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        else:
            return value

    def from_string(self, value):
        order, preference, flags, service, regexp, replacement = (
            value.split(' ')
        )
        self.order = int(order)
        self.preference = int(preference)
        self.flags = self._strip_double_quotes(flags)
        self.service = self._strip_double_quotes(service)
        self.regexp = self._strip_double_quotes(regexp)
        self.replacement = replacement

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 35


@base.DesignateRegistry.register
class NAPTRList(RecordList):

    LIST_ITEM_TYPE = NAPTR

    fields = {
        'objects': fields.ListOfObjectsField('NAPTR'),
    }

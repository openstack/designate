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
class CAA(Record):
    """
    CAA Resource Record Type
    Defined in: RFC6844
    """
    fields = {
        'flags': fields.IntegerFields(minimum=0, maximum=1),
        'prpt': fields.CaaPropertyField()
    }

    def from_string(self, value):
        flags, prpt = value.split(' ', 1)
        self.flags = int(flags)
        self.prpt = prpt

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 257


@base.DesignateRegistry.register
class CAAList(RecordList):

    LIST_ITEM_TYPE = CAA

    fields = {
        'objects': fields.ListOfObjectsField('CAA'),
    }

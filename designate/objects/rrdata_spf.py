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
class SPF(Record):
    """
    SPF Resource Record Type
    Defined in: RFC4408
    """
    fields = {
        'txt_data': fields.StringFields()
    }

    def from_string(self, value):
        if not value.startswith('"') and not value.endswith('"'):
            # value with spaces should be quoted as per RFC1035 5.1
            for element in value:
                if element.isspace():
                    raise ValueError(
                        'Empty spaces are not allowed in SPF record, '
                        'unless wrapped in double quotes.'
                    )
        else:
            # quotes within value should be escaped with backslash
            strip_value = value.strip('"')
            for index, char in enumerate(strip_value):
                if char == '"':
                    if strip_value[index - 1] != "\\":
                        raise ValueError(
                            'Quotation marks should be escaped with backslash.'
                        )

        self.txt_data = value

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 99


@base.DesignateRegistry.register
class SPFList(RecordList):

    LIST_ITEM_TYPE = SPF
    fields = {
        'objects': fields.ListOfObjectsField('SPF'),
    }

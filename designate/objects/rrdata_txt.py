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


class TXT(Record):
    """
    TXT Resource Record Type
    Defined in: RFC1035
    """
    FIELDS = {
        'txt_data': {
            'schema': {
                'type': 'string',
                'format': 'txt-data',
                'maxLength': 255,
            },
            'required': True
        }
    }

    def _to_string(self):
        return self.txt_data

    def _from_string(self, value):
        self.txt_data = value

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 16


class TXTList(RecordList):

    LIST_ITEM_TYPE = TXT

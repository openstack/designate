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
class TXT(Record):
    """
    TXT Resource Record Type
    Defined in: RFC1035
    """
    fields = {
        'txt_data': fields.TxtField()
    }

    @staticmethod
    def _is_wrapped_in_double_quotes(value):
        return value.startswith('"') and value.endswith('"')

    @staticmethod
    def _is_missing_double_quote(value):
        return ((value.startswith('"') and not value.endswith('"')) or
                (not value.startswith('"') and value.endswith('"')))

    def _validate_record_single_string(self, value):
        if len(value) > 255:
            raise ValueError(
                'Any TXT record string exceeding 255 characters has to be '
                'split.'
            )

        if self._is_missing_double_quote(value):
            raise ValueError(
                'TXT record is missing a double quote either at beginning '
                'or at end.'
            )

        if not self._is_wrapped_in_double_quotes(value):
            # value with spaces should be quoted as per RFC1035 5.1
            for element in value:
                if element.isspace():
                    raise ValueError(
                        'Empty spaces are not allowed in TXT record, '
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

    def from_string(self, value):
        if len(value) > 255:
            # expecting record containing multiple strings as
            # per rfc7208 3.3 and rfc1035 3.3.14
            stripped_value = value.strip('"')
            if (not self._is_wrapped_in_double_quotes(value) and
                    '" "' not in stripped_value):
                raise ValueError(
                    'TXT record strings over 255 characters have to be split '
                    'into multiple strings wrapped in double quotes.'
                )

            record_strings = stripped_value.split('" "')
            for record_string in record_strings:
                # add back the delimiting quotes after
                # strip and split for each string
                record_string = f'"{record_string}"'
                # further validate each string individually
                self._validate_record_single_string(value=record_string)
        else:
            # validate single TXT record string
            self._validate_record_single_string(value=value)

        self.txt_data = value

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 16


@base.DesignateRegistry.register
class TXTList(RecordList):

    LIST_ITEM_TYPE = TXT
    fields = {
        'objects': fields.ListOfObjectsField('TXT'),
    }

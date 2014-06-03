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
from designate.objects.base import BaseObject


class Record(BaseObject):
    RECORD_FIELDS = ['data', 'priority', 'domain_id', 'managed',
                     'managed_resource_type', 'managed_resource_id',
                     'managed_plugin_name', 'managed_plugin_type', 'hash',
                     'description', 'status', 'tenant_id', 'recordset_id',
                     'managed_tenant_id', 'managed_resource_region',
                     'managed_extra']
    RRDATA_FIELDS = []

    @classmethod
    def from_sqla(cls, obj):
        """
        Convert from a SQLA Model to a Designate Object
        Eventually, when we move from SQLA ORM to SQLA Core, this can be
        removed.
        This overrides the method for Records
        """
        cls.FIELDS = cls.RECORD_FIELDS + cls.RRDATA_FIELDS
        return super(Record, cls).from_sqla(obj)

    def __init__(self, **kwargs):
        self.FIELDS = self.RECORD_FIELDS + self.RRDATA_FIELDS
        super(Record, self).__init__(**kwargs)
        if len(self.RRDATA_FIELDS) > 0:
            self.from_text()
            self.to_text()

    def from_text(self):
        """
        self.'data' contains the text version of the rdata fields.
        This function splits self.data and puts it into the rdata fields.
        """
        # If length is one, then do not split - this is needed for SPF and TXT
        # records.
        if len(self.RRDATA_FIELDS) == 1:
            setattr(self, self.RRDATA_FIELDS[0], self.data)
        else:
            rdata_values = self.data.split()
            if len(self.RRDATA_FIELDS) != len(rdata_values):
                raise TypeError("Incorrect number of values. Expected: %s."
                                " Got %s" % (self.RRDATA_FIELDS, rdata_values))
            index = 0
            # TODO(vinod): Currently all the attributes are set as strings.
            # Once the schemas for the records are defined, the various fields
            # need to be transformed according to the schema.
            for rdata_field in self.RRDATA_FIELDS:
                setattr(self, rdata_field, rdata_values[index])
                index += 1

    def to_text(self):
        """
        This function joins the rdata fields and puts it into self.data
        """
        rdata_values = []
        for rdata_field in self.RRDATA_FIELDS:
            rdata_values.append(getattr(self, rdata_field))
        self.data = ' '.join(rdata_values)

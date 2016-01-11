# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
from designate.objects import base
from designate import utils


class ZoneMaster(base.DictObjectMixin, base.PersistentObjectMixin,
                 base.DesignateObject):
    FIELDS = {
        'zone_id': {},
        'host': {
            'schema': {
                'type': 'string',
                'format': 'ip-or-host',
                'required': True,
            },
        },
        'port': {
            'schema': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535,
                'required': True,
            },
        }
    }

    def to_data(self):
        return "%(host)s:%(port)d" % self.to_dict()

    @classmethod
    def from_data(cls, data):
        host, port = utils.split_host_port(data)
        return cls.from_dict({"host": host, "port": port})


class ZoneMasterList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = ZoneMaster

    def to_data(self):
        rlist = []
        for item in self.objects:
            rlist.append(item.to_data())
        return rlist

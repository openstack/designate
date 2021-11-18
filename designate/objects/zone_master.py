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
from oslo_versionedobjects import base as ovoo_base

from designate.objects import base
from designate.objects import fields
from designate import utils


@base.DesignateRegistry.register
class ZoneMaster(base.DesignateObject,
                 base.DictObjectMixin,
                 base.PersistentObjectMixin,
                 base.SoftDeleteObjectMixin):
    def __init__(self, *args, **kwargs):
        super(ZoneMaster, self).__init__(*args, **kwargs)

    fields = {
        'zone_id': fields.UUIDFields(nullable=True),
        'host': fields.StringFields(),
        'port': fields.IntegerFields(minimum=1, maximum=65535)
    }

    def to_data(self):
        return "{}:{}".format(self.host, self.port)

    @classmethod
    def from_data(cls, data):
        host, port = utils.split_host_port(data)
        dict_data = {"host": host, "port": port}
        return cls(**dict_data)


@base.DesignateRegistry.register
class ZoneMasterList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = ZoneMaster
    fields = {
        'objects': fields.ListOfObjectsField('ZoneMaster'),
    }

    @classmethod
    def from_list(cls, _list):
        instance = cls()

        for item in _list:
            instance.append(cls.LIST_ITEM_TYPE.from_dict(item))

        return instance

    def to_list(self):

        list_ = []

        for item in self.objects:
            if isinstance(item, ovoo_base.ObjectListBase):
                list_.append(item.to_list())
            elif isinstance(item, base.DesignateObject):
                list_.append(item.to_dict())
            else:
                list_.append(item)

        return list_

    def to_data(self):
        zone_master_list = []
        for item in self.objects:
            zone_master_list.append(item.to_data())
        return zone_master_list

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
from designate.objects.domain_attribute import DomainAttribute
from designate.objects.domain_attribute import DomainAttributeList


class Domain(base.DictObjectMixin, base.SoftDeleteObjectMixin,
             base.PersistentObjectMixin, base.DesignateObject):
    FIELDS = {
        'tenant_id': {},
        'name': {},
        'email': {},
        'ttl': {},
        'refresh': {},
        'retry': {},
        'expire': {},
        'minimum': {},
        'parent_domain_id': {},
        'serial': {},
        'description': {},
        'status': {},
        'action': {},
        'pool_id': {},
        'recordsets': {
            'relation': True,
            'relation_cls': 'RecordSetList'
        },
        'attributes': {
            'relation': True,
            'relation_cls': 'DomainAttributeList'
        },
        'type': {},
        'transferred_at': {},
    }

    @property
    def masters(self):
        if self.obj_attr_is_set('attributes'):
            return [i.value for i in self.attributes if i.key == 'master']
        else:
            return None

    # TODO(ekarlso): Make this a property sette rpr Kiall's comments later.
    def set_masters(self, masters):
        attributes = DomainAttributeList()

        for m in masters:
            obj = DomainAttribute(key='master', value=m)
            attributes.append(obj)
        self.attributes = attributes

    def get_master_by_ip(self, host):
        """
        Utility to get the master by it's ip for this domain.
        """
        for srv in self.masters:
            if host == srv.split(":")[0]:
                return srv
        return False


class DomainList(base.ListObjectMixin, base.DesignateObject,
                 base.PagedListObjectMixin):
    LIST_ITEM_TYPE = Domain

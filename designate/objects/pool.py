# Copyright (c) 2014 Rackspace Hosting
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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
from designate.objects import fields


@base.DesignateRegistry.register
class Pool(base.DictObjectMixin, base.PersistentObjectMixin,
           base.DesignateObject):
    fields = {
        'name': fields.StringFields(maxLength=50),
        'description': fields.StringFields(nullable=True, maxLength=160),
        'tenant_id': fields.StringFields(maxLength=36, nullable=True),
        'provisioner': fields.StringFields(nullable=True, maxLength=160),
        'attributes': fields.ObjectFields('PoolAttributeList', nullable=True),
        'ns_records': fields.ObjectFields('PoolNsRecordList', nullable=True),
        'nameservers': fields.ObjectFields('PoolNameserverList',
                                           nullable=True),
        'targets': fields.ObjectFields('PoolTargetList', nullable=True),
        'also_notifies': fields.ObjectFields('PoolAlsoNotifyList',
                                             nullable=True),
        'catalog_zone': fields.ObjectFields('PoolCatalogZone',
                                            nullable=True),
    }

    STRING_KEYS = [
        'id', 'name'
    ]


@base.DesignateRegistry.register
class PoolList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = Pool

    fields = {
        'objects': fields.ListOfObjectsField('Pool'),
    }

    def __contains__(self, pool):
        for p in self.objects:
            if p.id == pool.id:
                return True
        return False

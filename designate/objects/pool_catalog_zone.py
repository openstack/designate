# Copyright (c) 2023 inovex GmbH
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
from designate.common import constants
from designate.objects import base
from designate.objects import fields


@base.DesignateRegistry.register
class PoolCatalogZone(base.DictObjectMixin, base.PersistentObjectMixin,
                     base.DesignateObject):
    fields = {
        'catalog_zone_fqdn': fields.DomainField(),
        'catalog_zone_refresh': fields.IntegerFields(
            nullable=True, minimum=0, maximum=2147483647),
        'catalog_zone_tsig_key': fields.StringFields(
            nullable=True, maxLength=160),
        'catalog_zone_tsig_algorithm': fields.EnumField(
            nullable=True, valid_values=constants.TSIG_ALGORITHMS),
    }

    STRING_KEYS = [
        'catalog_zone_fqdn',
    ]

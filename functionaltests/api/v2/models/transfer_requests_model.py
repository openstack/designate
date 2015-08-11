# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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

from functionaltests.common.models import BaseModel
from functionaltests.common.models import CollectionModel
from functionaltests.common.models import EntityModel


class TransferRequestsData(BaseModel):
    pass


class TransferRequestsModel(EntityModel):
    ENTITY_NAME = 'transfer_request'
    MODEL_TYPE = TransferRequestsData


class TransferRequestsListModel(CollectionModel):
    COLLECTION_NAME = 'transfer_requests'
    MODEL_TYPE = TransferRequestsData

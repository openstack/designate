"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json


class BaseModel(object):

    @classmethod
    def from_json(cls, json_str):
        return cls.from_dict(json.loads(json_str))

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        model = cls()
        for key in data:
            setattr(model, key, data.get(key))
        return model

    def to_dict(self):
        result = {}
        for key in self.__dict__:
            result[key] = getattr(self, key)
            if isinstance(result[key], BaseModel):
                result[key] = result[key].to_dict()
        return result

    def __str__(self):
        return "%s" % self.to_dict()


class LinksModel(BaseModel):
    pass


class MetadataModel(BaseModel):
    pass


class CollectionModel(BaseModel):
    """
    {
        'collection_name' : [ <models> ],
        'links': { <links> },
        'metdata': { <metadata> },
    }
    """

    SUB_MODELS = {
        'links': LinksModel,
        'metadata': MetadataModel,
    }

    @classmethod
    def from_dict(cls, data):
        model = super(CollectionModel, cls).from_dict(data)

        # deserialize e.g. data['zones']
        collection = []
        if hasattr(model, cls.COLLECTION_NAME):
            for d in getattr(model, cls.COLLECTION_NAME):
                collection.append(cls.MODEL_TYPE.from_dict(d))
            setattr(model, cls.COLLECTION_NAME, collection)

        # deserialize data['
        for key, model_type in cls.SUB_MODELS.items():
            if hasattr(model, key):
                val = getattr(model, key)
                setattr(model, key, model_type.from_dict(val))

        return model


class EntityModel(BaseModel):
    """
    { 'entity_name': { <data> } }
    """

    @classmethod
    def from_dict(cls, data):
        model = super(EntityModel, cls).from_dict(data)
        if hasattr(model, cls.ENTITY_NAME):
            val = getattr(model, cls.ENTITY_NAME)
            setattr(model, cls.ENTITY_NAME, cls.MODEL_TYPE.from_dict(val))
        return model

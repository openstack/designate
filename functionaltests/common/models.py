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

        # deserialize data['links'], data['metadata'], etc
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


class ZoneFile(object):

    def __init__(self, origin, ttl, records):
        self.origin = origin
        self.ttl = ttl
        self.records = records

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @classmethod
    def from_text(cls, text):
        """Return a ZoneFile from a string containing the zone file contents"""
        # filter out empty lines and strip all leading/trailing whitespace.
        # this assumes no multiline records
        lines = [x.strip() for x in text.split('\n') if x.strip()]

        assert lines[0].startswith('$ORIGIN')
        assert lines[1].startswith('$TTL')

        return ZoneFile(
            origin=lines[0].split(' ')[1],
            ttl=int(lines[1].split(' ')[1]),
            records=[ZoneFileRecord.from_text(x) for x in lines[2:]],
        )


class ZoneFileRecord(object):

    def __init__(self, name, type, data):
        self.name = str(name)
        self.type = str(type)
        self.data = str(data)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    @classmethod
    def from_text(cls, text):
        """Create a ZoneFileRecord from a line of text of a zone file, like:

            mydomain.com. IN NS ns1.example.com.
        """
        # assumes records don't have a TTL between the name and the class.
        # assumes no parentheses in the record, all on a single line.
        parts = [x for x in text.split(' ', 4) if x.strip()]
        name, rclass, rtype, data = parts
        assert rclass == 'IN'
        return cls(name=name, type=rtype, data=data)

    @classmethod
    def records_from_recordset(cls, recordset):
        """Returns a list of ZoneFileRecords, one for each entry in the
        recordset's list of records
        """
        return [
            cls(name=recordset.name, type=recordset.type, data=data)
            for data in recordset.records
        ]

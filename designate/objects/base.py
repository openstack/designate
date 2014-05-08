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


class BaseObject(object):
    BASE_FIELDS = ('id', 'created_at', 'updated_at', 'version')
    FIELDS = []

    @classmethod
    def from_sqla(cls, obj):
        """
        Convert from a SQLA Model to a Designate Object
        Eventually, when we move from SQLA ORM to SQLA Core, this can be
        removed.
        """
        fields = {}
        fieldnames = []
        fieldnames += cls.FIELDS
        fieldnames += cls.BASE_FIELDS

        for fieldname in fieldnames:
            if hasattr(obj, fieldname):
                fields[fieldname] = getattr(obj, fieldname)

        return cls(**fields)

    @classmethod
    def from_primitive(cls, primitive):
        """
        Construct an object from primitive types.  This is used while
        deserializing the object.
        NOTE: Currently all the designate objects contain primitive types that
        do not need special handling.  If this changes we need to modify this
        function.
        """
        fields = primitive['designate_object.data']
        return cls(**fields)

    def __init__(self, **kwargs):
        fieldnames = []
        fieldnames += self.FIELDS
        fieldnames += self.BASE_FIELDS
        self._fieldnames = []

        for name, value in kwargs.items():
            if name in fieldnames:
                # We set _fieldnames to only the fields that are set.
                # This is useful in objects like Tenant which do not have
                # all the BASE_FIELDS set.
                # Only the fields in _fieldnames are displayed.
                self._fieldnames.append(name)
                setattr(self, name, value)
            else:
                raise TypeError("'%s' is an invalid keyword argument" % name)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        self._i = iter(self._fieldnames)
        return self

    def __contains__(self, item):
        # Some of the tests like the following one need this function to
        # succeed. Hence we implement this function.
        #    self.assertIn('status', domain)
        return item in self._fieldnames

    def next(self):
        n = self._i.next()
        return n, getattr(self, n)

    def update(self, values):
        """ Make the model object behave like a dict """
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        """
        Make the model object behave like a dict.

        Includes attributes from joins.
        """
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()

    def get(self, key, default=None):
        return getattr(self, key, default)

    def to_primitive(self):
        """
        Convert the object to primitive types so that the object can be
        serialized.
        NOTE: Currently all the designate objects contain primitive types that
        do not need special handling.  If this changes we need to modify this
        function.
        """
        primitive = {}
        class_name = self.__class__.__name__
        if self.__module__:
            class_name = self.__module__ + '.' + self.__class__.__name__
        primitive['designate_object.name'] = class_name
        primitive['designate_object.data'] = dict(self)
        return primitive

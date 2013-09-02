# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Author: Patrick Galbraith <patg@hp.com>
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
from sqlalchemy import Column, DateTime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import object_mapper
from sqlalchemy.types import CHAR
from designate.openstack.common import timeutils
from designate import exceptions


class Base(object):
    __abstract__ = True
    __table_initialized__ = False

    def save(self, session):
        """ Save this object """
        session.add(self)

        try:
            session.flush()
        except IntegrityError as e:
            non_unique_strings = (
                'duplicate entry',
                'not unique'
            )

            for non_unique_string in non_unique_strings:
                if non_unique_string in str(e).lower():
                    raise exceptions.Duplicate(str(e))

            # Not a Duplicate error.. Re-raise.
            raise

    def delete(self, session):
        """ Delete this object """
        session.delete(self)
        session.flush()

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        columns = dict(object_mapper(self).columns).keys()
        # NOTE(russellb): Allow models to specify other keys that can be looked
        # up, beyond the actual db columns.  An example would be the 'name'
        # property for an Instance.
        if hasattr(self, '_extra_keys'):
            columns.extend(self._extra_keys())
        self._i = iter(columns)
        return self

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


class SoftDeleteMixin(object):
    deleted = Column(CHAR(32), nullable=False, default="0", server_default="0")
    deleted_at = Column(DateTime, nullable=True, default=None)

    def soft_delete(self, session=None):
        """ Mark this object as deleted. """
        self.deleted = self.id.replace('-', '')
        self.deleted_at = timeutils.utcnow()

        if hasattr(self, 'status'):
            self.status = "DELETED"

        self.save(session=session)

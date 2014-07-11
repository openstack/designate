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
from oslo.db.sqlalchemy import models
from oslo.db import exception as oslo_db_exc
from sqlalchemy import Column, DateTime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import CHAR

from designate.openstack.common import timeutils
from designate import exceptions


class Base(models.ModelBase):
    # TODO(ekarlso): Remove me when o.db patch lands for this.
    def save(self, session):
        """Save this object"""
        session.add(self)

        try:
            session.flush()
        except oslo_db_exc.DBDuplicateEntry as e:
            raise exceptions.Duplicate(str(e))
        except IntegrityError:
            raise

    def delete(self, session):
        session.delete(self)
        session.flush()


# TODO(ekarlso): Get this into o.db?
class SoftDeleteMixin(object):
    deleted = Column(CHAR(32), nullable=False, default="0", server_default="0")
    deleted_at = Column(DateTime, nullable=True, default=None)

    def soft_delete(self, session):
        """Mark this object as deleted."""
        self.deleted = self.id.replace('-', '')
        self.deleted_at = timeutils.utcnow()

        if hasattr(self, 'status'):
            self.status = "DELETED"

        self.save(session=session)

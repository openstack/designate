# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Artom Lifshitz <artom.lifshitz@enovance.com>
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

import logging

from oslo_config import cfg
from oslo_utils import excutils

from designate import backend
from designate.backend import base


LOG = logging.getLogger(__name__)
CFG_GROUP = 'backend:multi'


class MultiBackend(base.Backend):
    """
    Multi-backend backend

    This backend dispatches calls to a master backend and a slave backend.
    It enforces master/slave ordering semantics as follows:

    Creates for tsigkeys, servers and domains are done on the master first,
    then on the slave.

    Updates for tsigkeys, servers and domains and all operations on records
    are done on the master only. It's assumed masters and slaves use an
    external mechanism to sync existing domains, most likely XFR.

    Deletes are done on the slave first, then on the master.

    If the create on the slave fails, the domain/tsigkey/server is deleted from
    the master. If delete on the master fails, the domain/tdigkey/server is
    recreated on the slave.
    """
    __plugin_name__ = 'multi'

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(
            name=CFG_GROUP, title="Configuration for multi-backend Backend"
        )

        opts = [
            cfg.StrOpt('master', default='fake', help='Master backend'),
            cfg.StrOpt('slave', default='fake', help='Slave backend'),
        ]

        return [(group, opts)]

    def __init__(self, central_service):
        super(MultiBackend, self).__init__(central_service)
        self.central = central_service
        self.master = backend.get_backend(cfg.CONF[CFG_GROUP].master,
                                          central_service)
        self.slave = backend.get_backend(cfg.CONF[CFG_GROUP].slave,
                                         central_service)

    def start(self):
        self.master.start()
        self.slave.start()

    def stop(self):
        self.slave.stop()
        self.master.stop()

    def create_tsigkey(self, context, tsigkey):
        self.master.create_tsigkey(context, tsigkey)
        try:
            self.slave.create_tsigkey(context, tsigkey)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.master.delete_tsigkey(context, tsigkey)

    def update_tsigkey(self, context, tsigkey):
        self.master.update_tsigkey(context, tsigkey)

    def delete_tsigkey(self, context, tsigkey):
        self.slave.delete_tsigkey(context, tsigkey)
        try:
            self.master.delete_tsigkey(context, tsigkey)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.slave.create_tsigkey(context, tsigkey)

    def create_zone(self, context, zone):
        self.master.create_zone(context, zone)
        try:
            self.slave.create_zone(context, zone)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.master.delete_zone(context, zone)

    def update_zone(self, context, zone):
        self.master.update_zone(context, zone)

    def delete_zone(self, context, zone):
        # Fetch the full zone from Central first, as we may
        # have to recreate it on slave if delete on master fails
        deleted_context = context.deepcopy()
        deleted_context.show_deleted = True

        full_domain = self.central.find_zone(
            deleted_context, {'id': zone['id']})

        self.slave.delete_zone(context, zone)
        try:
            self.master.delete_zone(context, zone)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.slave.create_zone(context, zone)

                [self.slave.create_record(context, zone, record)
                 for record in self.central.find_records(
                     context, {'domain_id': full_domain['id']})]

    def create_recordset(self, context, zone, recordset):
        self.master.create_recordset(context, zone, recordset)

    def update_recordset(self, context, zone, recordset):
        self.master.update_recordset(context, zone, recordset)

    def delete_recordset(self, context, zone, recordset):
        self.master.delete_recordset(context, zone, recordset)

    def create_record(self, context, zone, recordset, record):
        self.master.create_record(context, zone, recordset, record)

    def update_record(self, context, zone, recordset, record):
        self.master.update_record(context, zone, recordset, record)

    def delete_record(self, context, zone, recordset, record):
        self.master.delete_record(context, zone, recordset, record)

    def ping(self, context):
        return {
            'master': self.master.ping(context),
            'slave': self.slave.ping(context)
        }

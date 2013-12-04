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

from designate import backend
from designate import exceptions
from designate.backend import base
from designate.openstack.common import excutils
from oslo.config import cfg
import logging

LOG = logging.getLogger(__name__)

CFG_GRP = 'backend:multi'

cfg.CONF.register_group(cfg.OptGroup(
    name=CFG_GRP, title="Configuration for multi-backend Backend"
))

cfg.CONF.register_opts([
    cfg.StrOpt('master', default='fake', help='Master backend'),
    cfg.StrOpt('slave', default='fake', help='Slave backend'),
], group=CFG_GRP)


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

    def __init__(self, central_service):
        super(MultiBackend, self).__init__(central_service)
        self.central = central_service
        self.master = backend.get_backend(cfg.CONF[CFG_GRP].master,
                                          central_service)
        self.slave = backend.get_backend(cfg.CONF[CFG_GRP].slave,
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
        except (exceptions.Base, exceptions.Backend):
            with excutils.save_and_reraise_exception():
                self.master.delete_tsigkey(context, tsigkey)

    def update_tsigkey(self, context, tsigkey):
        self.master.update_tsigkey(context, tsigkey)

    def delete_tsigkey(self, context, tsigkey):
        self.slave.delete_tsigkey(context, tsigkey)
        try:
            self.master.delete_tsigkey(context, tsigkey)
        except (exceptions.Base, exceptions.Backend):
            with excutils.save_and_reraise_exception():
                self.slave.create_tsigkey(context, tsigkey)

    def create_domain(self, context, domain):
        self.master.create_domain(context, domain)
        try:
            self.slave.create_domain(context, domain)
        except (exceptions.Base, exceptions.Backend):
            with excutils.save_and_reraise_exception():
                self.master.delete_domain(context, domain)

    def update_domain(self, context, domain):
        self.master.update_domain(context, domain)

    def delete_domain(self, context, domain):
        # Get the "full" domain (including id) from Central first, as we may
        # have to recreate it on slave if delete on master fails
        full_domain = self.central.find_domain(
            context, criterion={'name': domain['name']})
        self.slave.delete_domain(context, domain)
        try:
            self.master.delete_domain(context, domain)
        except (exceptions.Base, exceptions.Backend):
            with excutils.save_and_reraise_exception():
                self.slave.create_domain(context, domain)
                [self.slave.create_record(context, domain, record)
                 for record in self.central.find_records(context,
                                                         full_domain['id'])]

    def create_server(self, context, server):
        self.master.create_server(context, server)
        try:
            self.slave.create_server(context, server)
        except (exceptions.Base, exceptions.Backend):
            with excutils.save_and_reraise_exception():
                self.master.delete_server(context, server)

    def update_server(self, context, server):
        self.master.update_server(context, server)

    def delete_server(self, context, server):
        self.slave.delete_server(context, server)
        try:
            self.master.delete_server(context, server)
        except (exceptions.Base, exceptions.Backend):
            with excutils.save_and_reraise_exception():
                self.slave.create_server(context, server)

    def create_record(self, context, domain, record):
        self.master.create_record(context, domain, record)

    def update_record(self, context, domain, record):
        self.master.update_record(context, domain, record)

    def delete_record(self, context, domain, record):
        self.master.delete_record(context, domain, record)

    def ping(self, context):
        return {
            'master': self.master.ping(context),
            'slave': self.slave.ping(context)
        }

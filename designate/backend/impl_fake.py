# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from designate.openstack.common import log as logging
from designate.openstack.common.gettextutils import _LI
from designate.backend import base

LOG = logging.getLogger(__name__)


class FakeBackend(base.Backend):
    __plugin_name__ = 'fake'

    def __init__(self, *args, **kwargs):
        super(FakeBackend, self).__init__(*args, **kwargs)

    def create_tsigkey(self, context, tsigkey):
        LOG.info(_LI('Create TSIG Key %r') % tsigkey)

    def update_tsigkey(self, context, tsigkey):
        LOG.info(_LI('Update TSIG Key %r') % tsigkey)

    def delete_tsigkey(self, context, tsigkey):
        LOG.info(_LI('Delete TSIG Key %r') % tsigkey)

    def create_server(self, context, server):
        LOG.info(_LI('Create Server %r') % server)

    def update_server(self, context, server):
        LOG.info(_LI('Update Server %r') % server)

    def delete_server(self, context, server):
        LOG.info(_LI('Delete Server %r') % server)

    def create_domain(self, context, domain):
        LOG.info(_LI('Create Domain %r') % domain)

    def update_domain(self, context, domain):
        LOG.info(_LI('Update Domain %r') % domain)

    def delete_domain(self, context, domain):
        LOG.info(_LI('Delete Domain %r') % domain)

    def create_recordset(self, context, domain, recordset):
        LOG.info(_LI('Create RecordSet %r / %r') % (domain, recordset))

    def update_recordset(self, context, domain, recordset):
        LOG.info(_LI('Update RecordSet %r / %r') % (domain, recordset))

    def delete_recordset(self, context, domain, recordset):
        LOG.info(_LI('Delete RecordSet %r / %r') % (domain, recordset))

    def create_record(self, context, domain, recordset, record):
        LOG.info(_LI('Create Record %r / %r / %r') %
                 (domain, recordset, record))

    def update_record(self, context, domain, recordset, record):
        LOG.info(_LI('Update Record %r / %r / %r') %
                 (domain, recordset, record))

    def delete_record(self, context, domain, recordset, record):
        LOG.info(_LI('Delete Record %r / %r / %r') %
                 (domain, recordset, record))

    def sync_domain(self, context, domain, records):
        LOG.info(_LI('Sync Domain %r / %r') % (domain, records))

    def sync_record(self, context, domain, record):
        LOG.info(_LI('Sync Record %r / %r') % (domain, record))

    def ping(self, context):
        LOG.info(_LI('Ping'))

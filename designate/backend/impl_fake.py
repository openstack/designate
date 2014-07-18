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
from designate.i18n import _LI
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
        LOG.info(_LI('Create RecordSet %(domain)r / %(recordset)r') %
                 {'domain': domain, 'recordset': recordset})

    def update_recordset(self, context, domain, recordset):
        LOG.info(_LI('Update RecordSet %(domain)r / %(recordset)r') %
                 {'domain': domain, 'recordset': recordset})

    def delete_recordset(self, context, domain, recordset):
        LOG.info(_LI('Delete RecordSet %(domain)r / %(recordset)r') %
                 {'domain': domain, 'recordset': recordset})

    def create_record(self, context, domain, recordset, record):
        LOG.info(_LI('Create Record %(domain)r / %(recordset)r / %(record)r') %
                 {'domain': domain, 'recordset': recordset, 'record': record})

    def update_record(self, context, domain, recordset, record):
        LOG.info(_LI('Update Record %(domain)r / %(recordset)r / %(record)r') %
                 {'domain': domain, 'recordset': recordset, 'record': record})

    def delete_record(self, context, domain, recordset, record):
        LOG.info(_LI('Delete Record %(domain)r / %(recordset)r / %(record)r') %
                 {'domain': domain, 'recordset': recordset, 'record': record})

    def sync_domain(self, context, domain, records):
        LOG.info(_LI('Sync Domain %(domain)r / %(records)r') %
                 {'domain': domain, 'records': records})

    def sync_record(self, context, domain, record):
        LOG.info(_LI('Sync Record %(domain)r / %(record)r') %
                 {'domain': domain, 'record': record})

    def ping(self, context):
        LOG.info(_LI('Ping'))

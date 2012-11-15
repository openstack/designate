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
from moniker.openstack.common import log as logging
from moniker.backend import base

LOG = logging.getLogger(__name__)


class FakeBackend(base.Backend):
    __plugin_name__ = 'fake'

    def __init__(self, *args, **kwargs):
        super(FakeBackend, self).__init__(*args, **kwargs)

        self.create_domain_calls = []
        self.update_domain_calls = []
        self.delete_domain_calls = []
        self.create_record_calls = []
        self.update_record_calls = []
        self.delete_record_calls = []

    def create_domain(self, context, domain):
        LOG.info('Create Domain %r' % domain)
        self.create_domain_calls.append((context, domain))

    def update_domain(self, context, domain):
        LOG.debug('Update Domain %r' % domain)
        self.update_domain_calls.append((context, domain))

    def delete_domain(self, context, domain):
        LOG.debug('Delete Domain %r' % domain)
        self.delete_domain_calls.append((context, domain))

    def create_record(self, context, domain, record):
        LOG.debug('Create Record %r / %r' % (domain, record))
        self.create_record_calls.append((context, domain, record))

    def update_record(self, context, domain, record):
        LOG.debug('Update Record %r / %r' % (domain, record))
        self.update_record_calls.append((context, domain, record))

    def delete_record(self, context, domain, record):
        LOG.debug('Delete Record %r / %r' % (domain, record))
        self.delete_record_calls.append((context, domain, record))

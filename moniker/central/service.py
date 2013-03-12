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
import re
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.openstack.common.rpc import service as rpc_service
from moniker import exceptions
from moniker import policy
from moniker import storage
from moniker import utils
from moniker import backend

LOG = logging.getLogger(__name__)


class Service(rpc_service.Service):
    def __init__(self, *args, **kwargs):
        backend_driver = cfg.CONF['service:central'].backend_driver
        self.backend = backend.get_backend(backend_driver,
                                           central_service=self)

        kwargs.update(
            host=cfg.CONF.host,
            topic=cfg.CONF.central_topic,
        )

        policy.init_policy()

        super(Service, self).__init__(*args, **kwargs)

        # Get a storage connection
        self.storage = storage.get_storage()

    def start(self):
        self.backend.start()

        super(Service, self).start()

    def stop(self):
        super(Service, self).stop()

        self.backend.stop()

    def _is_blacklisted_domain_name(self, context, domain_name):
        """
        Ensures the provided domain_name is not blacklisted.
        """
        blacklists = cfg.CONF['service:central'].domain_name_blacklist

        for blacklist in blacklists:
            if bool(re.search(blacklist, domain_name)):
                return blacklist

        return False

    def _is_valid_record_name(self, context, domain, record_name, record_type):
        if not record_name.endswith('.'):
            raise ValueError('Please supply a FQDN')

        # Record must be contained in the parent zone.
        if not record_name.endswith(domain['name']):
            raise exceptions.BadRequest('Records must be contained within '
                                        'their parent zone.')

        # CNAME's must not be created at the zone apex.
        if record_type == 'CNAME' and record_name == domain['name']:
            raise exceptions.BadRequest('%s records may not be created at '
                                        'the zone apex' % record_type)

        # CNAME's must not share a name with other records
        criterion = {'name': record_name}

        if record_type != 'CNAME':
            criterion['type'] = 'CNAME'

        records = self.storage.get_records(context, domain['id'],
                                           criterion=criterion)
        if len(records) > 0:
            raise exceptions.BadRequest('CNAME records must not share a name'
                                        'with any other records')

        if record_type == 'CNAME':
            # CNAME's may not have children. Ever.
            criterion = {'name': '%%.%s' % record_name}
            records = self.storage.get_records(context, domain['id'],
                                               criterion=criterion)

            if len(records) > 0:
                raise exceptions.BadRequest('CNAME records must not have any '
                                            'child records')

        else:
            # No record may have a CNAME as a parent
            if self._is_subrecord(context, domain, record_name,
                                  {'type': 'CNAME'}):
                raise exceptions.BadRequest('Records must not be children of '
                                            'a CNAME record')

        return True

    def _is_subdomain(self, context, domain_name):
        # Break the name up into it's component labels
        labels = domain_name.split(".")

        i = 1

        # Starting with label #2, search for matching domain's in the database
        while (i < len(labels)):
            name = '.'.join(labels[i:])

            try:
                domain = self.storage.find_domain(context, {'name': name})
            except exceptions.DomainNotFound:
                i += 1
            else:
                return domain

        return False

    def _is_subrecord(self, context, domain, record_name, criterion):
        # Break the names up into their component labels
        domain_labels = domain['name'].split(".")
        record_labels = record_name.split(".")

        i = 1
        j = len(record_labels) - len(domain_labels)

        # Starting with label #2, search for matching records's in the database
        while (i <= j):
            criterion['name'] = '.'.join(record_labels[i:])

            records = self.storage.get_records(context, domain['id'],
                                               criterion)

            if len(records) == 0:
                i += 1
            else:
                return records

        return False

    # Server Methods
    def create_server(self, context, values):
        policy.check('create_server', context)

        server = self.storage.create_server(context, values)

        utils.notify(context, 'api', 'server.create', server)

        return server

    def get_servers(self, context, criterion=None):
        policy.check('get_servers', context)

        return self.storage.get_servers(context, criterion)

    def get_server(self, context, server_id):
        policy.check('get_server', context, {'server_id': server_id})

        return self.storage.get_server(context, server_id)

    def update_server(self, context, server_id, values):
        policy.check('update_server', context, {'server_id': server_id})

        server = self.storage.update_server(context, server_id, values)

        utils.notify(context, 'api', 'server.update', server)

        return server

    def delete_server(self, context, server_id):
        policy.check('delete_server', context, {'server_id': server_id})

        server = self.storage.get_server(context, server_id)

        utils.notify(context, 'api', 'server.delete', server)

        return self.storage.delete_server(context, server_id)

    # TSIG Key Methods
    def create_tsigkey(self, context, values):
        policy.check('create_tsigkey', context)

        tsigkey = self.storage.create_tsigkey(context, values)

        try:
            self.backend.create_tsigkey(context, tsigkey)
        except exceptions.Backend:
            # Re-raise Backend exceptions as is..
            raise
        except Exception, e:
            raise exceptions.Backend('Unknown backend failure: %s' % e)

        utils.notify(context, 'api', 'tsigkey.create', tsigkey)

        return tsigkey

    def get_tsigkeys(self, context, criterion=None):
        policy.check('get_tsigkeys', context)

        return self.storage.get_tsigkeys(context, criterion)

    def get_tsigkey(self, context, tsigkey_id):
        policy.check('get_tsigkey', context, {'tsigkey_id': tsigkey_id})

        return self.storage.get_tsigkey(context, tsigkey_id)

    def update_tsigkey(self, context, tsigkey_id, values):
        policy.check('update_tsigkey', context, {'tsigkey_id': tsigkey_id})

        tsigkey = self.storage.update_tsigkey(context, tsigkey_id, values)

        try:
            self.backend.update_tsigkey(context, tsigkey)
        except exceptions.Backend:
            # Re-raise Backend exceptions as is..
            raise
        except Exception, e:
            raise exceptions.Backend('Unknown backend failure: %s' % e)

        utils.notify(context, 'api', 'tsigkey.update', tsigkey)

        return tsigkey

    def delete_tsigkey(self, context, tsigkey_id):
        policy.check('delete_tsigkey', context, {'tsigkey_id': tsigkey_id})

        tsigkey = self.storage.get_tsigkey(context, tsigkey_id)

        try:
            self.backend.delete_tsigkey(context, tsigkey)
        except exceptions.Backend:
            # Re-raise Backend exceptions as is..
            raise
        except Exception, e:
            raise exceptions.Backend('Unknown backend failure: %s' % e)

        utils.notify(context, 'api', 'tsigkey.delete', tsigkey)

        return self.storage.delete_tsigkey(context, tsigkey_id)

    # Domain Methods
    def create_domain(self, context, values):
        values['tenant_id'] = context.tenant_id

        target = {
            'tenant_id': values['tenant_id'],
            'domain_name': values['name']
        }

        policy.check('create_domain', context, target)

        # Ensure the domain is not blacklisted
        if self._is_blacklisted_domain_name(context, values['name']):
            # Raises an exception if the policy check is denied
            policy.check('use_blacklisted_domain', context)

        # Handle sub-domains appropriately
        parent_domain = self._is_subdomain(context, values['name'])

        if parent_domain:
            if parent_domain['tenant_id'] == values['tenant_id']:
                # Record the Parent Domain ID
                values['parent_domain_id'] = parent_domain['id']
            else:
                raise exceptions.Forbidden('Unable to create subdomain in '
                                           'another tenants domain')

        # NOTE(kiall): Fetch the servers before creating the domain, this way
        #              we can prevent domain creation if no servers are
        #              configured.
        servers = self.storage.get_servers(context)

        if len(servers) == 0:
            LOG.critical('No servers configured. Please create at least one '
                         'server')
            raise exceptions.NoServersConfigured()

        # Set the serial number
        values['serial'] = utils.increment_serial()

        domain = self.storage.create_domain(context, values)

        try:
            self.backend.create_domain(context, domain)
        except exceptions.Backend:
            # Re-raise Backend exceptions as is..
            raise
        except Exception, e:
            raise exceptions.Backend('Unknown backend failure: %s' % e)

        utils.notify(context, 'api', 'domain.create', domain)

        return domain

    def get_domains(self, context, criterion=None):
        target = {'tenant_id': context.tenant_id}
        policy.check('get_domains', context, target)

        if criterion is None:
            criterion = {}

        if not context.is_admin:
            criterion['tenant_id'] = context.tenant_id

        return self.storage.get_domains(context, criterion)

    def get_domain(self, context, domain_id):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }
        policy.check('get_domain', context, target)

        return domain

    def update_domain(self, context, domain_id, values):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('update_domain', context, target)

        if 'tenant_id' in values:
            # NOTE(kiall): Ensure the user is allowed to delete a domain from
            #              the original tenant.
            policy.check('delete_domain', context, target)

            # NOTE(kiall): Ensure the user is allowed to create a domain in
            #              the new tenant.
            target = {'domain_id': domain_id, 'tenant_id': values['tenant_id']}
            policy.check('create_domain', context, target)

        if 'name' in values and values['name'] != domain['name']:
            raise exceptions.BadRequest('Renaming a domain is not allowed')

        # Increment the serial number
        values['serial'] = utils.increment_serial(domain['serial'])

        domain = self.storage.update_domain(context, domain_id, values)

        try:
            self.backend.update_domain(context, domain)
        except exceptions.Backend:
            # Re-raise Backend exceptions as is..
            raise
        except Exception, e:
            raise exceptions.Backend('Unknown backend failure: %s' % e)

        utils.notify(context, 'api', 'domain.update', domain)

        return domain

    def delete_domain(self, context, domain_id):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('delete_domain', context, target)

        try:
            self.backend.delete_domain(context, domain)
        except exceptions.Backend:
            # Re-raise Backend exceptions as is..
            raise
        except Exception, e:
            raise exceptions.Backend('Unknown backend failure: %s' % e)

        utils.notify(context, 'api', 'domain.delete', domain)

        return self.storage.delete_domain(context, domain_id)

    def get_domain_servers(self, context, domain_id, criterion=None):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('get_domain_servers', context, target)

        if criterion is None:
            criterion = {}

        # TODO: Once we allow domains to be allocated on 1 of N server
        #       pools, return the filtered list here.
        return self.storage.get_servers(context, criterion)

    # Record Methods
    def create_record(self, context, domain_id, values):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'record_name': values['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('create_record', context, target)

        # Ensure the record name is valid
        self._is_valid_record_name(context, domain, values['name'],
                                   values['type'])

        record = self.storage.create_record(context, domain_id, values)

        try:
            self.backend.create_record(context, domain, record)
        except exceptions.Backend:
            # Re-raise Backend exceptions as is..
            raise
        except Exception, e:
            raise exceptions.Backend('Unknown backend failure: %s' % e)

        # Increment the domains serial number
        domain_values = {
            'serial': utils.increment_serial(domain['serial'])
        }
        self.storage.update_domain(context, domain_id, domain_values)

        # Send Record creation notification
        utils.notify(context, 'api', 'record.create', record)

        return record

    def get_records(self, context, domain_id, criterion=None):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('get_records', context, target)

        return self.storage.get_records(context, domain_id, criterion)

    def get_record(self, context, domain_id, record_id):
        domain = self.storage.get_domain(context, domain_id)
        record = self.storage.get_record(context, record_id)

        # Ensure the domain_id matches the record's domain_id
        if domain['id'] != record['domain_id']:
            raise exceptions.RecordNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'record_id': record['id'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('get_record', context, target)

        return record

    def update_record(self, context, domain_id, record_id, values):
        domain = self.storage.get_domain(context, domain_id)
        record = self.storage.get_record(context, record_id)

        # Ensure the domain_id matches the record's domain_id
        if domain['id'] != record['domain_id']:
            raise exceptions.RecordNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'record_id': record['id'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('update_record', context, target)

        # Ensure the record name is valid
        record_name = values['name'] if 'name' in values else record['name']
        record_type = values['type'] if 'type' in values else record['type']

        self._is_valid_record_name(context, domain, record_name, record_type)

        # Update the record
        record = self.storage.update_record(context, record_id, values)

        try:
            self.backend.update_record(context, domain, record)
        except exceptions.Backend:
            # Re-raise Backend exceptions as is..
            raise
        except Exception, e:
            raise exceptions.Backend('Unknown backend failure: %s' % e)

        # Increment the domains serial number
        domain_values = {
            'serial': utils.increment_serial(domain['serial'])
        }
        self.storage.update_domain(context, domain_id, domain_values)

        # Send Record update notification
        utils.notify(context, 'api', 'record.update', record)

        return record

    def delete_record(self, context, domain_id, record_id):
        domain = self.storage.get_domain(context, domain_id)
        record = self.storage.get_record(context, record_id)

        # Ensure the domain_id matches the record's domain_id
        if domain['id'] != record['domain_id']:
            raise exceptions.RecordNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'record_id': record['id'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('delete_record', context, target)

        try:
            self.backend.delete_record(context, domain, record)
        except exceptions.Backend:
            # Re-raise Backend exceptions as is..
            raise
        except Exception, e:
            raise exceptions.Backend('Unknown backend failure: %s' % e)

        # Increment the domains serial number
        domain_values = {
            'serial': utils.increment_serial(domain['serial'])
        }
        self.storage.update_domain(context, domain_id, domain_values)

        # Send Record deletion notification
        utils.notify(context, 'api', 'record.delete', record)

        return self.storage.delete_record(context, record_id)

    # Diagnostics Methods
    def sync_domains(self, context):
        policy.check('diagnostics_sync_domains', context)

        domains = self.storage.get_domains(context)
        results = {}

        for domain in domains:
            servers = self.storage.get_servers(context)
            records = self.storage.get_records(context, domain['id'])

            results[domain['id']] = self.backend.sync_domain(context,
                                                             domain,
                                                             records,
                                                             servers)

        return results

    def sync_domain(self, context, domain_id):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('diagnostics_sync_domain', context, target)

        records = self.storage.get_records(context, domain_id)

        return self.backend.sync_domain(context, domain, records)

    def sync_record(self, context, domain_id, record_id):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'record_id': record_id,
            'tenant_id': domain['tenant_id']
        }

        policy.check('diagnostics_sync_record', context, target)

        record = self.storage.get_record(context, record_id)

        return self.backend.sync_record(context, domain, record)

    def ping(self, context):
        policy.check('diagnostics_ping', context)

        try:
            backend_status = self.backend.ping(context)
        except Exception, e:
            backend_status = {'status': False, 'message': str(e)}

        try:
            storage_status = self.storage.ping(context)
        except Exception, e:
            storage_status = {'status': False, 'message': str(e)}

        if backend_status and storage_status:
            status = True
        else:
            status = False

        return {
            'host': cfg.CONF.host,
            'status': status,
            'backend': backend_status,
            'storage': storage_status
        }

# Copyright 2012 Managed I.T.
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
import contextlib
from oslo.config import cfg
from designate.central import effectivetld
from designate.openstack.common import log as logging
from designate.openstack.common.rpc import service as rpc_service
from designate import backend
from designate import exceptions
from designate import notifier
from designate import policy
from designate import quota
from designate import utils
from designate.storage import api as storage_api

LOG = logging.getLogger(__name__)


@contextlib.contextmanager
def wrap_backend_call():
    """
    Wraps backend calls, ensuring any exception raised is a Backend exception.
    """
    try:
        yield
    except exceptions.Backend as exc:
        raise
    except Exception as exc:
        raise exceptions.Backend('Unknown backend failure: %r' % exc)


class Service(rpc_service.Service):
    RPC_API_VERSION = '2.1'

    def __init__(self, *args, **kwargs):
        backend_driver = cfg.CONF['service:central'].backend_driver
        self.backend = backend.get_backend(backend_driver, self)

        kwargs.update(
            host=cfg.CONF.host,
            topic=cfg.CONF.central_topic,
        )

        self.notifier = notifier.get_notifier('central')

        policy.init_policy()

        super(Service, self).__init__(*args, **kwargs)

        # Get a storage connection
        self.storage_api = storage_api.StorageAPI()

        # Get a quota manager instance
        self.quota = quota.get_quota()
        self.effective_tld = effectivetld.EffectiveTld()

    def start(self):
        self.backend.start()

        super(Service, self).start()

    def wait(self):
        super(Service, self).wait()
        self.conn.consumer_thread.wait()

    def stop(self):
        super(Service, self).stop()

        self.backend.stop()

    def _is_valid_domain_name(self, context, domain_name):
        # Validate domain name length
        if len(domain_name) > cfg.CONF['service:central'].max_domain_name_len:
            raise exceptions.InvalidDomainName('Name too long')

        # Break the domain name up into its component labels
        domain_labels = domain_name.strip('.').split('.')

        # We need more than 1 label.
        if len(domain_labels) <= 1:
            raise exceptions.InvalidDomainName('More than one label is '
                                               'required')
        # Check the TLD for validity
        # We cannot use the effective TLD list as the publicsuffix.org list is
        # missing some top level entries.  At the time of coding, the following
        # entries were missing
        # arpa, au, bv, gb, gn, kp, lb, lr, sj, tp, tz, xn--80ao21a, xn--l1acc
        # xn--mgbx4cd0ab
        if self.effective_tld.accepted_tld_list:
            domain_tld = domain_labels[-1].lower()
            if domain_tld not in self.effective_tld.accepted_tld_list:
                raise exceptions.InvalidTLD('Unknown or invalid TLD')

        # Check if the domain_name is the same as an effective TLD.
        if self.effective_tld.is_effective_tld(domain_name):
            raise exceptions.DomainIsSameAsAnEffectiveTLD(
                'Domain name cannot be the same as an effective TLD')

        # Check domain name blacklist
        if self._is_blacklisted_domain_name(context, domain_name):
            # Some users are allowed bypass the blacklist.. Is this one?
            if not policy.check('use_blacklisted_domain', context, exc=None):
                raise exceptions.InvalidDomainName('Blacklisted domain name')

        return True

    def _is_valid_record_name(self, context, domain, record_name, record_type):
        if not record_name.endswith('.'):
            raise ValueError('Please supply a FQDN')

        # Validate record name length
        if len(record_name) > cfg.CONF['service:central'].max_record_name_len:
            raise exceptions.InvalidRecordName('Name too long')

        # Record must be contained in the parent zone
        if not record_name.endswith(domain['name']):
            raise exceptions.InvalidRecordLocation('Record is not contained '
                                                   'within it\'s parent '
                                                   'domain')

        # CNAME's must not be created at the zone apex.
        if record_type == 'CNAME' and record_name == domain['name']:
            raise exceptions.InvalidRecordLocation('CNAME records may not be '
                                                   'created at the zone apex')

    def _is_valid_record_placement(self, context, domain, record_name,
                                   record_type, record_id=None):
        # CNAME's must not share a name with other records
        criterion = {
            'name': record_name,
            'domain_id': domain['id']
        }

        if record_type != 'CNAME':
            criterion['type'] = 'CNAME'

        records = self.storage_api.find_records(context, criterion=criterion)
        if ((len(records) == 1 and records[0]['id'] != record_id)
                or len(records) > 1):
            raise exceptions.InvalidRecordLocation('CNAME records may not '
                                                   'share a name with any '
                                                   'other records')

        # Duplicate PTR's with the same name are not allowed
        if record_type == 'PTR':
            criterion = {
                'name': record_name,
                'type': 'PTR',
                'domain_id': domain['id']}
            records = self.storage_api.find_records(context,
                                                    criterion=criterion)
            if ((len(records) == 1 and records[0]['id'] != record_id)
                    or len(records) > 1):
                raise exceptions.DuplicateRecord()

        return True

    def _is_blacklisted_domain_name(self, context, domain_name):
        """
        Ensures the provided domain_name is not blacklisted.
        """
        blacklists = cfg.CONF['service:central'].domain_name_blacklist

        for blacklist in blacklists:
            if bool(re.search(blacklist, domain_name)):
                return blacklist

        return False

    def _is_subdomain(self, context, domain_name):
        # Break the name up into it's component labels
        labels = domain_name.split(".")

        i = 1

        # Starting with label #2, search for matching domain's in the database
        while (i < len(labels)):
            name = '.'.join(labels[i:])

            try:
                domain = self.storage_api.find_domain(context, {'name': name})
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

        criterion['domain_id'] = domain['id']

        # Starting with label #2, search for matching records's in the database
        while (i <= j):
            criterion['name'] = '.'.join(record_labels[i:])

            records = self.storage_api.find_records(context, criterion)

            if len(records) == 0:
                i += 1
            else:
                return records

        return False

    def _increment_domain_serial(self, context, domain_id):
        domain = self.storage_api.get_domain(context, domain_id)

        # Increment the serial number
        values = {'serial': utils.increment_serial(domain['serial'])}

        with self.storage_api.update_domain(
                context, domain_id, values) as domain:
            with wrap_backend_call():
                self.backend.update_domain(context, domain)

        return domain

    # Quota Enforcement Methods
    def _enforce_domain_quota(self, context, tenant_id):
        criterion = {'tenant_id': tenant_id}
        count = self.storage_api.count_domains(context, criterion)

        self.quota.limit_check(context, tenant_id, domains=count)

    def _enforce_record_quota(self, context, domain):
        # Ensure the records per domain quota is OK
        criterion = {'domain_id': domain['id']}
        count = self.storage_api.count_records(context, criterion)

        self.quota.limit_check(context, domain['tenant_id'],
                               domain_records=count)

    # Misc Methods
    def get_absolute_limits(self, context):
        # NOTE(Kiall): Currently, we only have quota based limits..
        return self.quota.get_quotas(context, context.tenant_id)

    # Quota Methods
    def get_quotas(self, context, tenant_id):
        target = {'tenant_id': tenant_id}
        policy.check('get_quotas', context, target)

        return self.quota.get_quotas(context, tenant_id)

    def get_quota(self, context, tenant_id, resource):
        target = {'tenant_id': tenant_id, 'resource': resource}
        policy.check('get_quota', context, target)

        return self.quota.get_quota(context, tenant_id, resource)

    def set_quota(self, context, tenant_id, resource, hard_limit):
        target = {
            'tenant_id': tenant_id,
            'resource': resource,
            'hard_limit': hard_limit,
        }

        policy.check('set_quota', context, target)

        return self.quota.set_quota(context, tenant_id, resource, hard_limit)

    def reset_quotas(self, context, tenant_id):
        target = {'tenant_id': tenant_id}
        policy.check('reset_quotas', context, target)

        self.quota.reset_quotas(context, tenant_id)

    # Server Methods
    def create_server(self, context, values):
        policy.check('create_server', context)

        with self.storage_api.create_server(context, values) as server:
            # Update backend with the new server..
            with wrap_backend_call():
                self.backend.create_server(context, server)

        self.notifier.info(context, 'dns.server.create', server)

        return server

    def find_servers(self, context, criterion=None):
        policy.check('find_servers', context)

        return self.storage_api.find_servers(context, criterion)

    def get_server(self, context, server_id):
        policy.check('get_server', context, {'server_id': server_id})

        return self.storage_api.get_server(context, server_id)

    def update_server(self, context, server_id, values):
        policy.check('update_server', context, {'server_id': server_id})

        with self.storage_api.update_server(
                context, server_id, values) as server:
            # Update backend with the new details..
            with wrap_backend_call():
                self.backend.update_server(context, server)

        self.notifier.info(context, 'dns.server.update', server)

        return server

    def delete_server(self, context, server_id):
        policy.check('delete_server', context, {'server_id': server_id})

        # don't delete last of servers
        servers = self.storage_api.find_servers(context)
        if len(servers) == 1 and server_id == servers[0]['id']:
            raise exceptions.LastServerDeleteNotAllowed(
                "Not allowed to delete last of servers")

        with self.storage_api.delete_server(context, server_id) as server:
            # Update backend with the new server..
            with wrap_backend_call():
                self.backend.delete_server(context, server)

        self.notifier.info(context, 'dns.server.delete', server)

    # TSIG Key Methods
    def create_tsigkey(self, context, values):
        policy.check('create_tsigkey', context)

        with self.storage_api.create_tsigkey(context, values) as tsigkey:
            with wrap_backend_call():
                self.backend.create_tsigkey(context, tsigkey)

        self.notifier.info(context, 'dns.tsigkey.create', tsigkey)

        return tsigkey

    def find_tsigkeys(self, context, criterion=None):
        policy.check('find_tsigkeys', context)

        return self.storage_api.find_tsigkeys(context, criterion)

    def get_tsigkey(self, context, tsigkey_id):
        policy.check('get_tsigkey', context, {'tsigkey_id': tsigkey_id})

        return self.storage_api.get_tsigkey(context, tsigkey_id)

    def update_tsigkey(self, context, tsigkey_id, values):
        policy.check('update_tsigkey', context, {'tsigkey_id': tsigkey_id})

        with self.storage_api.update_tsigkey(
                context, tsigkey_id, values) as tsigkey:
            with wrap_backend_call():
                self.backend.update_tsigkey(context, tsigkey)

        self.notifier.info(context, 'dns.tsigkey.update', tsigkey)

        return tsigkey

    def delete_tsigkey(self, context, tsigkey_id):
        policy.check('delete_tsigkey', context, {'tsigkey_id': tsigkey_id})

        with self.storage_api.delete_tsigkey(context, tsigkey_id) as tsigkey:
            with wrap_backend_call():
                self.backend.delete_tsigkey(context, tsigkey)

        self.notifier.info(context, 'dns.tsigkey.delete', tsigkey)

    # Tenant Methods
    def find_tenants(self, context):
        policy.check('find_tenants', context)
        return self.storage_api.find_tenants(context)

    def get_tenant(self, context, tenant_id):
        target = {
            'tenant_id': tenant_id
        }

        policy.check('get_tenant', context, target)

        return self.storage_api.get_tenant(context, tenant_id)

    def count_tenants(self, context):
        policy.check('count_tenants', context)
        return self.storage_api.count_tenants(context)

    # Domain Methods
    def create_domain(self, context, values):
        # TODO(kiall): Refactor this method into *MUCH* smaller chunks.
        values['tenant_id'] = context.tenant_id

        target = {
            'tenant_id': values['tenant_id'],
            'domain_name': values['name']
        }

        policy.check('create_domain', context, target)

        # Ensure the tenant has enough quota to continue
        self._enforce_domain_quota(context, values['tenant_id'])

        # Ensure the domain name is valid
        self._is_valid_domain_name(context, values['name'])

        # Handle sub-domains appropriately
        parent_domain = self._is_subdomain(context, values['name'])

        if parent_domain:
            if parent_domain['tenant_id'] == values['tenant_id']:
                # Record the Parent Domain ID
                values['parent_domain_id'] = parent_domain['id']
            else:
                raise exceptions.Forbidden('Unable to create subdomain in '
                                           'another tenants domain')

        # TODO(kiall): Handle super-domains properly

        # NOTE(kiall): Fetch the servers before creating the domain, this way
        #              we can prevent domain creation if no servers are
        #              configured.
        servers = self.storage_api.find_servers(context)

        if len(servers) == 0:
            LOG.critical('No servers configured. Please create at least one '
                         'server')
            raise exceptions.NoServersConfigured()

        # Set the serial number
        values['serial'] = utils.increment_serial()

        with self.storage_api.create_domain(context, values) as domain:
            with wrap_backend_call():
                self.backend.create_domain(context, domain)

        self.notifier.info(context, 'dns.domain.create', domain)

        return domain

    def get_domain(self, context, domain_id):
        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }
        policy.check('get_domain', context, target)

        return domain

    def get_domain_servers(self, context, domain_id, criterion=None):
        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('get_domain_servers', context, target)

        # TODO(kiall): Once we allow domains to be allocated on 1 of N server
        #              pools, return the filtered list here.
        return self.storage_api.find_servers(context, criterion)

    def find_domains(self, context, criterion=None):
        target = {'tenant_id': context.tenant_id}
        policy.check('find_domains', context, target)

        if criterion is None:
            criterion = {}

        if not context.is_admin:
            criterion['tenant_id'] = context.tenant_id

        return self.storage_api.find_domains(context, criterion)

    def find_domain(self, context, criterion):
        target = {'tenant_id': context.tenant_id}
        policy.check('find_domain', context, target)

        if not context.is_admin:
            criterion['tenant_id'] = context.tenant_id

        return self.storage_api.find_domain(context, criterion)

    def update_domain(self, context, domain_id, values, increment_serial=True):
        # TODO(kiall): Refactor this method into *MUCH* smaller chunks.
        domain = self.storage_api.get_domain(context, domain_id)

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

        if increment_serial:
            # Increment the serial number
            values['serial'] = utils.increment_serial(domain['serial'])

        with self.storage_api.update_domain(
                context, domain_id, values) as domain:
            with wrap_backend_call():
                self.backend.update_domain(context, domain)

        self.notifier.info(context, 'dns.domain.update', domain)

        return domain

    def delete_domain(self, context, domain_id):
        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('delete_domain', context, target)

        # Prevent deletion of a zone which has child zones
        criterion = {'parent_domain_id': domain_id}

        if self.storage_api.count_domains(context, criterion) > 0:
            raise exceptions.DomainHasSubdomain('Please delete any subdomains '
                                                'before deleting this domain')

        with self.storage_api.delete_domain(context, domain_id) as domain:
            with wrap_backend_call():
                self.backend.delete_domain(context, domain)

        self.notifier.info(context, 'dns.domain.delete', domain)

        return domain

    def count_domains(self, context, criterion=None):
        if criterion is None:
            criterion = {}

        target = {
            'tenant_id': criterion.get('tenant_id', None)
        }

        policy.check('count_domains', context, target)

        return self.storage_api.count_domains(context, criterion)

    def touch_domain(self, context, domain_id):
        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('touch_domain', context, target)

        domain = self._increment_domain_serial(context, domain_id)

        self.notifier.info(context, 'dns.domain.touch', domain)

        return domain

    # Record Methods
    def create_record(self, context, domain_id, values, increment_serial=True):
        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'record_name': values['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('create_record', context, target)

        # Ensure the tenant has enough quota to continue
        self._enforce_record_quota(context, domain)

        # Ensure the record name and placement is valid
        self._is_valid_record_name(context, domain, values['name'],
                                   values['type'])
        self._is_valid_record_placement(context, domain, values['name'],
                                        values['type'])

        with self.storage_api.create_record(
                context, domain_id, values) as record:
            with wrap_backend_call():
                self.backend.create_record(context, domain, record)

            if increment_serial:
                self._increment_domain_serial(context, domain_id)

        # Send Record creation notification
        self.notifier.info(context, 'dns.record.create', record)

        return record

    def get_record(self, context, domain_id, record_id):
        domain = self.storage_api.get_domain(context, domain_id)
        record = self.storage_api.get_record(context, record_id)

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

    def find_records(self, context, domain_id, criterion=None):
        if criterion is None:
            criterion = {}

        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('find_records', context, target)

        criterion['domain_id'] = domain_id

        return self.storage_api.find_records(context, criterion)

    def find_record(self, context, domain_id, criterion=None):
        if criterion is None:
            criterion = {}

        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('find_record', context, target)

        criterion['domain_id'] = domain_id

        return self.storage_api.find_record(context, criterion)

    def update_record(self, context, domain_id, record_id, values,
                      increment_serial=True):
        domain = self.storage_api.get_domain(context, domain_id)
        record = self.storage_api.get_record(context, record_id)

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
        self._is_valid_record_placement(context, domain, record_name,
                                        record_type, record_id)

        # Update the record
        with self.storage_api.update_record(
                context, record_id, values) as record:
            with wrap_backend_call():
                self.backend.update_record(context, domain, record)

            if increment_serial:
                self._increment_domain_serial(context, domain_id)

        # Send Record update notification
        self.notifier.info(context, 'dns.record.update', record)

        return record

    def delete_record(self, context, domain_id, record_id,
                      increment_serial=True):
        domain = self.storage_api.get_domain(context, domain_id)
        record = self.storage_api.get_record(context, record_id)

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

        with self.storage_api.delete_record(context, record_id) as record:
            with wrap_backend_call():
                self.backend.delete_record(context, domain, record)

            if increment_serial:
                self._increment_domain_serial(context, domain_id)

        # Send Record deletion notification
        self.notifier.info(context, 'dns.record.delete', record)

        return record

    def count_records(self, context, criterion=None):
        if criterion is None:
            criterion = {}

        target = {
            'tenant_id': criterion.get('tenant_id', None)
        }

        policy.check('count_records', context, target)
        return self.storage_api.count_records(context, criterion)

    # Diagnostics Methods
    def sync_domains(self, context):
        policy.check('diagnostics_sync_domains', context)

        domains = self.storage_api.find_domains(context)
        results = {}

        for domain in domains:
            servers = self.storage_api.find_servers(context)
            criterion = {'domain_id': domain['id']}
            records = self.storage_api.find_records(
                context, criterion=criterion)

            with wrap_backend_call():
                results[domain['id']] = self.backend.sync_domain(context,
                                                                 domain,
                                                                 records,
                                                                 servers)

        return results

    def sync_domain(self, context, domain_id):
        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('diagnostics_sync_domain', context, target)

        records = self.storage_api.find_records(
            context, criterion={'domain_id': domain_id})

        with wrap_backend_call():
            return self.backend.sync_domain(context, domain, records)

    def sync_record(self, context, domain_id, record_id):
        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'record_id': record_id,
            'tenant_id': domain['tenant_id']
        }

        policy.check('diagnostics_sync_record', context, target)

        record = self.storage_api.get_record(context, record_id)

        with wrap_backend_call():
            return self.backend.sync_record(context, domain, record)

    def ping(self, context):
        policy.check('diagnostics_ping', context)

        try:
            backend_status = self.backend.ping(context)
        except Exception as e:
            backend_status = {'status': False, 'message': str(e)}

        try:
            storage_status = self.storage_api.ping(context)
        except Exception as e:
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

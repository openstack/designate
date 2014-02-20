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
from designate.openstack.common import log as logging
from designate.openstack.common.rpc import service as rpc_service
from designate.openstack.common.notifier import proxy as notifier
from designate import backend
from designate import exceptions
from designate import policy
from designate import quota
from designate import utils
from designate.storage import api as storage_api
from designate import network_api

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
    RPC_API_VERSION = '3.3'

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

        self.network_api = network_api.get_network_api(cfg.CONF.network_api)

    def start(self):
        # Check to see if there are any TLDs in the database
        tlds = self.storage_api.find_tlds({})
        if tlds:
            self.check_for_tlds = True
            LOG.info("Checking for TLDs")
        else:
            self.check_for_tlds = False
            LOG.info("NOT checking for TLDs")

        self.backend.start()

        super(Service, self).start()

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

        # Check the TLD for validity if there are entries in the database
        if self.check_for_tlds:
            try:
                self.storage_api.find_tld(context, {'name': domain_labels[-1]})
            except exceptions.TLDNotFound:
                raise exceptions.InvalidDomainName('Invalid TLD')

            # Now check that the domain name is not the same as a TLD
            try:
                stripped_domain_name = domain_name.strip('.').lower()
                self.storage_api.find_tld(
                    context,
                    {'name': stripped_domain_name})
            except exceptions.TLDNotFound:
                pass
            else:
                raise exceptions.InvalidDomainName(
                    'Domain name cannot be the same as a TLD')

        # Check domain name blacklist
        if self._is_blacklisted_domain_name(context, domain_name):
            # Some users are allowed bypass the blacklist.. Is this one?
            if not policy.check('use_blacklisted_domain', context, exc=None):
                raise exceptions.InvalidDomainName('Blacklisted domain name')

        return True

    def _is_valid_recordset_name(self, context, domain, recordset_name):
        if not recordset_name.endswith('.'):
            raise ValueError('Please supply a FQDN')

        # Validate record name length
        max_len = cfg.CONF['service:central'].max_recordset_name_len
        if len(recordset_name) > max_len:
            raise exceptions.InvalidRecordSetName('Name too long')

        # RecordSets must be contained in the parent zone
        if not recordset_name.endswith(domain['name']):
            raise exceptions.InvalidRecordSetLocation(
                'RecordSet is not contained within it\'s parent domain')

    def _is_valid_recordset_placement(self, context, domain, recordset_name,
                                      recordset_type, recordset_id=None):
        # CNAME's must not be created at the zone apex.
        if recordset_type == 'CNAME' and recordset_name == domain['name']:
            raise exceptions.InvalidRecordSetLocation(
                'CNAME recordsets may not be created at the zone apex')

        # CNAME's must not share a name with other recordsets
        criterion = {
            'domain_id': domain['id'],
            'name': recordset_name,
        }

        if recordset_type != 'CNAME':
            criterion['type'] = 'CNAME'

        recordsets = self.storage_api.find_recordsets(context, criterion)

        if ((len(recordsets) == 1 and recordsets[0]['id'] != recordset_id)
                or len(recordsets) > 1):
            raise exceptions.InvalidRecordSetLocation(
                'CNAME recordsets may not share a name with any other records')

        return True

    def _is_valid_recordset_placement_subdomain(self, context, domain,
                                                recordset_name,
                                                criterion=None):
        """
        Check that the placement of the requested rrset belongs to any of the
        domains subdomains..
        """
        LOG.debug("Checking if %s belongs in any of %s subdomains",
                  recordset_name, domain['name'])

        criterion = criterion or {}

        context = context.elevated()
        context.all_tenants = True

        if domain['name'] == recordset_name:
            return

        child_domains = self.storage_api.find_domains(
            context, {"parent_domain_id": domain['id']})
        for child_domain in child_domains:
            try:
                self._is_valid_recordset_name(
                    context, child_domain, recordset_name)
            except Exception:
                continue
            else:
                msg = 'RecordSet belongs in a child zone: %s' % \
                    child_domain['name']
                raise exceptions.InvalidRecordSetLocation(msg)

    def _is_blacklisted_domain_name(self, context, domain_name):
        """
        Ensures the provided domain_name is not blacklisted.
        """

        blacklists = self.storage_api.find_blacklists(context)

        for blacklist in blacklists:
            if bool(re.search(blacklist["pattern"], domain_name)):
                return True

        return False

    def _is_subdomain(self, context, domain_name):
        context = context.elevated()
        context.all_tenants = True

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

    def _enforce_recordset_quota(self, context, domain):
        # TODO(kiall): Enforce RRSet Quotas
        pass

    def _enforce_record_quota(self, context, domain, recordset):
        # Ensure the records per domain quota is OK
        criterion = {'domain_id': domain['id']}
        count = self.storage_api.count_records(context, criterion)

        self.quota.limit_check(context, domain['tenant_id'],
                               domain_records=count)

        # TODO(kiall): Enforce Records per RRSet Quotas

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

    def find_servers(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        policy.check('find_servers', context)

        return self.storage_api.find_servers(context, criterion, marker, limit,
                                             sort_key, sort_dir)

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

    # TLD Methods
    def create_tld(self, context, values):
        policy.check('create_tld', context)

        # The TLD is only created on central's storage and not on the backend.
        with self.storage_api.create_tld(context, values) as tld:
            pass
        self.notifier.info(context, 'dns.tld.create', tld)

        # Set check for tlds to be true
        self.check_for_tlds = True
        return tld

    def find_tlds(self, context, criterion=None, marker=None, limit=None,
                  sort_key=None, sort_dir=None):
        policy.check('find_tlds', context)

        return self.storage_api.find_tlds(context, criterion, marker, limit,
                                          sort_key, sort_dir)

    def get_tld(self, context, tld_id):
        policy.check('get_tld', context, {'tld_id': tld_id})

        return self.storage_api.get_tld(context, tld_id)

    def update_tld(self, context, tld_id, values):
        policy.check('update_tld', context, {'tld_id': tld_id})

        with self.storage_api.update_tld(context, tld_id, values) as tld:
            pass

        self.notifier.info(context, 'dns.tld.update', tld)

        return tld

    def delete_tld(self, context, tld_id):
        # Known issue - self.check_for_tld is not reset here.  So if the last
        # TLD happens to be deleted, then we would incorrectly do the TLD
        # validations.
        # This decision was influenced by weighing the (ultra low) probability
        # of hitting this issue vs doing the checks for every delete.
        policy.check('delete_tld', context, {'tld_id': tld_id})

        with self.storage_api.delete_tld(context, tld_id) as tld:
            pass

        self.notifier.info(context, 'dns.tld.delete', tld)

    # TSIG Key Methods
    def create_tsigkey(self, context, values):
        policy.check('create_tsigkey', context)

        with self.storage_api.create_tsigkey(context, values) as tsigkey:
            with wrap_backend_call():
                self.backend.create_tsigkey(context, tsigkey)

        self.notifier.info(context, 'dns.tsigkey.create', tsigkey)

        return tsigkey

    def find_tsigkeys(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        policy.check('find_tsigkeys', context)

        return self.storage_api.find_tsigkeys(context, criterion, marker,
                                              limit, sort_key, sort_dir)

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

        # Default to creating in the current users tenant
        if 'tenant_id' not in values:
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

    def find_domains(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        target = {'tenant_id': context.tenant_id}
        policy.check('find_domains', context, target)

        return self.storage_api.find_domains(context, criterion, marker, limit,
                                             sort_key, sort_dir)

    def find_domain(self, context, criterion=None):
        target = {'tenant_id': context.tenant_id}
        policy.check('find_domain', context, target)

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

    # RecordSet Methods
    def create_recordset(self, context, domain_id, values):
        domain = self.storage_api.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'recordset_name': values['name'],
            'tenant_id': domain['tenant_id'],
        }

        policy.check('create_recordset', context, target)

        # Ensure the tenant has enough quota to continue
        self._enforce_recordset_quota(context, domain)

        # Ensure the recordset name and placement is valid
        self._is_valid_recordset_name(context, domain, values['name'])
        self._is_valid_recordset_placement(context, domain, values['name'],
                                           values['type'])
        self._is_valid_recordset_placement_subdomain(
            context, domain, values['name'])

        with self.storage_api.create_recordset(
                context, domain_id, values) as recordset:
            with wrap_backend_call():
                self.backend.create_recordset(context, domain, recordset)

        # Send RecordSet creation notification
        self.notifier.info(context, 'dns.recordset.create', recordset)

        return recordset

    def get_recordset(self, context, domain_id, recordset_id):
        domain = self.storage_api.get_domain(context, domain_id)
        recordset = self.storage_api.get_recordset(context, recordset_id)

        # Ensure the domain_id matches the record's domain_id
        if domain['id'] != recordset['domain_id']:
            raise exceptions.RecordSetNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'recordset_id': recordset['id'],
            'tenant_id': domain['tenant_id'],
        }

        policy.check('get_recordset', context, target)

        return recordset

    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        target = {'tenant_id': context.tenant_id}
        policy.check('find_recordsets', context, target)

        return self.storage_api.find_recordsets(context, criterion, marker,
                                                limit, sort_key, sort_dir)

    def find_recordset(self, context, criterion=None):
        target = {'tenant_id': context.tenant_id}
        policy.check('find_recordset', context, target)

        return self.storage_api.find_recordset(context, criterion)

    def update_recordset(self, context, domain_id, recordset_id, values,
                         increment_serial=True):
        domain = self.storage_api.get_domain(context, domain_id)
        recordset = self.storage_api.get_recordset(context, recordset_id)

        # Ensure the domain_id matches the recordset's domain_id
        if domain['id'] != recordset['domain_id']:
            raise exceptions.RecordSetNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'recordset_id': recordset['id'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('update_recordset', context, target)

        # Ensure the record name is valid
        recordset_name = values['name'] if 'name' in values \
            else recordset['name']
        recordset_type = values['type'] if 'type' in values \
            else recordset['type']

        self._is_valid_recordset_name(context, domain, recordset_name)
        self._is_valid_recordset_placement(context, domain, recordset_name,
                                           recordset_type, recordset_id)
        self._is_valid_recordset_placement_subdomain(
            context, domain, recordset_name)

        # Update the recordset
        with self.storage_api.update_recordset(
                context, recordset_id, values) as recordset:
            with wrap_backend_call():
                self.backend.update_recordset(context, domain, recordset)

            if increment_serial:
                self._increment_domain_serial(context, domain_id)

        # Send RecordSet update notification
        self.notifier.info(context, 'dns.recordset.update', recordset)

        return recordset

    def delete_recordset(self, context, domain_id, recordset_id,
                         increment_serial=True):
        domain = self.storage_api.get_domain(context, domain_id)
        recordset = self.storage_api.get_recordset(context, recordset_id)

        # Ensure the domain_id matches the recordset's domain_id
        if domain['id'] != recordset['domain_id']:
            raise exceptions.RecordSetNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'recordset_id': recordset['id'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('delete_recordset', context, target)

        with self.storage_api.delete_recordset(context, recordset_id) \
                as recordset:
            with wrap_backend_call():
                self.backend.delete_recordset(context, domain, recordset)

            if increment_serial:
                self._increment_domain_serial(context, domain_id)

        # Send Record deletion notification
        self.notifier.info(context, 'dns.recordset.delete', recordset)

        return recordset

    def count_recordsets(self, context, criterion=None):
        if criterion is None:
            criterion = {}

        target = {
            'tenant_id': criterion.get('tenant_id', None)
        }

        policy.check('count_recordsets', context, target)

        return self.storage_api.count_recordsets(context, criterion)

    # Record Methods
    def create_record(self, context, domain_id, recordset_id, values,
                      increment_serial=True):
        domain = self.storage_api.get_domain(context, domain_id)
        recordset = self.storage_api.get_recordset(context, recordset_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'recordset_id': recordset_id,
            'recordset_name': recordset['name'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('create_record', context, target)

        # Ensure the tenant has enough quota to continue
        self._enforce_record_quota(context, domain, recordset)

        with self.storage_api.create_record(
                context, domain_id, recordset_id, values) as record:
            with wrap_backend_call():
                self.backend.create_record(context, domain, recordset, record)

            if increment_serial:
                self._increment_domain_serial(context, domain_id)

        # Send Record creation notification
        self.notifier.info(context, 'dns.record.create', record)

        return record

    def get_record(self, context, domain_id, recordset_id, record_id):
        domain = self.storage_api.get_domain(context, domain_id)
        recordset = self.storage_api.get_recordset(context, recordset_id)
        record = self.storage_api.get_record(context, record_id)

        # Ensure the domain_id matches the record's domain_id
        if domain['id'] != record['domain_id']:
            raise exceptions.RecordNotFound()

        # Ensure the recordset_id matches the record's recordset_id
        if recordset['id'] != record['recordset_id']:
            raise exceptions.RecordNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'recordset_id': recordset_id,
            'recordset_name': recordset['name'],
            'record_id': record['id'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('get_record', context, target)

        return record

    def find_records(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        target = {'tenant_id': context.tenant_id}
        policy.check('find_records', context, target)

        return self.storage_api.find_records(context, criterion, marker, limit,
                                             sort_key, sort_dir)

    def find_record(self, context, criterion=None):
        target = {'tenant_id': context.tenant_id}
        policy.check('find_record', context, target)

        return self.storage_api.find_record(context, criterion)

    def update_record(self, context, domain_id, recordset_id, record_id,
                      values, increment_serial=True):
        domain = self.storage_api.get_domain(context, domain_id)
        recordset = self.storage_api.get_recordset(context, recordset_id)
        record = self.storage_api.get_record(context, record_id)

        # Ensure the domain_id matches the record's domain_id
        if domain['id'] != record['domain_id']:
            raise exceptions.RecordNotFound()

        # Ensure the recordset_id matches the record's recordset_id
        if recordset['id'] != record['recordset_id']:
            raise exceptions.RecordNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'recordset_id': recordset_id,
            'recordset_name': recordset['name'],
            'record_id': record['id'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('update_record', context, target)

        # Update the record
        with self.storage_api.update_record(
                context, record_id, values) as record:
            with wrap_backend_call():
                self.backend.update_record(context, domain, recordset, record)

            if increment_serial:
                self._increment_domain_serial(context, domain_id)

        # Send Record update notification
        self.notifier.info(context, 'dns.record.update', record)

        return record

    def delete_record(self, context, domain_id, recordset_id, record_id,
                      increment_serial=True):
        domain = self.storage_api.get_domain(context, domain_id)
        recordset = self.storage_api.get_recordset(context, recordset_id)
        record = self.storage_api.get_record(context, record_id)

        # Ensure the domain_id matches the record's domain_id
        if domain['id'] != record['domain_id']:
            raise exceptions.RecordNotFound()

        # Ensure the recordset_id matches the record's recordset_id
        if recordset['id'] != record['recordset_id']:
            raise exceptions.RecordNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'recordset_id': recordset_id,
            'recordset_name': recordset['name'],
            'record_id': record['id'],
            'tenant_id': domain['tenant_id']
        }

        policy.check('delete_record', context, target)

        with self.storage_api.delete_record(context, record_id) as record:
            with wrap_backend_call():
                self.backend.delete_record(context, domain, recordset, record)

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
            criterion = {'domain_id': domain['id']}
            records = self.storage_api.find_records(
                context, criterion=criterion)

            with wrap_backend_call():
                results[domain['id']] = self.backend.sync_domain(context,
                                                                 domain,
                                                                 records)

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

    def sync_record(self, context, domain_id, recordset_id, record_id):
        domain = self.storage_api.get_domain(context, domain_id)
        recordset = self.storage_api.get_recordset(context, recordset_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain['name'],
            'recordset_id': recordset_id,
            'recordset_name': recordset['name'],
            'record_id': record_id,
            'tenant_id': domain['tenant_id']
        }

        policy.check('diagnostics_sync_record', context, target)

        record = self.storage_api.get_record(context, record_id)

        with wrap_backend_call():
            return self.backend.sync_record(context, domain, recordset, record)

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

    def _determine_floatingips(self, context, fips, records=None,
                               tenant_id=None):
        """
        Given the context or tenant, records and fips it returns the valid
        floatingips either with a associated record or not. Deletes invalid
        records also.

        Returns a list of tuples with FloatingIPs and it's Record.
        """
        tenant_id = tenant_id or context.tenant_id

        elevated_context = context.elevated()
        elevated_context.all_tenants = True

        criterion = {
            'managed': True,
            'managed_resource_type': 'ptr:floatingip',
        }

        records = self.find_records(elevated_context, criterion)
        records = dict([(r['managed_extra'], r) for r in records])

        invalid = []
        data = {}
        # First populate the list of FIPS
        for fip_key, fip_values in fips.items():
            # Check if the FIP has a record
            record = records.get(fip_values['address'])

            # NOTE: Now check if it's owned by the tenant that actually has the
            # FIP in the external service and if not invalidate it (delete it)
            # thus not returning it with in the tuple with the FIP, but None..

            if record:
                record_tenant = record['managed_tenant_id']

                if record_tenant != tenant_id:
                    msg = "Invalid FloatingIP %s belongs to %s but record " \
                          "owner %s"
                    LOG.debug(msg, fip_key, tenant_id, record_tenant)

                    invalid.append(record)
                    record = None
            data[fip_key] = (fip_values, record)

        return data, invalid

    def _invalidate_floatingips(self, context, records):
        """
        Utility method to delete a list of records.
        """
        elevated_context = context.elevated()
        elevated_context.all_tenants = True

        if records > 0:
            for r in records:
                msg = 'Deleting record %s for FIP %s'
                LOG.debug(msg, r['id'], r['managed_resource_id'])
                self.delete_record(elevated_context, r['domain_id'],
                                   r['recordset_id'], r['id'])

    def _format_floatingips(self, context, data, recordsets=None):
        """
        Given a list of FloatingIP and Record tuples we look through creating
        a new dict of FloatingIPs
        """
        elevated_context = context.elevated()
        elevated_context.all_tenants = True

        fips = {}
        for key, value in data.items():
            fip_ptr = {
                'address': value[0]['address'],
                'id': value[0]['id'],
                'region': value[0]['region'],
                'ptrdname': None,
                'ttl': None,
                'description': None
            }

            # TTL population requires a present record in order to find the
            # RS or Zone
            if value[1]:
                # We can have a recordset dict passed in
                if (recordsets is not None and
                        value[1]['recordset_id'] in recordsets):
                    recordset = recordsets[value[1]['recordset_id']]
                else:
                    recordset = self.storage_api.get_recordset(
                        elevated_context, value[1]['recordset_id'])

                if recordset['ttl'] is not None:
                    fip_ptr['ttl'] = recordset['ttl']
                else:
                    zone = self.get_domain(
                        elevated_context, value[1]['domain_id'])
                    fip_ptr['ttl'] = zone['ttl']

                fip_ptr['ptrdname'] = value[1]['data']
            else:
                LOG.debug("No record information found for %s",
                          value[0]['id'])

            # Store the "fip_record" with the region and it's id as key
            fips[key] = fip_ptr
        return fips

    def _list_floatingips(self, context, region=None):
        data = self.network_api.list_floatingips(context, region=region)
        return self._list_to_dict(data, keys=['region', 'id'])

    def _list_to_dict(self, data, keys=['id']):
        new = {}
        for i in data:
            key = tuple([i[key] for key in keys])
            new[key] = i
        return new

    def _get_floatingip(self, context, region, floatingip_id, fips):
        if (region, floatingip_id) not in fips:
            msg = 'FloatingIP %s in %s is not associated for tenant "%s"' % \
                (floatingip_id, region, context.tenant_id)
            raise exceptions.NotFound(msg)
        return fips[region, floatingip_id]

    # PTR ops
    def list_floatingips(self, context):
        """
        List Floating IPs PTR

        A) We have service_catalog in the context and do a lookup using the
               token pr Neutron in the SC
        B) We lookup FIPs using the configured values for this deployment.
        """
        elevated_context = context.elevated()
        elevated_context.all_tenants = True

        tenant_fips = self._list_floatingips(context)

        valid, invalid = self._determine_floatingips(
            elevated_context, tenant_fips)

        self._invalidate_floatingips(context, invalid)

        return self._format_floatingips(context, valid).values()

    def get_floatingip(self, context, region, floatingip_id):
        """
        Get Floating IP PTR
        """
        elevated_context = context.elevated()
        elevated_context.all_tenants = True

        tenant_fips = self._list_floatingips(context, region=region)

        self._get_floatingip(context, region, floatingip_id, tenant_fips)

        valid, invalid = self._determine_floatingips(
            elevated_context, tenant_fips)

        self._invalidate_floatingips(context, invalid)

        mangled = self._format_floatingips(context, valid)
        return mangled[region, floatingip_id]

    def _set_floatingip_reverse(self, context, region, floatingip_id, values):
        """
        Set the FloatingIP's PTR record based on values.
        """
        values.setdefault('description', None)

        elevated_context = context.elevated()
        elevated_context.all_tenants = True

        tenant_fips = self._list_floatingips(context, region=region)

        fip = self._get_floatingip(context, region, floatingip_id, tenant_fips)

        zone_name = self.network_api.address_zone(fip['address'])

        # NOTE: Find existing zone or create it..
        try:
            zone = self.storage_api.find_domain(
                elevated_context, {'name': zone_name})
        except exceptions.DomainNotFound:
            msg = 'Creating zone for %s:%s - %s zone %s' % \
                (floatingip_id, region, fip['address'], zone_name)
            LOG.info(msg)

            email = cfg.CONF['service:central'].managed_resource_email
            tenant_id = cfg.CONF['service:central'].managed_resource_tenant_id

            zone_values = {
                'name': zone_name,
                'email': email,
                'tenant_id': tenant_id
            }

            zone = self.create_domain(elevated_context, zone_values)

        record_name = self.network_api.address_name(fip['address'])

        try:
            # NOTE: Delete the current recormdset if any (also purges records)
            LOG.debug("Removing old RRset / Record")
            rset = self.find_recordset(
                elevated_context, {'name': record_name, 'type': 'PTR'})

            records = self.find_records(
                elevated_context, {'recordset_id': rset['id']})

            for record in records:
                self.delete_record(
                    elevated_context,
                    rset['domain_id'],
                    rset['id'],
                    record['id'])
            self.delete_recordset(elevated_context, zone['id'], rset['id'])
        except exceptions.RecordSetNotFound:
            pass

        recordset_values = {
            'name': record_name,
            'type': 'PTR',
            'ttl': values.get('ttl', None)
        }

        recordset = self.create_recordset(
            elevated_context, zone['id'], recordset_values)

        record_values = {
            'data': values['ptrdname'],
            'description': values['description'],
            'type': 'PTR',
            'managed': True,
            'managed_extra': fip['address'],
            'managed_resource_id': floatingip_id,
            'managed_resource_region': region,
            'managed_resource_type': 'ptr:floatingip',
            'managed_tenant_id': context.tenant_id
        }

        record = self.create_record(
            elevated_context, zone['id'], recordset['id'], record_values)

        mangled = self._format_floatingips(
            context, {(region, floatingip_id): (fip, record)},
            {recordset['id']: recordset})

        return mangled[region, floatingip_id]

    def _unset_floatingip_reverse(self, context, region, floatingip_id):
        """
        Unset the FloatingIP PTR record based on the

        Service's FloatingIP ID > managed_resource_id
        Tenant ID > managed_tenant_id

        We find the record based on the criteria and delete it or raise.
        """
        elevated_context = context.elevated()
        elevated_context.all_tenants = True

        criterion = {
            'managed_resource_id': floatingip_id,
            'managed_tenant_id': context.tenant_id
        }

        try:
            record = self.storage_api.find_record(
                elevated_context, criterion=criterion)
        except exceptions.RecordNotFound:
            msg = 'No such FloatingIP %s:%s' % (region, floatingip_id)
            raise exceptions.NotFound(msg)

        self.delete_record(
            elevated_context,
            record['domain_id'],
            record['recordset_id'],
            record['id'])

    def update_floatingip(self, context, region, floatingip_id, values):
        """
        We strictly see if values['ptrdname'] is str or None and set / unset
        the requested FloatingIP's PTR record based on that.
        """
        if values['ptrdname'] is None:
            self._unset_floatingip_reverse(context, region, floatingip_id)
        elif isinstance(values['ptrdname'], basestring):
            return self._set_floatingip_reverse(
                context, region, floatingip_id, values)

    # Blacklisted Domains
    def create_blacklist(self, context, values):
        policy.check('create_blacklist', context)

        with self.storage_api.create_blacklist(context, values) as blacklist:
            pass  # NOTE: No other systems need updating

        self.notifier.info(context, 'dns.blacklist.create', blacklist)

        return blacklist

    def get_blacklist(self, context, blacklist_id):
        policy.check('get_blacklist', context)

        blacklist = self.storage_api.get_blacklist(context, blacklist_id)

        return blacklist

    def find_blacklists(self, context, criterion=None, marker=None,
                        limit=None, sort_key=None, sort_dir=None):
        policy.check('find_blacklists', context)

        blacklists = self.storage_api.find_blacklists(context, criterion,
                                                      marker, limit,
                                                      sort_key, sort_dir)

        return blacklists

    def find_blacklist(self, context, criterion):
        policy.check('find_blacklist', context)

        blacklist = self.storage_api.find_blacklist(context, criterion)

        return blacklist

    def update_blacklist(self, context, blacklist_id, values):
        policy.check('update_blacklist', context)

        with self.storage_api.update_blacklist(context,
                                               blacklist_id,
                                               values) as blacklist:
            pass  # NOTE: No other systems need updating

        self.notifier.info(context, 'dns.blacklist.update', blacklist)

        return blacklist

    def delete_blacklist(self, context, blacklist_id):
        policy.check('delete_blacklist', context)

        with self.storage_api.delete_blacklist(context,
                                               blacklist_id) as blacklist:
            pass  # NOTE: No other systems need updating

        self.notifier.info(context, 'dns.blacklist.delete', blacklist)

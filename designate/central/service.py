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
import functools

from oslo.config import cfg
from oslo import messaging

from designate.openstack.common import log as logging
from designate.openstack.common import excutils
from designate.i18n import _LI
from designate.i18n import _LC
from designate import backend
from designate import central
from designate import exceptions
from designate import network_api
from designate import objects
from designate import policy
from designate import quota
from designate import service
from designate import utils
from designate import storage


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


def transaction(f):
    # TODO(kiall): Get this a better home :)
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        self.storage.begin()
        try:
            result = f(self, *args, **kwargs)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.storage.rollback()
        else:
            self.storage.commit()
            return result
    return wrapper


class Service(service.Service):
    RPC_API_VERSION = '4.0'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)

        backend_driver = cfg.CONF['service:central'].backend_driver
        self.backend = backend.get_backend(backend_driver, self)

        # Get a storage connection
        storage_driver = cfg.CONF['service:central'].storage_driver
        self.storage = storage.get_storage(storage_driver)

        # Get a quota manager instance
        self.quota = quota.get_quota()

        self.network_api = network_api.get_network_api(cfg.CONF.network_api)

    def start(self):
        # Check to see if there are any TLDs in the database
        tlds = self.storage.find_tlds({})
        if tlds:
            self.check_for_tlds = True
            LOG.info(_LI("Checking for TLDs"))
        else:
            self.check_for_tlds = False
            LOG.info(_LI("NOT checking for TLDs"))

        self.backend.start()

        super(Service, self).start()

    def stop(self):
        super(Service, self).stop()

        self.backend.stop()

    @property
    def mdns_api(self):
        return central.get_mdns_api()

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
                self.storage.find_tld(context, {'name': domain_labels[-1]})
            except exceptions.TldNotFound:
                raise exceptions.InvalidDomainName('Invalid TLD')

            # Now check that the domain name is not the same as a TLD
            try:
                stripped_domain_name = domain_name.strip('.').lower()
                self.storage.find_tld(
                    context,
                    {'name': stripped_domain_name})
            except exceptions.TldNotFound:
                pass
            else:
                raise exceptions.InvalidDomainName(
                    'Domain name cannot be the same as a TLD')

        # Check domain name blacklist
        if self._is_blacklisted_domain_name(context, domain_name):
            # Some users are allowed bypass the blacklist.. Is this one?
            if not policy.check('use_blacklisted_domain', context,
                                do_raise=False):
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
        if recordset_type == 'CNAME' and recordset_name == domain.name:
            raise exceptions.InvalidRecordSetLocation(
                'CNAME recordsets may not be created at the zone apex')

        # CNAME's must not share a name with other recordsets
        criterion = {
            'domain_id': domain.id,
            'name': recordset_name,
        }

        if recordset_type != 'CNAME':
            criterion['type'] = 'CNAME'

        recordsets = self.storage.find_recordsets(context, criterion)

        if ((len(recordsets) == 1 and recordsets[0].id != recordset_id)
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
        LOG.debug("Checking if %s belongs in any of %s subdomains" %
                  (recordset_name, domain.name))

        criterion = criterion or {}

        context = context.elevated()
        context.all_tenants = True

        if domain.name == recordset_name:
            return

        child_domains = self.storage.find_domains(
            context, {"parent_domain_id": domain.id})
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

        blacklists = self.storage.find_blacklists(context)

        for blacklist in blacklists:
            if bool(re.search(blacklist.pattern, domain_name)):
                return True

        return False

    def _is_subdomain(self, context, domain_name):
        """
        Ensures the provided domain_name is the subdomain
        of an existing domain (checks across all tenants)
        """
        context = context.elevated()
        context.all_tenants = True

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

    def _is_superdomain(self, context, domain_name):
        """
        Ensures the provided domain_name is the parent domain
        of an existing subdomain (checks across all tenants)
        """
        context = context.elevated()
        context.all_tenants = True

        # Create wildcard term to catch all subdomains
        search_term = "*%s" % domain_name

        try:
            criterion = {'name': search_term}
            subdomains = self.storage.find_domains(context, criterion)
        except exceptions.DomainNotFound:
            return False

        return subdomains

    def _is_valid_ttl(self, context, ttl):
        min_ttl = cfg.CONF['service:central'].min_ttl
        if min_ttl != "None" and ttl < int(min_ttl):
            try:
                policy.check('use_low_ttl', context)
            except exceptions.Forbidden:
                raise exceptions.InvalidTTL('TTL is below the minimum: %s'
                                            % min_ttl)

    def _increment_domain_serial(self, context, domain_id):
        domain = self.storage.get_domain(context, domain_id)

        # Increment the serial number
        domain.serial = utils.increment_serial(domain.serial)
        domain = self.storage.update_domain(context, domain)

        with wrap_backend_call():
            self.backend.update_domain(context, domain)

        # Update SOA record
        self._update_soa(context, domain)

        return domain

    # Methods to handle priority
    def _get_priority(self, recordset):
        if recordset.type != "MX" and recordset.type != "SRV":
            return recordset
        else:
            if recordset.records is not None:
                for r in recordset.records:
                    r.data = str(r.priority) + " " + r.data

        return recordset

    def _set_priority(self, recordset):
        if recordset.type != "MX" and recordset.type != "SRV":
            return recordset
        else:
            if recordset.records is not None:
                for r in recordset.records:
                    head, sep, tail = r.data.partition(" ")
                    if sep:
                        r.priority = head
                        r.data = tail

        return recordset

    # SOA Recordset Methods
    def _build_soa_record(self, zone, servers):
        return "%s %s. %d %d %d %d %d" % (servers[0]['name'],
                                          zone['email'].replace("@", "."),
                                          zone['serial'],
                                          zone['refresh'],
                                          zone['retry'],
                                          zone['expire'],
                                          zone['minimum'])

    def _create_soa(self, context, zone):
        # Need elevated context to get the servers
        elevated_context = context.elevated()
        elevated_context.all_tenants = True
        servers = self.find_servers(elevated_context)

        soa_values = [self._build_soa_record(zone, servers)]
        recordlist = objects.RecordList(objects=[
            objects.Record(data=r) for r in soa_values])
        values = {
            'name': zone['name'],
            'type': "SOA",
            'records': recordlist
        }
        soa = self.create_recordset(context, zone['id'],
                                    objects.RecordSet(**values), False)
        return soa

    def _update_soa(self, context, zone):

        servers = self.get_domain_servers(context, zone['id'])

        soa = self.find_recordset(context,
                                  criterion={'domain_id': zone['id'],
                                             'type': "SOA"})

        new_values = [self._build_soa_record(zone, servers)]
        recordlist = objects.RecordList(objects=[
            objects.Record(data=r) for r in new_values])

        soa.records = recordlist

        self.update_recordset(context, soa, increment_serial=False)

    # NS Recordset Methods
    def _create_ns(self, context, zone, servers):
        # Create an NS record for each server
        ns_values = []
        for s in servers:
            ns_values.append(s.name)
        recordlist = objects.RecordList(objects=[
            objects.Record(data=r) for r in ns_values])
        values = {
            'name': zone['name'],
            'type': "NS",
            'records': recordlist
        }
        ns = self.create_recordset(context, zone['id'],
                                   objects.RecordSet(**values), False)

        return ns

    def _update_ns(self, context, zone, orig_name, new_name):
        # Get the zone's NS recordset
        ns = self.find_recordset(context,
                                 criterion={'domain_id': zone['id'],
                                            'type': "NS"})
        #
        for r in ns.records:
            if r.data == orig_name:
                r.data = new_name
                self.update_recordset(context, ns)

    def _add_ns(self, context, zone, server):
        # Get NS recordset
        ns = self.find_recordset(context,
                                 criterion={'domain_id': zone['id'],
                                            'type': "NS"})
        # Add new record to recordset
        ns_record = objects.Record(data=server.name)
        new_record = self.create_record(context, zone['id'],
                                        ns['id'], ns_record,
                                        increment_serial=False)

        ns.records.append(new_record)

        self.update_recordset(context, ns)

    def _delete_ns(self, context, zone, server):
        ns = self.find_recordset(context,
                                 criterion={'domain_id': zone['id'],
                                            'type': "NS"})
        records = ns.records

        for r in records:
            if r.data == server.name:
                ns.records.remove(r)

        self.update_recordset(context, ns)

    # Quota Enforcement Methods
    def _enforce_domain_quota(self, context, tenant_id):
        criterion = {'tenant_id': tenant_id}
        count = self.storage.count_domains(context, criterion)

        self.quota.limit_check(context, tenant_id, domains=count)

    def _enforce_recordset_quota(self, context, domain):
        # TODO(kiall): Enforce RRSet Quotas
        pass

    def _enforce_record_quota(self, context, domain, recordset):
        # Ensure the records per domain quota is OK
        criterion = {'domain_id': domain['id']}
        count = self.storage.count_records(context, criterion)

        self.quota.limit_check(context, domain['tenant_id'],
                               domain_records=count)

        # TODO(kiall): Enforce Records per RRSet Quotas

    # Misc Methods
    def get_absolute_limits(self, context):
        # NOTE(Kiall): Currently, we only have quota based limits..
        return self.quota.get_quotas(context, context.tenant)

    # Quota Methods
    def get_quotas(self, context, tenant_id):
        target = {'tenant_id': tenant_id}
        policy.check('get_quotas', context, target)

        # This allows admins to get quota information correctly for all tenants
        context.all_tenants = True

        return self.quota.get_quotas(context, tenant_id)

    def get_quota(self, context, tenant_id, resource):
        target = {'tenant_id': tenant_id, 'resource': resource}
        policy.check('get_quota', context, target)

        return self.quota.get_quota(context, tenant_id, resource)

    @transaction
    def set_quota(self, context, tenant_id, resource, hard_limit):
        target = {
            'tenant_id': tenant_id,
            'resource': resource,
            'hard_limit': hard_limit,
        }

        policy.check('set_quota', context, target)

        return self.quota.set_quota(context, tenant_id, resource, hard_limit)

    @transaction
    def reset_quotas(self, context, tenant_id):
        target = {'tenant_id': tenant_id}
        policy.check('reset_quotas', context, target)

        self.quota.reset_quotas(context, tenant_id)

    # Server Methods
    @transaction
    def create_server(self, context, server):
        policy.check('create_server', context)

        created_server = self.storage.create_server(context, server)

        # Update backend with the new server..
        with wrap_backend_call():
            self.backend.create_server(context, created_server)

        self.notifier.info(context, 'dns.server.create', created_server)

        # Update NS recordsets for all zones
        elevated_context = context.elevated()
        elevated_context.all_tenants = True
        zones = self.find_domains(elevated_context)
        # Create a new NS recordset for for every zone
        for z in zones:
            self._add_ns(elevated_context, z, server)

        return created_server

    def find_servers(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        policy.check('find_servers', context)

        return self.storage.find_servers(context, criterion, marker, limit,
                                         sort_key, sort_dir)

    def get_server(self, context, server_id):
        policy.check('get_server', context, {'server_id': server_id})

        return self.storage.get_server(context, server_id)

    @transaction
    def update_server(self, context, server):
        target = {
            'server_id': server.obj_get_original_value('id'),
        }
        policy.check('update_server', context, target)
        orig_server_name = server.obj_get_original_value('name')
        new_server_name = server.name

        server = self.storage.update_server(context, server)

        # Update backend with the new details..
        with wrap_backend_call():
            self.backend.update_server(context, server)

        self.notifier.info(context, 'dns.server.update', server)

        # Update NS recordsets for all zones
        elevated_context = context.elevated()
        elevated_context.all_tenants = True
        zones = self.find_domains(elevated_context)
        for z in zones:
            self._update_ns(elevated_context, z, orig_server_name,
                            new_server_name)

        return server

    @transaction
    def delete_server(self, context, server_id):
        policy.check('delete_server', context, {'server_id': server_id})

        # don't delete last of servers
        servers = self.storage.find_servers(context)
        if len(servers) == 1 and server_id == servers[0].id:
            raise exceptions.LastServerDeleteNotAllowed(
                "Not allowed to delete last of servers")

        server = self.storage.delete_server(context, server_id)

        # Update NS recordsets for all zones
        elevated_context = context.elevated()
        elevated_context.all_tenants = True
        zones = self.find_domains(elevated_context)
        for z in zones:
            self._delete_ns(elevated_context, z, server)

        # Update backend with the new server..
        with wrap_backend_call():
            self.backend.delete_server(context, server)

        self.notifier.info(context, 'dns.server.delete', server)

    # TLD Methods
    @transaction
    def create_tld(self, context, tld):
        policy.check('create_tld', context)

        # The TLD is only created on central's storage and not on the backend.
        created_tld = self.storage.create_tld(context, tld)

        self.notifier.info(context, 'dns.tld.create', created_tld)

        # Set check for tlds to be true
        self.check_for_tlds = True
        return created_tld

    def find_tlds(self, context, criterion=None, marker=None, limit=None,
                  sort_key=None, sort_dir=None):
        policy.check('find_tlds', context)

        return self.storage.find_tlds(context, criterion, marker, limit,
                                      sort_key, sort_dir)

    def get_tld(self, context, tld_id):
        policy.check('get_tld', context, {'tld_id': tld_id})

        return self.storage.get_tld(context, tld_id)

    @transaction
    def update_tld(self, context, tld):
        target = {
            'tld_id': tld.obj_get_original_value('id'),
        }
        policy.check('update_tld', context, target)

        tld = self.storage.update_tld(context, tld)

        self.notifier.info(context, 'dns.tld.update', tld)

        return tld

    @transaction
    def delete_tld(self, context, tld_id):
        # Known issue - self.check_for_tld is not reset here.  So if the last
        # TLD happens to be deleted, then we would incorrectly do the TLD
        # validations.
        # This decision was influenced by weighing the (ultra low) probability
        # of hitting this issue vs doing the checks for every delete.
        policy.check('delete_tld', context, {'tld_id': tld_id})

        tld = self.storage.delete_tld(context, tld_id)

        self.notifier.info(context, 'dns.tld.delete', tld)

    # TSIG Key Methods
    @transaction
    def create_tsigkey(self, context, tsigkey):
        policy.check('create_tsigkey', context)

        created_tsigkey = self.storage.create_tsigkey(context, tsigkey)

        with wrap_backend_call():
            self.backend.create_tsigkey(context, created_tsigkey)

        self.notifier.info(context, 'dns.tsigkey.create', created_tsigkey)

        return created_tsigkey

    def find_tsigkeys(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        policy.check('find_tsigkeys', context)

        return self.storage.find_tsigkeys(context, criterion, marker,
                                          limit, sort_key, sort_dir)

    def get_tsigkey(self, context, tsigkey_id):
        policy.check('get_tsigkey', context, {'tsigkey_id': tsigkey_id})

        return self.storage.get_tsigkey(context, tsigkey_id)

    @transaction
    def update_tsigkey(self, context, tsigkey):
        target = {
            'tsigkey_id': tsigkey.obj_get_original_value('id'),
        }
        policy.check('update_tsigkey', context, target)

        tsigkey = self.storage.update_tsigkey(context, tsigkey)

        with wrap_backend_call():
            self.backend.update_tsigkey(context, tsigkey)

        self.notifier.info(context, 'dns.tsigkey.update', tsigkey)

        return tsigkey

    @transaction
    def delete_tsigkey(self, context, tsigkey_id):
        policy.check('delete_tsigkey', context, {'tsigkey_id': tsigkey_id})

        tsigkey = self.storage.delete_tsigkey(context, tsigkey_id)

        with wrap_backend_call():
            self.backend.delete_tsigkey(context, tsigkey)

        self.notifier.info(context, 'dns.tsigkey.delete', tsigkey)

    # Tenant Methods
    def find_tenants(self, context):
        policy.check('find_tenants', context)
        return self.storage.find_tenants(context)

    def get_tenant(self, context, tenant_id):
        target = {
            'tenant_id': tenant_id
        }

        policy.check('get_tenant', context, target)

        return self.storage.get_tenant(context, tenant_id)

    def count_tenants(self, context):
        policy.check('count_tenants', context)
        return self.storage.count_tenants(context)

    # Domain Methods
    @transaction
    def create_domain(self, context, domain):
        # TODO(kiall): Refactor this method into *MUCH* smaller chunks.

        # Default to creating in the current users tenant
        if domain.tenant_id is None:
            domain.tenant_id = context.tenant

        target = {
            'tenant_id': domain.tenant_id,
            'domain_name': domain.name
        }

        policy.check('create_domain', context, target)

        # Ensure the tenant has enough quota to continue
        self._enforce_domain_quota(context, domain.tenant_id)

        # Ensure the domain name is valid
        self._is_valid_domain_name(context, domain.name)

        # Ensure TTL is above the minimum
        if domain.ttl is not None:
            self._is_valid_ttl(context, domain.ttl)

        # Handle sub-domains appropriately
        parent_domain = self._is_subdomain(context, domain.name)
        if parent_domain:
            if parent_domain.tenant_id == domain.tenant_id:
                # Record the Parent Domain ID
                domain.parent_domain_id = parent_domain.id
            else:
                raise exceptions.Forbidden('Unable to create subdomain in '
                                           'another tenants domain')

        # Handle super-domains appropriately
        subdomains = self._is_superdomain(context, domain.name)
        if subdomains:
            LOG.debug("Domain '{0}' is a superdomain.".format(domain.name))
            for subdomain in subdomains:
                if subdomain.tenant_id != domain.tenant_id:
                    raise exceptions.Forbidden('Unable to create domain '
                                               'because another tenant '
                                               'owns a subdomain of '
                                               'the domain')
        # If this succeeds, subdomain parent IDs will be updated
        # after domain is created

        # NOTE(kiall): Fetch the servers before creating the domain, this way
        #              we can prevent domain creation if no servers are
        #              configured.
        servers = self.storage.find_servers(context)

        if len(servers) == 0:
            LOG.critical(_LC('No servers configured. '
                             'Please create at least one server'))
            raise exceptions.NoServersConfigured()

        # Set the serial number
        domain.serial = utils.increment_serial()

        created_domain = self.storage.create_domain(context, domain)

        with wrap_backend_call():
            self.backend.create_domain(context, created_domain)

        self.notifier.info(context, 'dns.domain.create', created_domain)

        # If domain is a superdomain, update subdomains
        # with new parent IDs
        for subdomain in subdomains:
            LOG.debug("Updating subdomain '{0}' parent ID "
                      "using superdomain ID '{1}'"
                      .format(subdomain.name, domain.id))
            subdomain.parent_domain_id = domain.id
            self.update_domain(context, subdomain)

        # Create the SOA and NS recordsets for the new domain
        self._create_soa(context, created_domain)
        self._create_ns(context, created_domain, servers)

        return created_domain

    def get_domain(self, context, domain_id):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'tenant_id': domain.tenant_id
        }
        policy.check('get_domain', context, target)

        return domain

    def get_domain_servers(self, context, domain_id, criterion=None):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'tenant_id': domain.tenant_id
        }

        policy.check('get_domain_servers', context, target)

        # TODO(kiall): Once we allow domains to be allocated on 1 of N server
        #              pools, return the filtered list here.
        return self.storage.find_servers(context, criterion)

    def find_domains(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_domains', context, target)

        return self.storage.find_domains(context, criterion, marker, limit,
                                         sort_key, sort_dir)

    def find_domain(self, context, criterion=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_domain', context, target)

        return self.storage.find_domain(context, criterion)

    @transaction
    def update_domain(self, context, domain, increment_serial=True):
        # TODO(kiall): Refactor this method into *MUCH* smaller chunks.
        target = {
            'domain_id': domain.obj_get_original_value('id'),
            'domain_name': domain.obj_get_original_value('name'),
            'tenant_id': domain.obj_get_original_value('tenant_id'),
        }

        policy.check('update_domain', context, target)

        changes = domain.obj_get_changes()

        # Ensure immutable fields are not changed
        if 'tenant_id' in changes:
            # TODO(kiall): Moving between tenants should be allowed, but the
            #              current code will not take into account that
            #              RecordSets and Records must also be moved.
            raise exceptions.BadRequest('Moving a domain between tenants is '
                                        'not allowed')

        if 'name' in changes:
            raise exceptions.BadRequest('Renaming a domain is not allowed')

        # Ensure TTL is above the minimum
        ttl = changes.get('ttl', None)
        if ttl is not None:
            self._is_valid_ttl(context, ttl)

        if increment_serial:
            # Increment the serial number
            domain.serial = utils.increment_serial(domain.serial)
            self._update_soa(context, domain)

        domain = self.storage.update_domain(context, domain)

        with wrap_backend_call():
            self.backend.update_domain(context, domain)

        self.notifier.info(context, 'dns.domain.update', domain)
        self.mdns_api.notify_zone_changed(context, domain.name)

        return domain

    @transaction
    def delete_domain(self, context, domain_id):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'tenant_id': domain.tenant_id
        }

        policy.check('delete_domain', context, target)

        # Prevent deletion of a zone which has child zones
        criterion = {'parent_domain_id': domain_id}

        if self.storage.count_domains(context, criterion) > 0:
            raise exceptions.DomainHasSubdomain('Please delete any subdomains '
                                                'before deleting this domain')

        domain = self.storage.delete_domain(context, domain_id)

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

        return self.storage.count_domains(context, criterion)

    # Report combining all the count reports based on criterion
    def count_report(self, context, criterion=None):
        reports = []

        if criterion is None:
            # Get all the reports
            reports.append({'zones': self.count_domains(context),
                            'records': self.count_records(context),
                            'tenants': self.count_tenants(context)})
        elif criterion == 'zones':
            reports.append({'zones': self.count_domains(context)})
        elif criterion == 'records':
            reports.append({'records': self.count_records(context)})
        elif criterion == 'tenants':
            reports.append({'tenants': self.count_tenants(context)})
        else:
            raise exceptions.ReportNotFound()

        return reports

    @transaction
    def touch_domain(self, context, domain_id):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'tenant_id': domain.tenant_id
        }

        policy.check('touch_domain', context, target)

        domain = self._increment_domain_serial(context, domain_id)

        self.notifier.info(context, 'dns.domain.touch', domain)

        return domain

    # RecordSet Methods
    @transaction
    def create_recordset(self, context, domain_id, recordset,
                         increment_serial=True):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'recordset_name': recordset.name,
            'tenant_id': domain.tenant_id,
        }

        policy.check('create_recordset', context, target)

        # Ensure the tenant has enough quota to continue
        self._enforce_recordset_quota(context, domain)

        # Ensure TTL is above the minimum
        ttl = getattr(recordset, 'ttl', None)
        if ttl is not None:
            self._is_valid_ttl(context, ttl)

        # Ensure the recordset name and placement is valid
        self._is_valid_recordset_name(context, domain, recordset.name)
        self._is_valid_recordset_placement(context, domain, recordset.name,
                                           recordset.type)
        self._is_valid_recordset_placement_subdomain(
            context, domain, recordset.name)

        # Extract the priority from the records
        recordset = self._set_priority(recordset)

        created_recordset = self.storage.create_recordset(context, domain_id,
                                                          recordset)

        with wrap_backend_call():
            self.backend.create_recordset(context, domain, created_recordset)

        # Send RecordSet creation notification
        self.notifier.info(context, 'dns.recordset.create', created_recordset)

        # Only increment the serial # if records exist and
        # increment_serial = True
        if increment_serial:
            if len(recordset.records) > 0:
                self._increment_domain_serial(context, domain.id)

        # Get the correct format for priority
        return self._get_priority(recordset)

    def get_recordset(self, context, domain_id, recordset_id):
        domain = self.storage.get_domain(context, domain_id)
        recordset = self.storage.get_recordset(context, recordset_id)

        # Ensure the domain_id matches the record's domain_id
        if domain.id != recordset.domain_id:
            raise exceptions.RecordSetNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'recordset_id': recordset.id,
            'tenant_id': domain.tenant_id,
        }

        policy.check('get_recordset', context, target)

        # Add the priority to the records
        recordset = self._get_priority(recordset)

        return recordset

    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_recordsets', context, target)

        recordsets = self.storage.find_recordsets(context, criterion, marker,
                                                  limit, sort_key, sort_dir)

        # Set the priority for each record
        for rs in recordsets:
            rs = self._get_priority(rs)

        return recordsets

    def find_recordset(self, context, criterion=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_recordset', context, target)

        recordset = self.storage.find_recordset(context, criterion)

        # Add the priority to the records
        recordset = self._get_priority(recordset)

        return recordset

    @transaction
    def update_recordset(self, context, recordset, increment_serial=True):
        domain_id = recordset.obj_get_original_value('domain_id')
        domain = self.storage.get_domain(context, domain_id)

        # Set the priority for the records
        recordset = self._set_priority(recordset)

        changes = recordset.obj_get_changes()

        # Ensure immutable fields are not changed
        if 'tenant_id' in changes:
            raise exceptions.BadRequest('Moving a recordset between tenants '
                                        'is not allowed')

        if 'domain_id' in changes:
            raise exceptions.BadRequest('Moving a recordset between domains '
                                        'is not allowed')

        if 'type' in changes:
            raise exceptions.BadRequest('Changing a recordsets type is not '
                                        'allowed')

        target = {
            'domain_id': recordset.obj_get_original_value('domain_id'),
            'recordset_id': recordset.obj_get_original_value('id'),
            'domain_name': domain.name,
            'tenant_id': domain.tenant_id
        }

        policy.check('update_recordset', context, target)

        # Ensure the record name is valid
        self._is_valid_recordset_name(context, domain, recordset.name)
        self._is_valid_recordset_placement(context, domain, recordset.name,
                                           recordset.type, recordset.id)
        self._is_valid_recordset_placement_subdomain(
            context, domain, recordset.name)

        # Ensure TTL is above the minimum
        ttl = changes.get('ttl', None)
        if ttl is not None:
            self._is_valid_ttl(context, ttl)

        # Update the recordset
        recordset = self.storage.update_recordset(context, recordset)

        with wrap_backend_call():
            self.backend.update_recordset(context, domain, recordset)

        if increment_serial:
            self._increment_domain_serial(context, domain.id)

        # Send RecordSet update notification
        self.notifier.info(context, 'dns.recordset.update', recordset)
        self.mdns_api.notify_zone_changed(context, domain.name)

        return self._get_priority(recordset)

    @transaction
    def delete_recordset(self, context, domain_id, recordset_id,
                         increment_serial=True):
        domain = self.storage.get_domain(context, domain_id)
        recordset = self.storage.get_recordset(context, recordset_id)

        # Ensure the domain_id matches the recordset's domain_id
        if domain.id != recordset.domain_id:
            raise exceptions.RecordSetNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'recordset_id': recordset.id,
            'tenant_id': domain.tenant_id
        }

        policy.check('delete_recordset', context, target)

        recordset = self.storage.delete_recordset(context, recordset_id)

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

        return self.storage.count_recordsets(context, criterion)

    # Record Methods
    @transaction
    def create_record(self, context, domain_id, recordset_id, record,
                      increment_serial=True):
        domain = self.storage.get_domain(context, domain_id)
        recordset = self.storage.get_recordset(context, recordset_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'recordset_id': recordset_id,
            'recordset_name': recordset.name,
            'tenant_id': domain.tenant_id
        }

        policy.check('create_record', context, target)

        # Ensure the tenant has enough quota to continue
        self._enforce_record_quota(context, domain, recordset)

        created_record = self.storage.create_record(context, domain_id,
                                                    recordset_id, record)

        with wrap_backend_call():
            self.backend.create_record(
                context, domain, recordset, created_record)

        if increment_serial:
            self._increment_domain_serial(context, domain_id)

        # Send Record creation notification
        self.notifier.info(context, 'dns.record.create', created_record)

        return created_record

    def get_record(self, context, domain_id, recordset_id, record_id):
        domain = self.storage.get_domain(context, domain_id)
        recordset = self.storage.get_recordset(context, recordset_id)
        record = self.storage.get_record(context, record_id)

        # Ensure the domain_id matches the record's domain_id
        if domain.id != record.domain_id:
            raise exceptions.RecordNotFound()

        # Ensure the recordset_id matches the record's recordset_id
        if recordset.id != record.recordset_id:
            raise exceptions.RecordNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'recordset_id': recordset_id,
            'recordset_name': recordset.name,
            'record_id': record.id,
            'tenant_id': domain.tenant_id
        }

        policy.check('get_record', context, target)

        return record

    def find_records(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_records', context, target)

        return self.storage.find_records(context, criterion, marker, limit,
                                         sort_key, sort_dir)

    def find_record(self, context, criterion=None):
        target = {'tenant_id': context.tenant}
        policy.check('find_record', context, target)

        return self.storage.find_record(context, criterion)

    @transaction
    def update_record(self, context, record, increment_serial=True):
        domain_id = record.obj_get_original_value('domain_id')
        domain = self.storage.get_domain(context, domain_id)

        recordset_id = record.obj_get_original_value('recordset_id')
        recordset = self.storage.get_recordset(context, recordset_id)

        changes = record.obj_get_changes()

        # Ensure immutable fields are not changed
        if 'tenant_id' in changes:
            raise exceptions.BadRequest('Moving a recordset between tenants '
                                        'is not allowed')

        if 'domain_id' in changes:
            raise exceptions.BadRequest('Moving a recordset between domains '
                                        'is not allowed')

        if 'recordset_id' in changes:
            raise exceptions.BadRequest('Moving a recordset between '
                                        'recordsets is not allowed')

        target = {
            'domain_id': record.obj_get_original_value('domain_id'),
            'domain_name': domain.name,
            'recordset_id': record.obj_get_original_value('recordset_id'),
            'recordset_name': recordset.name,
            'record_id': record.obj_get_original_value('id'),
            'tenant_id': domain.tenant_id
        }

        policy.check('update_record', context, target)

        # Update the record
        record = self.storage.update_record(context, record)

        with wrap_backend_call():
            self.backend.update_record(context, domain, recordset, record)

        if increment_serial:
            self._increment_domain_serial(context, domain.id)

        # Send Record update notification
        self.notifier.info(context, 'dns.record.update', record)
        self.mdns_api.notify_zone_changed(context, domain.name)

        return record

    @transaction
    def delete_record(self, context, domain_id, recordset_id, record_id,
                      increment_serial=True):
        domain = self.storage.get_domain(context, domain_id)
        recordset = self.storage.get_recordset(context, recordset_id)
        record = self.storage.get_record(context, record_id)

        # Ensure the domain_id matches the record's domain_id
        if domain.id != record.domain_id:
            raise exceptions.RecordNotFound()

        # Ensure the recordset_id matches the record's recordset_id
        if recordset.id != record.recordset_id:
            raise exceptions.RecordNotFound()

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'recordset_id': recordset_id,
            'recordset_name': recordset.name,
            'record_id': record.id,
            'tenant_id': domain.tenant_id
        }

        policy.check('delete_record', context, target)

        record = self.storage.delete_record(context, record_id)

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
        return self.storage.count_records(context, criterion)

    # Diagnostics Methods
    def _sync_domain(self, context, domain):
        recordsets = self.storage.find_recordsets(
            context, criterion={'domain_id': domain['id']})

        # Since we now have records as well as recordsets we need to get the
        # records for it as well and pass that down since the backend wants it.
        rdata = []
        for recordset in recordsets:
            records = self.find_records(
                context, {'recordset_id': recordset.id})
            rdata.append((recordset, records))
        with wrap_backend_call():
            return self.backend.sync_domain(context, domain, rdata)

    @transaction
    def sync_domains(self, context):
        policy.check('diagnostics_sync_domains', context)

        domains = self.storage.find_domains(context)

        results = {}
        for domain in domains:
            results[domain.id] = self._sync_domain(context, domain)

        return results

    @transaction
    def sync_domain(self, context, domain_id):
        domain = self.storage.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'tenant_id': domain.tenant_id
        }

        policy.check('diagnostics_sync_domain', context, target)

        return self._sync_domain(context, domain)

    @transaction
    def sync_record(self, context, domain_id, recordset_id, record_id):
        domain = self.storage.get_domain(context, domain_id)
        recordset = self.storage.get_recordset(context, recordset_id)

        target = {
            'domain_id': domain_id,
            'domain_name': domain.name,
            'recordset_id': recordset_id,
            'recordset_name': recordset.name,
            'record_id': record_id,
            'tenant_id': domain.tenant_id
        }

        policy.check('diagnostics_sync_record', context, target)

        record = self.storage.get_record(context, record_id)

        with wrap_backend_call():
            return self.backend.sync_record(context, domain, recordset, record)

    def ping(self, context):
        policy.check('diagnostics_ping', context)

        try:
            backend_status = self.backend.ping(context)
        except Exception as e:
            backend_status = {'status': False, 'message': str(e)}

        try:
            storage_status = self.storage.ping(context)
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
        tenant_id = tenant_id or context.tenant

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
                    recordset = self.storage.get_recordset(
                        elevated_context, value[1]['recordset_id'])

                if recordset['ttl'] is not None:
                    fip_ptr['ttl'] = recordset['ttl']
                else:
                    zone = self.get_domain(
                        elevated_context, value[1]['domain_id'])
                    fip_ptr['ttl'] = zone['ttl']

                fip_ptr['ptrdname'] = value[1]['data']
            else:
                LOG.debug("No record information found for %s" %
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
                (floatingip_id, region, context.tenant)
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
            zone = self.storage.find_domain(
                elevated_context, {'name': zone_name})
        except exceptions.DomainNotFound:
            msg = _LI('Creating zone for %(fip_id)s:%(region)s - '
                      '%(fip_addr)s zone %(zonename)s') % \
                    {'fip_id': floatingip_id, 'region': region,
                    'fip_addr': fip['address'], 'zonename': zone_name}
            LOG.info(msg)

            email = cfg.CONF['service:central'].managed_resource_email
            tenant_id = cfg.CONF['service:central'].managed_resource_tenant_id

            zone_values = {
                'name': zone_name,
                'email': email,
                'tenant_id': tenant_id
            }

            zone = self.create_domain(
                elevated_context, objects.Domain(**zone_values))

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
            'ttl': values.get('ttl', None),
        }

        recordset = self.create_recordset(
            elevated_context,
            zone['id'],
            objects.RecordSet(**recordset_values))

        record_values = {
            'data': values['ptrdname'],
            'description': values['description'],
            'managed': True,
            'managed_extra': fip['address'],
            'managed_resource_id': floatingip_id,
            'managed_resource_region': region,
            'managed_resource_type': 'ptr:floatingip',
            'managed_tenant_id': context.tenant
        }

        record = self.create_record(
            elevated_context,
            zone['id'],
            recordset['id'],
            objects.Record(**record_values))

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
            'managed_tenant_id': context.tenant
        }

        try:
            record = self.storage.find_record(
                elevated_context, criterion=criterion)
        except exceptions.RecordNotFound:
            msg = 'No such FloatingIP %s:%s' % (region, floatingip_id)
            raise exceptions.NotFound(msg)

        self.delete_record(
            elevated_context,
            record['domain_id'],
            record['recordset_id'],
            record['id'])

    @transaction
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
    @transaction
    def create_blacklist(self, context, blacklist):
        policy.check('create_blacklist', context)

        created_blacklist = self.storage.create_blacklist(context, blacklist)

        self.notifier.info(context, 'dns.blacklist.create', created_blacklist)

        return created_blacklist

    def get_blacklist(self, context, blacklist_id):
        policy.check('get_blacklist', context)

        blacklist = self.storage.get_blacklist(context, blacklist_id)

        return blacklist

    def find_blacklists(self, context, criterion=None, marker=None,
                        limit=None, sort_key=None, sort_dir=None):
        policy.check('find_blacklists', context)

        blacklists = self.storage.find_blacklists(context, criterion,
                                                  marker, limit,
                                                  sort_key, sort_dir)

        return blacklists

    def find_blacklist(self, context, criterion):
        policy.check('find_blacklist', context)

        blacklist = self.storage.find_blacklist(context, criterion)

        return blacklist

    @transaction
    def update_blacklist(self, context, blacklist):
        target = {
            'blacklist_id': blacklist.id,
        }
        policy.check('update_blacklist', context, target)

        blacklist = self.storage.update_blacklist(context, blacklist)

        self.notifier.info(context, 'dns.blacklist.update', blacklist)

        return blacklist

    @transaction
    def delete_blacklist(self, context, blacklist_id):
        policy.check('delete_blacklist', context)

        blacklist = self.storage.delete_blacklist(context, blacklist_id)

        self.notifier.info(context, 'dns.blacklist.delete', blacklist)

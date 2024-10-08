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
import hashlib

from oslo_log import log as logging
from oslo_utils import timeutils
from sqlalchemy import case, select, distinct, func
from sqlalchemy.sql.expression import or_, literal_column

from designate.common import constants
from designate import exceptions
from designate import objects
from designate.objects.adapters import DesignateAdapter
from designate.storage import sql
from designate.storage.sqlalchemy import base
from designate.storage.sqlalchemy import tables

import designate.conf


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)

MAXIMUM_SUBZONE_DEPTH = 128


class SQLAlchemyStorage(base.SQLAlchemy):
    """SQLAlchemy connection"""
    __plugin_name__ = 'sqlalchemy'

    def __init__(self):
        super().__init__()

    def get_inspector(self):
        return sql.get_inspector()

    # CRUD for our resources (quota, server, tsigkey, tenant, zone & record)
    # R - get_*, find_*s
    #
    # Standard Arguments
    # self      - python object for the class
    # context   - a dictionary of details about the request (http etc),
    #             provided by flask.
    # criterion - dictionary of filters to be applied
    #

    # Quota Methods
    def _find_quotas(self, context, criterion, one=False, marker=None,
                     limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.quotas, objects.Quota, objects.QuotaList,
            exceptions.QuotaNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_quota(self, context, quota):
        """
        Create a Quota.

        :param context: RPC Context.
        :param quota: Quota object with the values to be created.
        """
        if not isinstance(quota, objects.Quota):
            # TODO(kiall): Quotas should always use Objects
            quota = objects.Quota(**quota)

        return self._create(
            tables.quotas, quota, exceptions.DuplicateQuota)

    def get_quota(self, context, quota_id):
        """
        Get a Quota via ID.

        :param context: RPC Context.
        :param quota_id: Quota ID to get.
        """
        return self._find_quotas(context, {'id': quota_id}, one=True)

    def find_quotas(self, context, criterion=None, marker=None, limit=None,
                    sort_key=None, sort_dir=None):
        """
        Find Quotas

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        return self._find_quotas(context, criterion, marker=marker,
                                 limit=limit, sort_key=sort_key,
                                 sort_dir=sort_dir)

    def find_quota(self, context, criterion):
        """
        Find a single Quota.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_quotas(context, criterion, one=True)

    def update_quota(self, context, quota):
        """
        Update a Quota

        :param context: RPC Context.
        :param quota: Quota to update.
        """
        return self._update(
            context, tables.quotas, quota, exceptions.DuplicateQuota,
            exceptions.QuotaNotFound)

    def delete_quota(self, context, quota_id):
        """
        Delete a Quota via ID.

        :param context: RPC Context.
        :param quota_id: Delete a Quota via ID
        """
        # Fetch the existing quota, we'll need to return it.
        quota = self._find_quotas(context, {'id': quota_id}, one=True)
        return self._delete(context, tables.quotas, quota,
                            exceptions.QuotaNotFound)

    # TLD Methods
    def _find_tlds(self, context, criterion, one=False, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.tlds, objects.Tld, objects.TldList,
            exceptions.TldNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_tld(self, context, tld):
        """
        Create a TLD.

        :param context: RPC Context.
        :param tld: Tld object with the values to be created.
        """
        return self._create(
            tables.tlds, tld, exceptions.DuplicateTld)

    def get_tld(self, context, tld_id):
        """
        Get a TLD via ID.

        :param context: RPC Context.
        :param tld_id: TLD ID to get.
        """
        return self._find_tlds(context, {'id': tld_id}, one=True)

    def find_tlds(self, context, criterion=None, marker=None, limit=None,
                  sort_key=None, sort_dir=None):
        """
        Find TLDs

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        return self._find_tlds(context, criterion, marker=marker, limit=limit,
                               sort_key=sort_key, sort_dir=sort_dir)

    def find_tld(self, context, criterion):
        """
        Find a single TLD.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_tlds(context, criterion, one=True)

    def update_tld(self, context, tld):
        """
        Update a TLD

        :param context: RPC Context.
        :param tld: TLD to update.
        """
        return self._update(
            context, tables.tlds, tld, exceptions.DuplicateTld,
            exceptions.TldNotFound)

    def delete_tld(self, context, tld_id):
        """
        Delete a TLD via ID.

        :param context: RPC Context.
        :param tld_id: Delete a TLD via ID
        """
        # Fetch the existing tld, we'll need to return it.
        tld = self._find_tlds(context, {'id': tld_id}, one=True)
        return self._delete(context, tables.tlds, tld, exceptions.TldNotFound)

    # TSIG Key Methods
    def _find_tsigkeys(self, context, criterion, one=False, marker=None,
                       limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.tsigkeys, objects.TsigKey, objects.TsigKeyList,
            exceptions.TsigKeyNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_tsigkey(self, context, tsigkey):
        """
        Create a TSIG Key.

        :param context: RPC Context.
        :param tsigkey: TsigKey object with the values to be created.
        """
        return self._create(
            tables.tsigkeys, tsigkey, exceptions.DuplicateTsigKey)

    def get_tsigkey(self, context, tsigkey_id):
        """
        Get a TSIG Key via ID.

        :param context: RPC Context.
        :param tsigkey_id: Server ID to get.
        """
        return self._find_tsigkeys(context, {'id': tsigkey_id}, one=True)

    def find_tsigkeys(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        """
        Find TSIG Keys.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        return self._find_tsigkeys(context, criterion, marker=marker,
                                   limit=limit, sort_key=sort_key,
                                   sort_dir=sort_dir)

    def find_tsigkey(self, context, criterion):
        """
        Find TSIG Key.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_tsigkeys(context, criterion, one=True)

    def update_tsigkey(self, context, tsigkey):
        """
        Update a TSIG Key

        :param context: RPC Context.
        :param tsigkey: TSIG Keyto update.
        """
        return self._update(
            context, tables.tsigkeys, tsigkey, exceptions.DuplicateTsigKey,
            exceptions.TsigKeyNotFound)

    def delete_tsigkey(self, context, tsigkey_id):
        """
        Delete a TSIG Key via ID.

        :param context: RPC Context.
        :param tsigkey_id: Delete a TSIG Key via ID
        """
        # Fetch the existing tsigkey, we'll need to return it.
        tsigkey = self._find_tsigkeys(context, {'id': tsigkey_id}, one=True)
        return self._delete(context, tables.tsigkeys, tsigkey,
                            exceptions.TsigKeyNotFound)

    ##
    # Tenant Methods
    ##
    def find_tenants(self, context):
        """
        Find all Tenants.

        :param context: RPC Context.
        """
        # returns an array of tenant_id & count of their zones
        query = select(tables.zones.c.tenant_id, func.count(tables.zones.c.id))
        query = self._apply_tenant_criteria(context, tables.zones, query)
        query = self._apply_deleted_criteria(context, tables.zones, query)
        query = query.group_by(tables.zones.c.tenant_id)

        with sql.get_read_session() as session:
            resultproxy = session.execute(query)
            results = resultproxy.fetchall()

        tenant_list = objects.TenantList(
            objects=[objects.Tenant(id=t[0], zone_count=t[1]) for t in
                     results])

        tenant_list.obj_reset_changes()

        return tenant_list

    def get_tenant(self, context, tenant_id):
        """
        Get Tenant.

        :param context: RPC Context.
        :param tenant_id: ID of the Tenant.
        """
        # get list & count of all zones owned by given tenant_id
        query = select(tables.zones.c.name)
        query = self._apply_tenant_criteria(context, tables.zones, query)
        query = self._apply_deleted_criteria(context, tables.zones, query)
        query = query.where(tables.zones.c.tenant_id == tenant_id)

        with sql.get_read_session() as session:
            resultproxy = session.execute(query)
            results = resultproxy.fetchall()

        return objects.Tenant(
            id=tenant_id,
            zone_count=len(results),
            zones=[r[0] for r in results])

    def count_tenants(self, context):
        """
        Count tenants

        :param context: RPC Context.
        """
        # tenants are the owner of zones, count the number of unique tenants
        # select count(distinct tenant_id) from zones
        query = select(func.count(distinct(tables.zones.c.tenant_id)))
        query = self._apply_tenant_criteria(context, tables.zones, query)
        query = self._apply_deleted_criteria(context, tables.zones, query)

        with sql.get_read_session() as session:
            resultproxy = session.execute(query)
            result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    ##
    # Zone Methods
    ##
    def _find_zones(self, context, criterion, one=False, marker=None,
                    limit=None, sort_key=None, sort_dir=None,
                    apply_tenant_criteria=True, include_shared=False):
        # Check to see if the criterion can use the reverse_name column
        criterion = self._rname_check(criterion)

        # Create a virtual column showing if the zone is shared or not.
        shared_case = case((tables.shared_zones.c.target_project_id.is_(None),
                            literal_column('False')),
                           else_=literal_column('True')).label('shared')
        query = select(
            tables.zones,
            shared_case).outerjoin(tables.shared_zones).distinct()

        zones = self._find(
            context, tables.zones, objects.Zone, objects.ZoneList,
            exceptions.ZoneNotFound, criterion, one, marker, limit,
            sort_key, sort_dir, query=query,
            apply_tenant_criteria=apply_tenant_criteria,
            include_shared=include_shared)

        def _load_relations(zone):
            if zone.type == 'SECONDARY':
                zone.masters = self._find_zone_masters(
                    context, {'zone_id': zone.id})
            else:
                # This avoids an extra DB call per primary zone. This will
                # always have 0 results for a PRIMARY zone.
                zone.masters = objects.ZoneMasterList()

            zone.attributes = self._find_zone_attributes(
                context, {'zone_id': zone.id, 'key': '!master'})

            zone.obj_reset_changes(['masters', 'attributes'])

        # TODO(Federico) refactor part of _find_zones into _find_zone, move
        # _load_relations out

        if one:
            _load_relations(zones)
        else:
            zones.total_count = self.count_zones(context, criterion)
            for d in zones:
                _load_relations(d)

        if one:
            LOG.debug('Fetched zone %s', zones)
        return zones

    def create_zone(self, context, zone):
        """
        Create a new Zone.

        :param context: RPC Context.
        :param zone: Zone object with the values to be created.
        """
        # Patch in the reverse_name column
        extra_values = {'reverse_name': zone.name[::-1]}

        # Don't handle recordsets for now
        zone = self._create(
            tables.zones, zone, exceptions.DuplicateZone,
            ['attributes', 'recordsets', 'masters'],
            extra_values=extra_values)

        if zone.obj_attr_is_set('attributes'):
            for attrib in zone.attributes:
                self.create_zone_attribute(context, zone.id, attrib)
        else:
            zone.attributes = objects.ZoneAttributeList()
        if zone.obj_attr_is_set('masters'):
            for master in zone.masters:
                self.create_zone_master(context, zone.id, master)
        else:
            zone.masters = objects.ZoneMasterList()
        zone.obj_reset_changes(['masters', 'attributes'])

        return zone

    def get_zone(self, context, zone_id, apply_tenant_criteria=True):
        """
        Get a Zone via its ID.

        :param context: RPC Context.
        :param zone_id: ID of the Zone.
        :param apply_tenant_criteria: Whether to filter results by project_id.
        """
        zone = self._find_zones(context, {'id': zone_id}, one=True,
                                apply_tenant_criteria=apply_tenant_criteria,
                                include_shared=True)
        return zone

    def find_zones(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):
        """
        Find zones

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        zones = self._find_zones(context, criterion, marker=marker,
                                 limit=limit, sort_key=sort_key,
                                 sort_dir=sort_dir, include_shared=True)
        return zones

    def find_zone(self, context, criterion):
        """
        Find a single Zone.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        zone = self._find_zones(context, criterion, one=True,
                                include_shared=True)
        return zone

    def update_zone(self, context, zone):
        """
        Update a Zone

        :param context: RPC Context.
        :param zone: Zone object.
        """
        tenant_id_changed = False
        if 'tenant_id' in zone.obj_what_changed():
            tenant_id_changed = True

        # Don't handle recordsets for now
        LOG.debug('Updating zone %s', zone)
        updated_zone = self._update(
            context, tables.zones, zone, exceptions.DuplicateZone,
            exceptions.ZoneNotFound,
            ['attributes', 'recordsets', 'masters'])

        if zone.obj_attr_is_set('attributes'):
            # Gather the Attribute ID's we have
            have = {r.id for r in self._find_zone_attributes(
                context, {'zone_id': zone.id})}

            # Prep some lists of changes
            keep = set()
            create = []
            update = []

            # Determine what to change
            for i in zone.attributes:
                keep.add(i.id)
                try:
                    i.obj_get_original_value('id')
                except KeyError:
                    create.append(i)
                else:
                    update.append(i)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete attribute is not needed.
            #       The original item will be mutated in place on the input
            #       "zone.attributes" list.

            # Delete Attributes
            for i_id in have - keep:
                attr = self._find_zone_attributes(
                    context, {'id': i_id}, one=True)
                self.delete_zone_attribute(context, attr.id)

            # Update Attributes
            for i in update:
                self.update_zone_attribute(context, i)

            # Create Attributes
            for attr in create:
                attr.zone_id = zone.id
                self.create_zone_attribute(context, zone.id, attr)

        if zone.obj_attr_is_set('masters'):
            # Gather the Attribute ID's we have
            have = {r.id for r in self._find_zone_masters(
                context, {'zone_id': zone.id})}

            # Prep some lists of changes
            keep = set()
            create = []
            update = []

            # Determine what to change
            for i in zone.masters:
                keep.add(i.id)
                try:
                    i.obj_get_original_value('id')
                except KeyError:
                    create.append(i)
                else:
                    update.append(i)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete attribute is not needed.
            #       The original item will be mutated in place on the input
            #       "zone.attributes" list.

            # Delete Attributes
            for i_id in have - keep:
                attr = self._find_zone_masters(
                    context, {'id': i_id}, one=True)
                self.delete_zone_master(context, attr.id)

            # Update Attributes
            for i in update:
                self.update_zone_master(context, i)

            # Create Attributes
            for attr in create:
                attr.zone_id = zone.id
                self.create_zone_master(context, zone.id, attr)

        if zone.obj_attr_is_set('recordsets'):
            existing = {}
            for rrset in self.find_recordsets(context, {'zone_id': zone.id}):
                existing[rrset.name, rrset.type] = rrset

            keep = set()
            for rrset in zone.recordsets:
                existing_recordset = existing.get((rrset.name, rrset.type))
                if existing_recordset:
                    existing_recordset.update(rrset)
                    existing_recordset.records = rrset.records
                    existing_recordset.obj_reset_changes(['zone_name'])
                    self.update_recordset(context, existing_recordset)
                    keep.add(existing_recordset.id)
                else:
                    self.create_recordset(context, zone.id, rrset)
                    keep.add(rrset.id)

            if zone.type == 'SECONDARY':
                # Purge anything that shouldn't be there :P
                for i in {i.id for i in existing.values()} - keep:
                    self.delete_recordset(context, i)

        if tenant_id_changed:
            with sql.get_write_session() as session:
                session.execute(
                    tables.recordsets.update().
                    where(tables.recordsets.c.zone_id == zone.id).
                    values({'tenant_id': zone.tenant_id})
                )

                session.execute(
                    tables.records.update().
                    where(tables.records.c.zone_id == zone.id).
                    values({'tenant_id': zone.tenant_id})
                )

        return updated_zone

    def increment_serial(self, context, zone_id):
        """Increment the zone's serial number.
        """
        new_serial = timeutils.utcnow_ts()
        query = tables.zones.update().where(
            tables.zones.c.id == zone_id).values(
            {'serial': new_serial, 'increment_serial': False}
        )
        with sql.get_write_session() as session:
            session.execute(query)
        LOG.debug('Incremented zone serial for %s to %d', zone_id, new_serial)
        return new_serial

    def delete_zone(self, context, zone_id):
        """
        Delete a Zone

        :param context: RPC Context.
        :param zone_id: Zone ID to delete.
        """
        # Fetch the existing zone, we'll need to return it.
        zone = self._find_zones(context, {'id': zone_id}, one=True)
        return self._delete(context, tables.zones, zone,
                            exceptions.ZoneNotFound)

    def purge_zone(self, context, zone):
        """
        Purge a Zone, effectively removing the zone database record.

        :param context: RPC Context.
        :param zone: Zone to delete.
        """
        return self._delete(context, tables.zones, zone,
                            exceptions.ZoneNotFound, hard_delete=True)

    def _walk_up_zones(self, current, zones_by_id):
        """Walk upwards in a zone hierarchy until we find a parent zone
        that does not belong to "zones_by_id"
        :returns: parent zone ID or None
        """
        max_steps = MAXIMUM_SUBZONE_DEPTH
        while current.parent_zone_id in zones_by_id:
            current = zones_by_id[current.parent_zone_id]
            max_steps -= 1
            if max_steps == 0:
                raise exceptions.IllegalParentZone('Loop detected in the'
                                                   ' zone hierarchy')

        return current.parent_zone_id

    def purge_zones(self, context, criterion, limit):
        """
        Purge Zones, effectively removing the zones database records.

        Reparent orphan childrens, if any.
        Transactions/locks are not needed.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param limit: Integer limit of objects of the page size after the
                      marker
        """
        if 'deleted' in criterion:
            context.show_deleted = True

        zones = self.find_zones(
            context=context,
            criterion=criterion,
            limit=limit,
        )
        if not zones:
            LOG.info('No zones to be purged')
            return

        LOG.debug('Purging %d zones', len(zones))

        zones_by_id = {z.id: z for z in zones}

        for zone in zones:

            # Reparent child zones, if any.
            surviving_parent_id = self._walk_up_zones(zone, zones_by_id)
            query = (
                tables.zones.update().
                where(tables.zones.c.parent_zone_id == zone.id).
                values(parent_zone_id=surviving_parent_id)
            )

            with sql.get_write_session() as session:
                resultproxy = session.execute(query)
                LOG.debug('%d child zones updated', resultproxy.rowcount)

            self.purge_zone(context, zone)

        LOG.info('Purged %d zones', len(zones))
        return len(zones)

    def count_zones(self, context, criterion=None):
        """
        Count zones

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        query = select(func.count(tables.zones.c.id))
        query = self._apply_criterion(tables.zones, query, criterion)
        query = self._apply_tenant_criteria(context, tables.zones, query)
        query = self._apply_deleted_criteria(context, tables.zones, query)

        with sql.get_read_session() as session:
            resultproxy = session.execute(query)
            result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Shared zones methods
    def _find_shared_zones(self, context, criterion, one=False, marker=None,
                           limit=None, sort_key=None, sort_dir=None):

        table = tables.shared_zones

        query = select(table)

        if not context.all_tenants:
            query = query.where(or_(
                table.c.project_id == context.project_id,
                table.c.target_project_id == context.project_id))

        return self._find(
            context, tables.shared_zones, objects.SharedZone,
            objects.SharedZoneList, exceptions.SharedZoneNotFound, criterion,
            one, marker, limit, sort_key, sort_dir, query=query,
            apply_tenant_criteria=False)

    def share_zone(self, context, shared_zone):
        """
        Share zone

        :param context: RPC Context.
        :param shared_zone: Shared Zone dict
        """
        return self._create(tables.shared_zones, shared_zone,
                            exceptions.DuplicateSharedZone)

    def unshare_zone(self, context, zone_id, shared_zone_id):
        """
        Unshare zone

        :param context: RPC Context.
        :param shared_zone_id: Shared Zone Id
        """
        shared_zone = self._find_shared_zones(
            context, {'id': shared_zone_id, 'zone_id': zone_id}, one=True
        )
        return self._delete(context, tables.shared_zones, shared_zone,
                            exceptions.SharedZoneNotFound)

    def find_shared_zones(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        """
        Find shared zones

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        return self._find_shared_zones(
            context, criterion, marker=marker,
            limit=limit, sort_key=sort_key, sort_dir=sort_dir
        )

    def get_shared_zone(self, context, zone_id, shared_zone_id):
        """
        Get a shared zone via ID

        :param context: RPC Context.
        :param shared_zone_id: Shared Zone Id
        """
        return self._find_shared_zones(
            context, {'id': shared_zone_id, 'zone_id': zone_id}, one=True
        )

    def is_zone_shared_with_project(self, zone_id, project_id):
        """
        Checks if a zone is shared with a project.

        :param zone_id: The zone ID to check.
        :param project_id: The project ID to check.
        :returns: Boolean True/False if the zone is shared with the project.
        """
        query = select(literal_column('true'))
        query = query.where(tables.shared_zones.c.zone_id == zone_id)
        query = query.where(
            tables.shared_zones.c.target_project_id == project_id)
        with sql.get_read_session() as session:
            return session.scalar(query) is not None

    def delete_zone_shares(self, zone_id):
        """
        Delete all of the zone shares for a specific zone.

        :param zone_id: The zone ID to check.
        """
        query = tables.shared_zones.delete().where(
            tables.shared_zones.c.zone_id == zone_id)
        with sql.get_write_session() as session:
            session.execute(query)

    # Zone attribute methods
    def _find_zone_attributes(self, context, criterion, one=False,
                              marker=None, limit=None, sort_key=None,
                              sort_dir=None):
        return self._find(context, tables.zone_attributes,
                          objects.ZoneAttribute, objects.ZoneAttributeList,
                          exceptions.ZoneAttributeNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_zone_attribute(self, context, zone_id, zone_attribute):
        zone_attribute.zone_id = zone_id
        return self._create(tables.zone_attributes, zone_attribute,
                            exceptions.DuplicateZoneAttribute)

    def get_zone_attributes(self, context, zone_attribute_id):
        return self._find_zone_attributes(
            context, {'id': zone_attribute_id}, one=True)

    def find_zone_attributes(self, context, criterion=None, marker=None,
                             limit=None, sort_key=None, sort_dir=None):
        return self._find_zone_attributes(context, criterion, marker=marker,
                                          limit=limit, sort_key=sort_key,
                                          sort_dir=sort_dir)

    def update_zone_attribute(self, context, zone_attribute):
        return self._update(context, tables.zone_attributes,
                            zone_attribute,
                            exceptions.DuplicateZoneAttribute,
                            exceptions.ZoneAttributeNotFound)

    def delete_zone_attribute(self, context, zone_attribute_id):
        zone_attribute = self._find_zone_attributes(
            context, {'id': zone_attribute_id}, one=True)
        deleted_zone_attribute = self._delete(
            context, tables.zone_attributes, zone_attribute,
            exceptions.ZoneAttributeNotFound)

        return deleted_zone_attribute

    # Zone master methods
    def _find_zone_masters(self, context, criterion, one=False,
                           marker=None, limit=None, sort_key=None,
                           sort_dir=None):

        return self._find(context, tables.zone_masters,
                          objects.ZoneMaster, objects.ZoneMasterList,
                          exceptions.ZoneMasterNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_zone_master(self, context, zone_id, zone_master):
        zone_master.zone_id = zone_id
        return self._create(tables.zone_masters, zone_master,
                            exceptions.DuplicateZoneMaster)

    def update_zone_master(self, context, zone_master):
        return self._update(context, tables.zone_masters,
                            zone_master,
                            exceptions.DuplicateZoneMaster,
                            exceptions.ZoneMasterNotFound)

    def delete_zone_master(self, context, zone_master_id):
        zone_master = self._find_zone_masters(
            context, {'id': zone_master_id}, one=True)
        deleted_zone_master = self._delete(
            context, tables.zone_masters, zone_master,
            exceptions.ZoneMasterNotFound)

        return deleted_zone_master

    # RecordSet Methods
    def _find_recordsets(self, context, criterion, one=False, marker=None,
                         limit=None, sort_key=None, sort_dir=None,
                         force_index=False, apply_tenant_criteria=True):

        # Check to see if the criterion can use the reverse_name column
        criterion = self._rname_check(criterion)

        if criterion is not None and not criterion.get('zones_deleted', True):
            # remove 'zones_deleted' from the criterion, as _apply_criterion
            # assumes each key in criterion to be a column name.
            del criterion['zones_deleted']

        if one:
            rjoin = tables.recordsets.join(
                tables.zones,
                tables.recordsets.c.zone_id == tables.zones.c.id)
            query = (
                select(tables.recordsets).select_from(rjoin).
                where(tables.zones.c.deleted == '0')
            )

            recordsets = self._find(
                context, tables.recordsets, objects.RecordSet,
                objects.RecordSetList, exceptions.RecordSetNotFound, criterion,
                one, marker, limit, sort_key, sort_dir, query,
                apply_tenant_criteria=apply_tenant_criteria,
            )

            recordsets.records = self._find_records(
                context, {'recordset_id': recordsets.id},
                apply_tenant_criteria=apply_tenant_criteria,
            )

            recordsets.obj_reset_changes(['records'])

        else:
            tc, recordsets = self._find_recordsets_with_records(
                    context, criterion, limit=limit, marker=marker,
                    sort_key=sort_key, sort_dir=sort_dir,
                    force_index=force_index,
                    apply_tenant_criteria=apply_tenant_criteria,
            )

            recordsets.total_count = tc

        return recordsets

    def find_recordsets_axfr(self, context, criterion=None):
        """
        Find RecordSets.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        # Check to see if the criterion can use the reverse_name column
        criterion = self._rname_check(criterion)

        rjoin = tables.records.join(
            tables.recordsets,
            tables.records.c.recordset_id == tables.recordsets.c.id)

        query = (
            select(tables.recordsets.c.id, tables.recordsets.c.type,
                   tables.recordsets.c.ttl, tables.recordsets.c.name,
                   tables.records.c.data, tables.records.c.action).
            select_from(rjoin).where(tables.records.c.action != 'DELETE')
        )

        query = query.order_by(tables.recordsets.c.id)

        raw_rows = self._select_raw(
            context, tables.recordsets, criterion, query)

        return raw_rows

    def create_recordset(self, context, zone_id, recordset):
        """
        Create a recordset on a given Zone ID

        :param context: RPC Context.
        :param zone_id: Zone ID to create the recordset in.
        :param recordset: RecordSet object with the values to be created.
        """
        recordset.tenant_id = context.project_id
        recordset.zone_id = zone_id

        # Patch in the reverse_name column
        extra_values = {'reverse_name': recordset.name[::-1]}

        recordset = self._create(
            tables.recordsets, recordset, exceptions.DuplicateRecordSet,
            ['records'], extra_values=extra_values)

        if recordset.obj_attr_is_set('records'):
            for record in recordset.records:
                # NOTE: Since we're dealing with a mutable object, the return
                #       value is not needed. The original item will be mutated
                #       in place on the input "recordset.records" list.
                self.create_record(context, zone_id, recordset.id, record)
        else:
            recordset.records = objects.RecordList()

        recordset.obj_reset_changes(['records'])

        return recordset

    def find_recordsets_export(self, context, criterion=None):
        query = None

        rjoin = tables.records.join(
            tables.recordsets,
            tables.records.c.recordset_id == tables.recordsets.c.id)

        query = (
            select(tables.recordsets.c.name, tables.recordsets.c.ttl,
                   tables.recordsets.c.type, tables.records.c.data).
            select_from(rjoin)
        )

        query = query.order_by(tables.recordsets.c.created_at)

        raw_rows = self._select_raw(
            context, tables.recordsets, criterion, query)

        return raw_rows

    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None, force_index=False,
                        apply_tenant_criteria=True):
        """
        Find RecordSets.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        :param apply_tenant_criteria: Whether to filter results by project_id.
        """
        return self._find_recordsets(
            context, criterion, marker=marker, sort_dir=sort_dir,
            sort_key=sort_key, limit=limit, force_index=force_index,
            apply_tenant_criteria=apply_tenant_criteria)

    def find_recordset(self, context, criterion, apply_tenant_criteria=True):
        """
        Find a single RecordSet.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param apply_tenant_criteria: Whether to filter results by project_id.
        """
        return self._find_recordsets(
            context, criterion, one=True,
            apply_tenant_criteria=apply_tenant_criteria)

    def update_recordset(self, context, recordset):
        """
        Update a recordset

        :param context: RPC Context.
        :param recordset: RecordSet to update
        """
        recordset = self._update(
            context, tables.recordsets, recordset,
            exceptions.DuplicateRecordSet, exceptions.RecordSetNotFound,
            ['records'])

        if recordset.obj_attr_is_set('records'):
            # Gather the Record ID's we have
            have_records = {r.id for r in self._find_records(
                context, {'recordset_id': recordset.id})}

            # Prep some lists of changes
            keep_records = set()
            create_records = []
            update_records = []

            # Determine what to change
            for record in recordset.records:
                keep_records.add(record.id)
                try:
                    record.obj_get_original_value('id')
                except KeyError:
                    create_records.append(record)
                else:
                    update_records.append(record)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete record is not needed. The original
            #       item will be mutated in place on the input
            #       "recordset.records" list.

            # Delete Records
            for record_id in have_records - keep_records:
                self.delete_record(context, record_id)

            # Update Records
            for record in update_records:
                self.update_record(context, record)

            # Create Records
            for record in create_records:
                self.create_record(
                    context, recordset.zone_id, recordset.id, record)

        return recordset

    def delete_recordset(self, context, recordset_id):
        """
        Delete a recordset

        :param context: RPC Context.
        :param recordset_id: RecordSet ID to delete
        """
        # Fetch the existing recordset, we'll need to return it.
        recordset = self._find_recordsets(
            context, {'id': recordset_id}, one=True)

        return self._delete(context, tables.recordsets, recordset,
                            exceptions.RecordSetNotFound)

    def count_recordsets(self, context, criterion=None):
        """
        Count recordsets

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        # Ensure that we return only active recordsets
        rjoin = tables.recordsets.join(
            tables.zones,
            tables.recordsets.c.zone_id == tables.zones.c.id)

        query = (
            select(func.count(tables.recordsets.c.id)).
            select_from(rjoin).
            where(tables.zones.c.deleted == '0')
        )

        query = self._apply_criterion(tables.recordsets, query, criterion)
        query = self._apply_tenant_criteria(context, tables.recordsets, query)
        query = self._apply_deleted_criteria(context, tables.recordsets, query)

        with sql.get_read_session() as session:
            resultproxy = session.execute(query)
            result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Record Methods
    def _find_records(self, context, criterion, one=False, marker=None,
                      limit=None, sort_key=None, sort_dir=None,
                      apply_tenant_criteria=True):
        return self._find(
            context, tables.records, objects.Record, objects.RecordList,
            exceptions.RecordNotFound, criterion, one, marker, limit,
            sort_key, sort_dir,
            apply_tenant_criteria=apply_tenant_criteria,
        )

    def _recalculate_record_hash(self, record):
        """
        Calculates the hash of the record, used to ensure record uniqueness.
        """
        md5sum = hashlib.md5(usedforsecurity=False)
        md5sum.update(('{}:{}'.format(record.recordset_id,
                                      record.data)).encode('utf-8'))

        return md5sum.hexdigest()

    def create_record(self, context, zone_id, recordset_id, record):
        """
        Create a record on a given Zone ID

        :param context: RPC Context.
        :param zone_id: Zone ID to create the record in.
        :param recordset_id: RecordSet ID to create the record in.
        :param record: Record object with the values to be created.
        """
        record.tenant_id = context.project_id
        record.zone_id = zone_id
        record.recordset_id = recordset_id
        record.hash = self._recalculate_record_hash(record)

        return self._create(
            tables.records, record, exceptions.DuplicateRecord)

    def get_record(self, context, record_id):
        """
        Get a record via ID

        :param context: RPC Context.
        :param record_id: Record ID to get
        """
        return self._find_records(context, {'id': record_id}, one=True)

    def find_records(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        """
        Find Records.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        return self._find_records(context, criterion, marker=marker,
                                  limit=limit, sort_key=sort_key,
                                  sort_dir=sort_dir)

    def find_record(self, context, criterion):
        """
        Find a single Record.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_records(context, criterion, one=True)

    def update_record(self, context, record):
        """
        Update a record

        :param context: RPC Context.
        :param record: Record to update
        """
        if record.obj_what_changed():
            record.hash = self._recalculate_record_hash(record)

        return self._update(
            context, tables.records, record, exceptions.DuplicateRecord,
            exceptions.RecordNotFound)

    def delete_record(self, context, record_id):
        """
        Delete a record

        :param context: RPC Context.
        :param record_id: Record ID to delete
        """
        # Fetch the existing record, we'll need to return it.
        record = self._find_records(context, {'id': record_id}, one=True)
        return self._delete(context, tables.records, record,
                            exceptions.RecordNotFound)

    def count_records(self, context, criterion=None):
        """
        Count records

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        # Ensure that we return only active records
        rjoin = tables.records.join(
            tables.zones,
            tables.records.c.zone_id == tables.zones.c.id)

        query = (
            select(func.count(tables.records.c.id)).
            select_from(rjoin).
            where(tables.zones.c.deleted == '0')
        )

        query = self._apply_criterion(tables.records, query, criterion)
        query = self._apply_tenant_criteria(context, tables.records, query)
        query = self._apply_deleted_criteria(context, tables.records, query)

        with sql.get_read_session() as session:
            resultproxy = session.execute(query)
            result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Blacklist Methods
    def _find_blacklists(self, context, criterion, one=False, marker=None,
                         limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.blacklists, objects.Blacklist,
            objects.BlacklistList, exceptions.BlacklistNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

    def create_blacklist(self, context, blacklist):
        """
        Create a Blacklist.

        :param context: RPC Context.
        :param blacklist: Blacklist object with the values to be created.
        """
        return self._create(
            tables.blacklists, blacklist, exceptions.DuplicateBlacklist)

    def get_blacklist(self, context, blacklist_id):
        """
        Get a Blacklist via ID.

        :param context: RPC Context.
        :param blacklist_id: Blacklist ID to get.
        """
        return self._find_blacklists(context, {'id': blacklist_id}, one=True)

    def find_blacklists(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        """
        Find Blacklists

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        return self._find_blacklists(context, criterion, marker=marker,
                                     limit=limit, sort_key=sort_key,
                                     sort_dir=sort_dir)

    def find_blacklist(self, context, criterion):
        """
        Find a single Blacklist.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_blacklists(context, criterion, one=True)

    def update_blacklist(self, context, blacklist):
        """
        Update a Blacklist

        :param context: RPC Context.
        :param blacklist: Blacklist to update.
        """
        return self._update(
            context, tables.blacklists, blacklist,
            exceptions.DuplicateBlacklist, exceptions.BlacklistNotFound)

    def delete_blacklist(self, context, blacklist_id):
        """
        Delete a Blacklist via ID.

        :param context: RPC Context.
        :param blacklist_id: Delete a Blacklist via ID
        """
        # Fetch the existing blacklist, we'll need to return it.
        blacklist = self._find_blacklists(
            context, {'id': blacklist_id}, one=True)

        return self._delete(context, tables.blacklists, blacklist,
                            exceptions.BlacklistNotFound)

    # Pool methods
    def _find_pools(self, context, criterion, one=False, marker=None,
                    limit=None, sort_key=None, sort_dir=None):
        pools = self._find(context, tables.pools, objects.Pool,
                           objects.PoolList, exceptions.PoolNotFound,
                           criterion, one, marker, limit, sort_key,
                           sort_dir)

        # Load Relations
        def _load_relations(pool):
            pool.attributes = self._find_pool_attributes(
                context, {'pool_id': pool.id})

            pool.ns_records = self._find_pool_ns_records(
                context, {'pool_id': pool.id})

            pool.nameservers = self._find_pool_nameservers(
                context, {'pool_id': pool.id})

            pool.targets = self._find_pool_targets(
                context, {'pool_id': pool.id})

            pool.also_notifies = self._find_pool_also_notifies(
                context, {'pool_id': pool.id})

            try:
                catalog_zone = self.get_catalog_zone(context, pool)

                try:
                    tsigkey = self.find_tsigkey(
                        context, criterion={'resource_id': catalog_zone.id})
                except exceptions.TsigKeyNotFound:
                    tsigkey = None

                secret = tsigkey.secret if tsigkey is not None else None
                algorithm = tsigkey.algorithm if tsigkey is not None else None

                pool.catalog_zone = objects.PoolCatalogZone(
                    catalog_zone_fqdn=catalog_zone.name,
                    catalog_zone_refresh=catalog_zone.refresh,
                    catalog_zone_tsig_key=secret,
                    catalog_zone_tsig_algorithm=algorithm,
                )
            except exceptions.ZoneNotFound:
                pool.catalog_zone = None

            pool.obj_reset_changes(['attributes', 'ns_records', 'nameservers',
                                    'targets', 'also_notifies', 'catalog_zone']
                                   )

        if one:
            _load_relations(pools)
        else:
            for pool in pools:
                _load_relations(pool)

        return pools

    def create_pool(self, context, pool):
        """
        Create a Pool.

        :param context: RPC Context.
        :param pool: Pool object with the values to be created.
        """
        pool = self._create(
            tables.pools, pool, exceptions.DuplicatePool,
            ['attributes', 'ns_records', 'nameservers', 'targets',
             'also_notifies', 'catalog_zone'])

        if pool.obj_attr_is_set('attributes'):
            for pool_attribute in pool.attributes:
                self.create_pool_attribute(context, pool.id, pool_attribute)
        else:
            pool.attributes = objects.PoolAttributeList()

        if pool.obj_attr_is_set('ns_records'):
            for ns_record in pool.ns_records:
                self.create_pool_ns_record(context, pool.id, ns_record)
        else:
            pool.ns_records = objects.PoolNsRecordList()

        if pool.obj_attr_is_set('nameservers'):
            for nameserver in pool.nameservers:
                self.create_pool_nameserver(context, pool.id, nameserver)
        else:
            pool.nameservers = objects.PoolNameserverList()

        if pool.obj_attr_is_set('targets'):
            for target in pool.targets:
                self.create_pool_target(context, pool.id, target)
        else:
            pool.targets = objects.PoolTargetList()

        if pool.obj_attr_is_set('also_notifies'):
            for also_notify in pool.also_notifies:
                self.create_pool_also_notify(context, pool.id, also_notify)
        else:
            pool.also_notifies = objects.PoolAlsoNotifyList()

        pool.obj_reset_changes(['attributes', 'ns_records', 'nameservers',
                                'targets', 'also_notifies'])

        self._ensure_catalog_zone_config(context, pool)

        return pool

    def get_pool(self, context, pool_id):
        """
        Get a Pool via the id

        :param context: RPC Context.
        :param pool_id: The ID of the pool to get
        """
        return self._find_pools(context, {'id': pool_id}, one=True)

    def find_pools(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        """
        Find all Pools

        :param context: RPC Context.
        :param criterion: Criteria by which to filter
        :param marker: Resource ID used by paging. The next page will start
                       at the next resource after the marker
        :param limit: Integer limit of objects on the page
        :param sort_key: Key used to sort the returned list
        :param sort_dir: Directions to sort after using sort_key
        """
        return self._find_pools(context, criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_pool(self, context, criterion):
        """
        Find a single Pool.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_pools(context, criterion, one=True)

    def update_pool(self, context, pool):
        """
        Update the specified pool

        :param context: RPC Context.
        :param pool: Pool to update.
        """
        pool = self._update(context, tables.pools, pool,
                            exceptions.DuplicatePool, exceptions.PoolNotFound,
                            ['attributes', 'ns_records', 'nameservers',
                             'targets', 'also_notifies', 'catalog_zone'])

        for attribute_name in ('attributes', 'ns_records', 'nameservers',
                               'targets', 'also_notifies'):
            if pool.obj_attr_is_set(attribute_name):
                self._update_pool_items(context, pool, attribute_name)

        # Call get_pool to get the ids of all the attributes/ns_records
        # refreshed in the pool object
        updated_pool = self.get_pool(context, pool.id)

        self._ensure_catalog_zone_config(context, pool)

        return updated_pool

    def delete_pool(self, context, pool_id):
        """
        Delete the pool with the matching id

        :param context: RPC Context.
        :param pool_id: The ID of the pool to be deleted
        """
        pool = self._find_pools(context, {'id': pool_id}, one=True)

        try:
            catalog_zone = self.get_catalog_zone(context, pool)

            try:
                catalog_zone_tsig = self.find_tsigkey(
                    context, criterion={'resource_id': catalog_zone.id})
                self.delete_tsigkey(context, catalog_zone_tsig.id)
            except exceptions.TsigKeyNotFound:
                pass

            self.delete_zone(context, catalog_zone.id)
        except exceptions.ZoneNotFound:
            pass

        return self._delete(context, tables.pools, pool,
                            exceptions.PoolNotFound)

    # Pool attribute methods
    def _find_pool_attributes(self, context, criterion, one=False, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        return self._find(context, tables.pool_attributes,
                          objects.PoolAttribute, objects.PoolAttributeList,
                          exceptions.PoolAttributeNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_attribute(self, context, pool_id, pool_attribute):
        """
        Create a PoolAttribute.

        :param context: RPC Context.
        :param pool_id: The ID of the pool to which the attribute belongs.
        :param pool_attribute: PoolAttribute object with the values created.
        """
        pool_attribute.pool_id = pool_id

        return self._create(tables.pool_attributes, pool_attribute,
                            exceptions.DuplicatePoolAttribute)

    def get_pool_attribute(self, context, pool_attribute_id):
        """
        Get a PoolAttribute via the ID

        :param context: RPC Context.
        :param pool_attribute_id: The ID of the PoolAttribute to get
        """
        return self._find_pool_attributes(
            context, {'id': pool_attribute_id}, one=True)

    def find_pool_attributes(self, context, criterion=None, marker=None,
                             limit=None, sort_key=None, sort_dir=None):
        """
        Find all PoolAttributes

        :param context: RPC Context
        :param criterion: Criteria by which to filer
        :param marker: Resource ID used by paging. The next page will start
                       at the next resource after the marker
        :param limit: Integer limit of objects on the page
        :param sort_key: Key used to sort the returned list
        :param sort_dir: Directions to sort after using sort_key
        """
        return self._find_pool_attributes(context, criterion, marker=marker,
                                          limit=limit, sort_key=sort_key,
                                          sort_dir=sort_dir)

    def find_pool_attribute(self, context, criterion):
        """
        Find a single PoolAttribute

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_pool_attributes(context, criterion, one=True)

    def update_pool_attribute(self, context, pool_attribute):
        """
        Update the specified pool

        :param context: RPC Context.
        :param pool_attribute: PoolAttribute to update
        """
        return self._update(context, tables.pool_attributes, pool_attribute,
                            exceptions.DuplicatePoolAttribute,
                            exceptions.PoolAttributeNotFound)

    def delete_pool_attribute(self, context, pool_attribute_id):
        """
        Delete the pool with the matching id

        :param context: RPC Context.
        :param pool_attribute_id: The ID of the PoolAttribute to be deleted
        """
        pool_attribute = self._find_pool_attributes(
            context, {'id': pool_attribute_id}, one=True)
        deleted_pool_attribute = self._delete(
            context, tables.pool_attributes, pool_attribute,
            exceptions.PoolAttributeNotFound)

        return deleted_pool_attribute

    # Pool ns_record methods
    def _find_pool_ns_records(self, context, criterion, one=False, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        return self._find(context, tables.pool_ns_records,
                          objects.PoolNsRecord, objects.PoolNsRecordList,
                          exceptions.PoolNsRecordNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_ns_record(self, context, pool_id, pool_ns_record):
        pool_ns_record.pool_id = pool_id

        return self._create(tables.pool_ns_records, pool_ns_record,
                            exceptions.DuplicatePoolNsRecord)

    def update_pool_ns_record(self, context, pool_ns_record):
        return self._update(context, tables.pool_ns_records, pool_ns_record,
                            exceptions.DuplicatePoolNsRecord,
                            exceptions.PoolNsRecordNotFound)

    def delete_pool_ns_record(self, context, pool_ns_record_id):
        pool_ns_record = self._find_pool_ns_records(
            context, {'id': pool_ns_record_id}, one=True)
        deleted_pool_ns_record = self._delete(
            context, tables.pool_ns_records, pool_ns_record,
            exceptions.PoolNsRecordNotFound)

        return deleted_pool_ns_record

    # PoolNameserver methods
    def _find_pool_nameservers(self, context, criterion, one=False,
                               marker=None, limit=None, sort_key=None,
                               sort_dir=None):
        return self._find(context, tables.pool_nameservers,
                          objects.PoolNameserver, objects.PoolNameserverList,
                          exceptions.PoolNameserverNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_nameserver(self, context, pool_id, pool_nameserver):
        pool_nameserver.pool_id = pool_id

        return self._create(tables.pool_nameservers, pool_nameserver,
                            exceptions.DuplicatePoolNameserver)

    def get_pool_nameserver(self, context, pool_nameserver_id):
        return self._find_pool_nameservers(
            context, {'id': pool_nameserver_id}, one=True)

    def find_pool_nameservers(self, context, criterion=None, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_nameservers(context, criterion, marker=marker,
                                           limit=limit, sort_key=sort_key,
                                           sort_dir=sort_dir)

    def find_pool_nameserver(self, context, criterion):
        return self._find_pool_nameservers(context, criterion, one=True)

    def update_pool_nameserver(self, context, pool_nameserver):
        return self._update(context, tables.pool_nameservers, pool_nameserver,
                            exceptions.DuplicatePoolNameserver,
                            exceptions.PoolNameserverNotFound)

    def delete_pool_nameserver(self, context, pool_nameserver_id):
        pool_nameserver = self._find_pool_nameservers(
            context, {'id': pool_nameserver_id}, one=True)
        deleted_pool_nameserver = self._delete(
            context, tables.pool_nameservers, pool_nameserver,
            exceptions.PoolNameserverNotFound)

        return deleted_pool_nameserver

    # PoolTarget methods
    def _find_pool_targets(self, context, criterion, one=False, marker=None,
                           limit=None, sort_key=None, sort_dir=None):
        pool_targets = self._find(
            context, tables.pool_targets, objects.PoolTarget,
            objects.PoolTargetList, exceptions.PoolTargetNotFound,
            criterion, one, marker, limit, sort_key,
            sort_dir)

        # Load Relations
        def _load_relations(pool_target):
            pool_target.options = self._find_pool_target_options(
                context, {'pool_target_id': pool_target.id})

            pool_target.masters = self._find_pool_target_masters(
                context, {'pool_target_id': pool_target.id})

            pool_target.obj_reset_changes(['options', 'masters'])

        if one:
            _load_relations(pool_targets)
        else:
            for pool_target in pool_targets:
                _load_relations(pool_target)

        return pool_targets

    def create_pool_target(self, context, pool_id, pool_target):
        pool_target.pool_id = pool_id

        pool_target = self._create(
            tables.pool_targets, pool_target, exceptions.DuplicatePoolTarget,
            ['options', 'masters'])

        if pool_target.obj_attr_is_set('options'):
            for pool_target_option in pool_target.options:
                self.create_pool_target_option(
                    context, pool_target.id, pool_target_option)
        else:
            pool_target.options = objects.PoolTargetOptionList()

        if pool_target.obj_attr_is_set('masters'):
            for pool_target_master in pool_target.masters:
                self.create_pool_target_master(
                    context, pool_target.id, pool_target_master)
        else:
            pool_target.masters = objects.PoolTargetMasterList()

        pool_target.obj_reset_changes(['options', 'masters'])

        return pool_target

    def get_pool_target(self, context, pool_target_id):
        return self._find_pool_targets(
            context, {'id': pool_target_id}, one=True)

    def find_pool_targets(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_targets(context, criterion, marker=marker,
                                       limit=limit, sort_key=sort_key,
                                       sort_dir=sort_dir)

    def find_pool_target(self, context, criterion):
        return self._find_pool_targets(context, criterion, one=True)

    def _update_pool_items(self, context, pool, attribute_name):
        """Update attributes beloging to a pool
        """
        assert attribute_name in ('attributes', 'ns_records', 'nameservers',
                                  'targets', 'also_notifies')

        # Gather the pool ID's we have
        finder = getattr(self, '_find_pool_%s' % attribute_name)
        have_items = set()
        for r in finder(context, {'pool_id': pool.id}):
            have_items.add(r.id)

        # Prep some lists of changes
        keep_items = set()
        create_items = []
        update_items = []

        items = []
        if pool.obj_attr_is_set(attribute_name):
            for r in getattr(pool, attribute_name).objects:
                items.append(r)

        # Determine what to change
        for item in items:
            keep_items.add(item.id)
            try:
                item.obj_get_original_value('id')
            except KeyError:
                create_items.append(item)
            else:
                update_items.append(item)

        # NOTE: Since we're dealing with mutable objects, the return value
        #       of create/update/delete option is not needed. The
        #       original item will be mutated in place on the input
        #       "pool.options" list.

        # singular: attributes -> attribute, 'notify' is as a corner case
        if attribute_name == 'also_notifies':
            singular = 'also_notify'
        else:
            singular = attribute_name[:-1]

        # Delete items
        fn = getattr(self, 'delete_pool_%s' % singular)
        for item_id in have_items - keep_items:
            fn(context, item_id)

        # Update items
        fn = getattr(self, 'update_pool_%s' % singular)
        for item in update_items:
            fn(context, item)

        # Create items
        fn = getattr(self, 'create_pool_%s' % singular)
        for item in create_items:
            fn(context, pool.id, item)

    def _update_pool_target_items(self, context, pool_target, attribute_name):
        """Update attributes beloging to a pool target
        """
        assert attribute_name in ('options', 'masters')

        # Gather the pool ID's we have
        finder = getattr(self, '_find_pool_target_%s' % attribute_name)
        have_items = set()
        for r in finder(context, {'pool_target_id': pool_target.id}):
            have_items.add(r.id)

        # Prep some lists of changes
        keep_items = set()
        create_items = []
        update_items = []

        items = []
        if pool_target.obj_attr_is_set(attribute_name):
            for r in getattr(pool_target, attribute_name).objects:
                items.append(r)

        # Determine what to change
        for item in items:
            keep_items.add(item.id)
            try:
                item.obj_get_original_value('id')
            except KeyError:
                create_items.append(item)
            else:
                update_items.append(item)

        # NOTE: Since we're dealing with mutable objects, the return value
        #       of create/update/delete option is not needed. The
        #       original item will be mutated in place on the input
        #       "pool.options" list.

        # singular: options -> option
        singular = attribute_name[:-1]

        # Delete items
        fn = getattr(self, 'delete_pool_target_%s' % singular)
        for item_id in have_items - keep_items:
            fn(context, item_id)

        # Update items
        fn = getattr(self, 'update_pool_target_%s' % singular)
        for item in update_items:
            fn(context, item)

        # Create items
        fn = getattr(self, 'create_pool_target_%s' % singular)
        for item in create_items:
            fn(context, pool_target.id, item)

    def update_pool_target(self, context, pool_target):
        pool_target = self._update(
            context, tables.pool_targets, pool_target,
            exceptions.DuplicatePoolTarget, exceptions.PoolTargetNotFound,
            ['options', 'masters'])

        for attribute_name in ('options', 'masters'):
            if pool_target.obj_attr_is_set(attribute_name):
                self._update_pool_target_items(context, pool_target,
                                               attribute_name)

        # Call get_pool to get the ids of all the attributes/ns_records
        # refreshed in the pool object
        updated_pool_target = self.get_pool_target(context, pool_target.id)

        return updated_pool_target

    def delete_pool_target(self, context, pool_target_id):
        pool_target = self._find_pool_targets(
            context, {'id': pool_target_id}, one=True)

        return self._delete(context, tables.pool_targets, pool_target,
                            exceptions.PoolTargetNotFound)

    # PoolTargetOption methods
    def _find_pool_target_options(self, context, criterion, one=False,
                                  marker=None, limit=None, sort_key=None,
                                  sort_dir=None):
        return self._find(
            context, tables.pool_target_options,
            objects.PoolTargetOption, objects.PoolTargetOptionList,
            exceptions.PoolTargetOptionNotFound, criterion, one,
            marker, limit, sort_key, sort_dir)

    def create_pool_target_option(self, context, pool_target_id,
                                  pool_target_option):
        pool_target_option.pool_target_id = pool_target_id

        return self._create(tables.pool_target_options, pool_target_option,
                            exceptions.DuplicatePoolTargetOption)

    def update_pool_target_option(self, context, pool_target_option):
        return self._update(
            context, tables.pool_target_options, pool_target_option,
            exceptions.DuplicatePoolTargetOption,
            exceptions.PoolTargetOptionNotFound)

    def delete_pool_target_option(self, context, pool_target_option_id):
        pool_target_option = self._find_pool_target_options(
            context, {'id': pool_target_option_id}, one=True)
        deleted_pool_target_option = self._delete(
            context, tables.pool_target_options, pool_target_option,
            exceptions.PoolTargetOptionNotFound)

        return deleted_pool_target_option

    # PoolTargetMaster methods
    def _find_pool_target_masters(self, context, criterion, one=False,
                                  marker=None, limit=None, sort_key=None,
                                  sort_dir=None):
        return self._find(
            context, tables.pool_target_masters,
            objects.PoolTargetMaster, objects.PoolTargetMasterList,
            exceptions.PoolTargetMasterNotFound, criterion, one,
            marker, limit, sort_key, sort_dir)

    def create_pool_target_master(self, context, pool_target_id,
                                  pool_target_master):
        pool_target_master.pool_target_id = pool_target_id

        return self._create(tables.pool_target_masters, pool_target_master,
                            exceptions.DuplicatePoolTargetMaster)

    def update_pool_target_master(self, context, pool_target_master):
        return self._update(
            context, tables.pool_target_masters, pool_target_master,
            exceptions.DuplicatePoolTargetMaster,
            exceptions.PoolTargetMasterNotFound)

    def delete_pool_target_master(self, context, pool_target_master_id):
        pool_target_master = self._find_pool_target_masters(
            context, {'id': pool_target_master_id}, one=True)
        deleted_pool_target_master = self._delete(
            context, tables.pool_target_masters, pool_target_master,
            exceptions.PoolTargetMasterNotFound)

        return deleted_pool_target_master

    # PoolAlsoNotify methods
    def _find_pool_also_notifies(self, context, criterion, one=False,
                                 marker=None, limit=None, sort_key=None,
                                 sort_dir=None):
        return self._find(context, tables.pool_also_notifies,
                          objects.PoolAlsoNotify, objects.PoolAlsoNotifyList,
                          exceptions.PoolAlsoNotifyNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_also_notify(self, context, pool_id, pool_also_notify):
        pool_also_notify.pool_id = pool_id

        return self._create(tables.pool_also_notifies, pool_also_notify,
                            exceptions.DuplicatePoolAlsoNotify)

    def get_pool_also_notify(self, context, pool_also_notify_id):
        return self._find_pool_also_notifies(
            context, {'id': pool_also_notify_id}, one=True)

    def find_pool_also_notifies(self, context, criterion=None, marker=None,
                                limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_also_notifies(context, criterion, marker=marker,
                                             limit=limit, sort_key=sort_key,
                                             sort_dir=sort_dir)

    def find_pool_also_notify(self, context, criterion):
        return self._find_pool_also_notifies(context, criterion, one=True)

    def update_pool_also_notify(self, context, pool_also_notify):
        return self._update(
            context, tables.pool_also_notifies, pool_also_notify,
            exceptions.DuplicatePoolAlsoNotify,
            exceptions.PoolAlsoNotifyNotFound)

    def delete_pool_also_notify(self, context, pool_also_notify_id):
        pool_also_notify = self._find_pool_also_notifies(
            context, {'id': pool_also_notify_id}, one=True)
        deleted_pool_also_notify = self._delete(
            context, tables.pool_also_notifies, pool_also_notify,
            exceptions.PoolAlsoNotifyNotFound)

        return deleted_pool_also_notify

    # Zone Transfer Methods
    def _find_zone_transfer_requests(self, context, criterion, one=False,
                                     marker=None, limit=None, sort_key=None,
                                     sort_dir=None):

        table = tables.zone_transfer_requests

        ljoin = tables.zone_transfer_requests.join(
            tables.zones,
            tables.zone_transfer_requests.c.zone_id == tables.zones.c.id)

        query = select(
            table, tables.zones.c.name.label('zone_name')
        ).select_from(ljoin)

        if not context.all_tenants:
            # If we have a system scoped token with no project_id and
            # all_tenants was not used, we don't know what records to return,
            # so return an empty list.
            if not context.project_id:
                if one:
                    return objects.ZoneTransferRequest()
                return objects.ZoneTransferRequestList()

            query = query.where(or_(
                table.c.tenant_id == context.project_id,
                table.c.target_tenant_id == context.project_id))

        return self._find(
            context, table, objects.ZoneTransferRequest,
            objects.ZoneTransferRequestList,
            exceptions.ZoneTransferRequestNotFound,
            criterion,
            one=one, marker=marker, limit=limit, sort_dir=sort_dir,
            sort_key=sort_key, query=query,
            apply_tenant_criteria=False
        )

    def create_zone_transfer_request(self, context, zone_transfer_request):

        try:
            criterion = {'zone_id': zone_transfer_request.zone_id,
                         'status': 'ACTIVE'}
            self.find_zone_transfer_request(
                context, criterion)
        except exceptions.ZoneTransferRequestNotFound:
            return self._create(
                tables.zone_transfer_requests,
                zone_transfer_request,
                exceptions.DuplicateZoneTransferRequest)
        else:
            raise exceptions.DuplicateZoneTransferRequest()

    def find_zone_transfer_requests(self, context, criterion=None,
                                    marker=None, limit=None, sort_key=None,
                                    sort_dir=None):

        return self._find_zone_transfer_requests(
            context, criterion, marker=marker,
            limit=limit, sort_key=sort_key,
            sort_dir=sort_dir)

    def get_zone_transfer_request(self, context, zone_transfer_request_id):
        request = self._find_zone_transfer_requests(
            context,
            {'id': zone_transfer_request_id},
            one=True)

        return request

    def find_zone_transfer_request(self, context, criterion):

        return self._find_zone_transfer_requests(context, criterion, one=True)

    def update_zone_transfer_request(self, context, zone_transfer_request):

        zone_transfer_request.obj_reset_changes('zone_name')

        updated_zt_request = self._update(
            context,
            tables.zone_transfer_requests,
            zone_transfer_request,
            exceptions.DuplicateZoneTransferRequest,
            exceptions.ZoneTransferRequestNotFound,
            skip_values=['zone_name'])

        return updated_zt_request

    def delete_zone_transfer_request(self, context, zone_transfer_request_id):

        zone_transfer_request = self._find_zone_transfer_requests(
            context,
            {'id': zone_transfer_request_id},
            one=True)

        return self._delete(
            context,
            tables.zone_transfer_requests,
            zone_transfer_request,
            exceptions.ZoneTransferRequestNotFound)

    def count_zone_transfer_accept(self, context, criterion=None):
        query = select(func.count(tables.zone_transfer_accepts.c.id))
        query = self._apply_criterion(
            tables.zone_transfer_accepts, query, criterion
        )
        query = self._apply_deleted_criteria(
            context, tables.zone_transfer_accepts, query
        )

        with sql.get_read_session() as session:
            resultproxy = session.execute(query)
            result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    def _find_zone_transfer_accept(self, context, criterion, one=False,
                                   marker=None, limit=None, sort_key=None,
                                   sort_dir=None):

        zone_transfer_accept = self._find(
            context, tables.zone_transfer_accepts,
            objects.ZoneTransferAccept,
            objects.ZoneTransferAcceptList,
            exceptions.ZoneTransferAcceptNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

        if not one:
            zone_transfer_accept.total_count = self.count_zone_transfer_accept(
                context, criterion)

        return zone_transfer_accept

    def create_zone_transfer_accept(self, context, zone_transfer_accept):

        return self._create(
            tables.zone_transfer_accepts,
            zone_transfer_accept,
            exceptions.DuplicateZoneTransferAccept)

    def find_zone_transfer_accepts(self, context, criterion=None,
                                   marker=None, limit=None, sort_key=None,
                                   sort_dir=None):
        return self._find_zone_transfer_accept(
            context, criterion, marker=marker, limit=limit, sort_key=sort_key,
            sort_dir=sort_dir)

    def get_zone_transfer_accept(self, context, zone_transfer_accept_id):
        return self._find_zone_transfer_accept(
            context,
            {'id': zone_transfer_accept_id},
            one=True)

    def find_zone_transfer_accept(self, context, criterion):
        return self._find_zone_transfer_accept(
            context,
            criterion,
            one=True)

    def update_zone_transfer_accept(self, context, zone_transfer_accept):

        return self._update(
            context,
            tables.zone_transfer_accepts,
            zone_transfer_accept,
            exceptions.DuplicateZoneTransferAccept,
            exceptions.ZoneTransferAcceptNotFound)

    def delete_zone_transfer_accept(self, context, zone_transfer_accept_id):

        zone_transfer_accept = self._find_zone_transfer_accept(
            context,
            {'id': zone_transfer_accept_id},
            one=True)

        return self._delete(
            context,
            tables.zone_transfer_accepts,
            zone_transfer_accept,
            exceptions.ZoneTransferAcceptNotFound)

    # Zone Import Methods
    def _find_zone_imports(self, context, criterion, one=False, marker=None,
                           limit=None, sort_key=None, sort_dir=None):
        if not criterion:
            criterion = {}
        criterion['task_type'] = 'IMPORT'
        zone_imports = self._find(
            context, tables.zone_tasks, objects.ZoneImport,
            objects.ZoneImportList, exceptions.ZoneImportNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

        if not one:
            zone_imports.total_count = self.count_zone_tasks(
                context, criterion)

        return zone_imports

    def create_zone_import(self, context, zone_import):
        """
        Create a Zone Import.

        :param context: RPC Context.
        :param zone_import: Zone Import object with the values to be created.
        """
        return self._create(
            tables.zone_tasks, zone_import, exceptions.DuplicateZoneImport)

    def get_zone_import(self, context, zone_import_id):
        """
        Get a Zone Import via ID.

        :param context: RPC Context.
        :param zone_import_id: Zone Import ID to get.
        """
        return self._find_zone_imports(context, {'id': zone_import_id},
                                       one=True)

    def find_zone_imports(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        """
        Find Zone Imports

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        return self._find_zone_imports(context, criterion, marker=marker,
                                       limit=limit, sort_key=sort_key,
                                       sort_dir=sort_dir)

    def find_zone_import(self, context, criterion):
        """
        Find a single Zone Import.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_zone_imports(context, criterion, one=True)

    def update_zone_import(self, context, zone_import):
        """
        Update a Zone Import

        :param context: RPC Context.
        :param zone_import: Zone Import to update.
        """
        return self._update(
            context, tables.zone_tasks, zone_import,
            exceptions.DuplicateZoneImport, exceptions.ZoneImportNotFound)

    def delete_zone_import(self, context, zone_import_id):
        """
        Delete a Zone Import via ID.

        :param context: RPC Context.
        :param zone_import_id: Delete a Zone Import via ID
        """
        # Fetch the existing zone_import, we'll need to return it.
        zone_import = self._find_zone_imports(context, {'id': zone_import_id},
                                              one=True)
        return self._delete(context, tables.zone_tasks, zone_import,
                            exceptions.ZoneImportNotFound)

    # Zone Export Methods
    def _find_zone_exports(self, context, criterion, one=False, marker=None,
                           limit=None, sort_key=None, sort_dir=None):
        if not criterion:
            criterion = {}
        criterion['task_type'] = 'EXPORT'
        zone_exports = self._find(
            context, tables.zone_tasks, objects.ZoneExport,
            objects.ZoneExportList, exceptions.ZoneExportNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)
        if not one:
            zone_exports.total_count = self.count_zone_tasks(
                context, criterion)

        return zone_exports

    def create_zone_export(self, context, zone_export):
        """
        Create a Zone Export.

        :param context: RPC Context.
        :param zone_export: Zone Export object with the values to be created.
        """
        return self._create(
            tables.zone_tasks, zone_export, exceptions.DuplicateZoneExport)

    def get_zone_export(self, context, zone_export_id):
        """
        Get a Zone Export via ID.

        :param context: RPC Context.
        :param zone_export_id: Zone Export ID to get.
        """
        return self._find_zone_exports(context, {'id': zone_export_id},
                                       one=True)

    def find_zone_exports(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        """
        Find Zone Exports

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        return self._find_zone_exports(context, criterion, marker=marker,
                                       limit=limit, sort_key=sort_key,
                                       sort_dir=sort_dir)

    def find_zone_export(self, context, criterion):
        """
        Find a single Zone Export.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_zone_exports(context, criterion, one=True)

    def update_zone_export(self, context, zone_export):
        """
        Update a Zone Export

        :param context: RPC Context.
        :param zone_export: Zone Export to update.
        """
        return self._update(
            context, tables.zone_tasks, zone_export,
            exceptions.DuplicateZoneExport, exceptions.ZoneExportNotFound)

    def delete_zone_export(self, context, zone_export_id):
        """
        Delete a Zone Export via ID.

        :param context: RPC Context.
        :param zone_export_id: Delete a Zone Export via ID
        """
        # Fetch the existing zone_export, we'll need to return it.
        zone_export = self._find_zone_exports(context, {'id': zone_export_id},
                                              one=True)
        return self._delete(context, tables.zone_tasks, zone_export,
                            exceptions.ZoneExportNotFound)

    def count_zone_tasks(self, context, criterion=None):
        query = select(func.count(tables.zone_tasks.c.id))
        query = self._apply_criterion(tables.zone_tasks, query, criterion)
        query = self._apply_tenant_criteria(context, tables.zone_tasks, query)
        query = self._apply_deleted_criteria(context, tables.zone_tasks, query)

        with sql.get_read_session() as session:
            resultproxy = session.execute(query)
            result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Service Status Methods
    def _find_service_statuses(self, context, criterion, one=False,
                               marker=None, limit=None, sort_key=None,
                               sort_dir=None):
        return self._find(
            context, tables.service_status, objects.ServiceStatus,
            objects.ServiceStatusList, exceptions.ServiceStatusNotFound,
            criterion, one, marker, limit, sort_key, sort_dir)

    def find_service_status(self, context, criterion):
        """
        Find a single Service Status.

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        """
        return self._find_service_statuses(context, criterion, one=True)

    def find_service_statuses(self, context, criterion=None, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        """
        Retrieve status for services

        :param context: RPC Context.
        :param criterion: Criteria to filter by.
        :param marker: Resource ID from which after the requested page will
                       start after
        :param limit: Integer limit of objects of the page size after the
                      marker
        :param sort_key: Key from which to sort after.
        :param sort_dir: Direction to sort after using sort_key.
        """
        return self._find_service_statuses(context, criterion, marker=marker,
                                           limit=limit, sort_key=sort_key,
                                           sort_dir=sort_dir)

    def create_service_status(self, context, service_status):
        """
        Create a Service status for a service.

        :param context: RPC Context.
        :param service_status: The status of a service.
        """
        return self._create(
            tables.service_status, service_status,
            exceptions.DuplicateServiceStatus)

    def update_service_status(self, context, service_status):
        """
        Update the Service status for a service.

        :param context: RPC Context.
        :param service_status: Set the status for a service.
        """
        return self._update(
            context, tables.service_status, service_status,
            exceptions.DuplicateServiceStatus,
            exceptions.ServiceStatusNotFound)

    # Reverse Name utils
    def _rname_check(self, criterion):
        # If the criterion has 'name' in it, switch it out for reverse_name
        if criterion is not None and criterion.get('name', '').startswith('*'):
            criterion['reverse_name'] = criterion.pop('name')[::-1]
        return criterion

    def _create_catalog_zone(self, pool):
        catalog_zone = objects.Zone(
            name=pool.catalog_zone.catalog_zone_fqdn,
            email=CONF[
                'service:central'].managed_resource_email,
            refresh=pool.catalog_zone.catalog_zone_refresh,
            serial=1,
            pool_id=pool.id,
            type=constants.ZONE_CATALOG
        )
        return catalog_zone

    def get_catalog_zone(self, context, pool):
        catalog_zone = self.find_zone(
            context, criterion={
                'pool_id': pool.id, 'type': constants.ZONE_CATALOG})
        return catalog_zone

    def _ensure_catalog_zone_config(self, context, pool):
        if (
            not pool.obj_attr_is_set("catalog_zone") or
            pool.catalog_zone is None
        ):
            return

        try:
            self.get_catalog_zone(context, pool)
        except exceptions.ZoneNotFound:
            catalog_zone = self._create_catalog_zone(pool)
            self.create_zone(context, catalog_zone)

        self._ensure_catalog_zone_consistent(context, pool)

    def _ensure_catalog_zone_consistent(self, context, pool):
        """
        Ensure a catalog zone's data as defined in pools.yaml is consistent
        with its values in the database.

        :param context: RPC Context.
        :param pool: The pool to ensure catalog zone consistency for.
        """
        if not pool.obj_attr_is_set("catalog_zone") or not pool.catalog_zone:
            return

        catalog_zone = self.get_catalog_zone(context, pool)
        catalog_zone.attributes = self._find_zone_attributes(
                context, {'zone_id': catalog_zone.id})

        catalog_zone = self._ensure_catalog_zone_info_consistent(
            context, catalog_zone, pool.catalog_zone) or catalog_zone
        self._ensure_catalog_zone_soa_consistent(context, catalog_zone, pool)
        self._ensure_catalog_zone_tsig_data_consistent(
            context, catalog_zone, pool.catalog_zone)

    def _ensure_catalog_zone_info_consistent(
            self, context, catalog_zone, values):
        """
        Ensure a catalog zone's FQDN and refresh interval as defined in
        pools.yaml are consistent with their values in the database.

        :param context: RPC Context.
        :param catalog_zone: The catalog zone to ensure consistency for.
        :param values: The catalog zone values as defined in pools.yaml.
        """
        if (
            not catalog_zone.attributes or
            catalog_zone.attributes.get('catalog_zone_fqdn') !=
            values.catalog_zone_fqdn or
            catalog_zone.attributes.get('catalog_zone_refresh') !=
            values.catalog_zone_refresh
        ):
            catalog_zone.attributes = objects.ZoneAttributeList()
            catalog_zone_fqdn = objects.ZoneAttribute()
            catalog_zone_fqdn.zone_id = catalog_zone.id
            catalog_zone_fqdn.key = 'catalog_zone_fqdn'
            catalog_zone_fqdn.value = values.catalog_zone_fqdn

            catalog_zone_refresh = objects.ZoneAttribute()
            catalog_zone_refresh.zone_id = catalog_zone.id
            catalog_zone_refresh.key = 'catalog_zone_refresh'
            catalog_zone_refresh.value = values.catalog_zone_refresh
            catalog_zone.attributes.append(catalog_zone_fqdn)
            catalog_zone.attributes.append(catalog_zone_refresh)

            return self.update_zone(context, catalog_zone)

    def _ensure_catalog_zone_soa_consistent(self, context, catalog_zone, pool):
        """
        Ensure a catalog zone's SOA based on the values in pools.yaml is
        consistent with its values in the database.

        :param context: RPC Context.
        :param catalog_zone: The catalog zone to ensure consistency for.
        :param pool: The catalog_zone's pool.
        """
        soa_record = objects.RecordList()
        soa_record.append(
            objects.Record(
                    data=f'{pool.ns_records[0]["hostname"]} '
                    f'{catalog_zone.attributes.get("catalog_zone_fqdn")} '
                    f'{catalog_zone.serial} '
                    f'{catalog_zone.attributes.get("catalog_zone_refresh")} '
                    f'{catalog_zone.retry} '
                    '2147483646 '
                    f'{catalog_zone.minimum}'
            )
        )
        soa = objects.RecordSet(
            name=catalog_zone.name,
            type='SOA',
            records=soa_record
        )

        try:
            soa_db = self.find_recordset(
                context, criterion={'zone_id': catalog_zone.id, 'type': 'SOA'})
            soa_db.name = catalog_zone.name
            soa_db.records = soa_record
            self.update_recordset(context, soa_db)
        except exceptions.RecordSetNotFound:
            self.create_recordset(context, catalog_zone.id, soa)

    def _ensure_catalog_zone_tsig_data_consistent(
            self, context, catalog_zone, values):
        """
        Ensure a catalog zone's TSIG key and TSIG algorithm as defined in
        pools.yaml are consistent with their values in the database.

        :param context: RPC Context.
        :param catalog_zone: The catalog zone to ensure consistency for.
        :param values: The catalog zone values as defined in pools.yaml.
        """
        if (
            not values.catalog_zone_tsig_key or not
            values.catalog_zone_tsig_algorithm
        ):
            return

        tsig_key = values.catalog_zone_tsig_key
        tsig_algorithm = values.catalog_zone_tsig_algorithm

        try:
            tsigkey = self.find_tsigkey(
                context, criterion={'resource_id': catalog_zone.id})

            if (
                tsigkey.name !=
                    catalog_zone.attributes.get('catalog_zone_fqdn') or
                    tsigkey.secret != tsig_key or
                    tsigkey.algorithm != tsig_algorithm
            ):
                tsigkey.name = catalog_zone.attributes.get('catalog_zone_fqdn')
                tsigkey.secret = tsig_key
                tsigkey.algorithm = tsig_algorithm
                self.update_tsigkey(context, tsigkey)
        except exceptions.TsigKeyNotFound:
            tsigkey = objects.TsigKey(
                name=catalog_zone.attributes.get('catalog_zone_fqdn'),
                secret=tsig_key,
                algorithm=tsig_algorithm,
                scope='ZONE',
                resource_id=catalog_zone.id,
            )
            tsigkey = DesignateAdapter.parse(
                'API_v2', tsigkey, objects.TsigKey())
            tsigkey.validate()
            self.create_tsigkey(context, tsigkey)

    def get_catalog_zone_records(self, context, pool):
        catalog_zone = self.get_catalog_zone(context, pool)
        zones = self.find_zones(
            context, criterion={'pool_id': pool.id, 'type': '!CATALOG'})
        soa_record = self.find_recordset(
            context, criterion={'zone_id': catalog_zone.id, 'type': 'SOA'})
        records = []

        # Catalog zones require one NS record using NSDNAME 'invalid.'
        # per RFC 9432
        ns_record = objects.RecordList()
        ns_record.append(objects.Record(data='invalid.'))
        records.append(
            objects.RecordSet(
                name=pool.catalog_zone.catalog_zone_fqdn,
                type='NS',
                records=ns_record
            )
        )

        # Catalog zones require a TXT record with the schema version,
        # currently '2' per RFC 9432
        txt_record = objects.RecordList()
        txt_record.append(objects.Record(data='2'))
        records.append(
            objects.RecordSet(
                name=f'version.{pool.catalog_zone.catalog_zone_fqdn}',
                type='TXT',
                records=txt_record
            )
        )

        for z in zones:
            # If member zone is scheduled for deletion, do not include it in
            # catalog. Otherwise, zone poller will wait for zone's deletion on
            # secondary DNS servers, which will not happen since the zone is
            # still in catalog (deadlock).
            if z.action == 'DELETE':
                continue

            rs = objects.RecordList()
            rs.append(
                objects.Record(
                    data=z.name
                )
            )
            record = objects.RecordSet(
                name=f'{z.id}.zones.{soa_record.name}',
                type='PTR',
                records=rs
            )
            records.append(record)

        records.insert(0, soa_record)
        records.append(soa_record)

        return records

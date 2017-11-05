# Copyright 2015 Infoblox Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import gettext

from oslo_log import log

from designate.backend.impl_infoblox import ibexceptions as exc

_ = gettext.gettext

LOG = log.getLogger(__name__)


class InfobloxObjectManipulator(object):
    FIELDS = ['ttl', 'use_ttl']

    def __init__(self, connector):
        self.connector = connector

    def get_member(self, member_name):
        obj = {'host_name': member_name[0:-1]}
        return self.connector.get_object('member', obj)

    def create_dns_view(self, net_view_name, dns_view_name):
        dns_view_data = {'name': dns_view_name,
                         'network_view': net_view_name}
        return self._create_infoblox_object('view', dns_view_data)

    def delete_dns_view(self, net_view_name):
        net_view_data = {'name': net_view_name}
        self._delete_infoblox_object('view', net_view_data)

    def create_network_view(self, net_view_name, tenant_id):
        net_view_data = {'name': net_view_name}
        extattrs = {'extattrs': {'TenantID': {'value': tenant_id}}}
        return self._create_infoblox_object('networkview',
                                            net_view_data, extattrs)

    def delete_network_view(self, net_view_name):
        if net_view_name == 'default':
            # never delete default network view
            return

        net_view_data = {'name': net_view_name}
        self._delete_infoblox_object('networkview', net_view_data)

    def create_tsig(self, name, algorithm, secret):
        tsig = {
            'name': name,
            'key': secret
        }
        self._create_infoblox_object(
            'tsig', tsig,
            check_if_exists=True)

    def delete_tsig(self, name, algorithm, secret):
        tsig = {
            'name': name,
            'key': secret
        }
        self._delete_infoblox_object(
            'tsig', tsig,
            check_if_exists=True)

    def create_multi_tenant_dns_view(self, net_view, tenant):
        if not net_view:
            net_view = "%s.%s" % (self.connector.network_view, tenant)
        dns_view = "%s.%s" % (self.connector.dns_view, net_view)

        try:
            self.create_network_view(
                net_view_name=net_view,
                tenant_id=tenant)

            self.create_dns_view(
                net_view_name=net_view,
                dns_view_name=dns_view)
        except exc.InfobloxException as e:
            LOG.warning(_("Issue happens during views creating: %s"), e)

        LOG.debug("net_view: %s, dns_view: %s" % (net_view, dns_view))
        return dns_view

    def get_dns_view(self, tenant):
        if not self.connector.multi_tenant:
            return self.connector.dns_view
        else:
            # Look for the network view with the specified TenantID EA
            net_view = self._get_infoblox_object_or_none(
                'networkview',
                return_fields=['name'],
                extattrs={'TenantID': {'value': tenant}})
            if net_view:
                net_view = net_view['name']

            return self.create_multi_tenant_dns_view(net_view, tenant)

    def create_zone_auth(self, fqdn, dns_view):
        try:
            if fqdn.endswith("in-addr.arpa"):
                zone_format = 'IPV4'
            elif fqdn.endswith("ip6.arpa"):
                zone_format = 'IPV6'
            else:
                zone_format = 'FORWARD'
            self._create_infoblox_object(
                'zone_auth',
                {'fqdn': fqdn, 'view': dns_view},
                {'ns_group': self.connector.ns_group,
                 'restart_if_needed': True, 'zone_format': zone_format},
                check_if_exists=True)
        except exc.InfobloxCannotCreateObject as e:
            LOG.warning(e)

    def delete_zone_auth(self, fqdn):
        self._delete_infoblox_object(
            'zone_auth', {'fqdn': fqdn})

    def _create_infoblox_object(self, obj_type, payload,
                                additional_create_kwargs=None,
                                check_if_exists=True,
                                return_fields=None):
        if additional_create_kwargs is None:
            additional_create_kwargs = {}

        ib_object = None
        if check_if_exists:
            ib_object = self._get_infoblox_object_or_none(obj_type, payload)
            if ib_object:
                LOG.info(_(
                    "Infoblox %(obj_type)s already exists: %(ib_object)s"),
                    {'obj_type': obj_type, 'ib_object': ib_object})

        if not ib_object:
            payload.update(additional_create_kwargs)
            ib_object = self.connector.create_object(obj_type, payload,
                                                     return_fields)
            LOG.info(_("Infoblox %(obj_type)s was created: %(ib_object)s"),
                     {'obj_type': obj_type, 'ib_object': ib_object})

        return ib_object

    def _get_infoblox_object_or_none(self, obj_type, payload=None,
                                     return_fields=None, extattrs=None):
        ib_object = self.connector.get_object(obj_type, payload, return_fields,
                                              extattrs=extattrs)
        if ib_object:
            if return_fields:
                return ib_object[0]
            else:
                return ib_object[0]['_ref']

        return None

    def _update_infoblox_object(self, obj_type, payload, update_kwargs):
        ib_object_ref = None
        warn_msg = _('Infoblox %(obj_type)s will not be updated because'
                     ' it cannot be found: %(payload)s')
        try:
            ib_object_ref = self._get_infoblox_object_or_none(obj_type,
                                                              payload)
            if not ib_object_ref:
                LOG.warning(warn_msg % {'obj_type': obj_type,
                                        'payload': payload})
        except exc.InfobloxSearchError as e:
            LOG.warning(warn_msg, {'obj_type': obj_type, 'payload': payload})
            LOG.info(e)

        if ib_object_ref:
            self._update_infoblox_object_by_ref(ib_object_ref, update_kwargs)

    def _update_infoblox_object_by_ref(self, ref, update_kwargs):
        self.connector.update_object(ref, update_kwargs)
        LOG.info(_('Infoblox object was updated: %s'), ref)

    def _delete_infoblox_object(self, obj_type, payload):
        ib_object_ref = None
        warn_msg = _('Infoblox %(obj_type)s will not be deleted because'
                     ' it cannot be found: %(payload)s')
        try:
            ib_object_ref = self._get_infoblox_object_or_none(obj_type,
                                                              payload)
            if not ib_object_ref:
                LOG.warning(warn_msg, {'obj_type': obj_type,
                                       'payload': payload})
        except exc.InfobloxSearchError as e:
            LOG.warning(warn_msg, {'obj_type': obj_type, 'payload': payload})
            LOG.info(e)

        if ib_object_ref:
            self.connector.delete_object(ib_object_ref)
            LOG.info(_('Infoblox object was deleted: %s'), ib_object_ref)

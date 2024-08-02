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
import copy

from keystoneauth1.access import service_catalog as ksa_service_catalog
from keystoneauth1 import plugin
from oslo_context import context
from oslo_log import log as logging

from designate import policy

LOG = logging.getLogger(__name__)


class DesignateContext(context.RequestContext):

    _all_tenants = False
    _hide_counts = False
    _abandon = None
    original_project_id = None
    _edit_managed_records = False
    _hard_delete = False
    _client_addr = None
    _delete_shares = False
    FROM_DICT_EXTRA_KEYS = [
        'original_project_id', 'service_catalog', 'all_tenants', 'abandon',
        'edit_managed_records', 'tsigkey_id', 'hide_counts', 'client_addr',
        'hard_delete', 'delete_shares'
    ]

    def __init__(self, service_catalog=None, all_tenants=False, abandon=None,
                 tsigkey_id=None, original_project_id=None,
                 edit_managed_records=False, hide_counts=False,
                 client_addr=None, user_auth_plugin=None,
                 hard_delete=False, delete_shares=False, **kwargs):
        super().__init__(**kwargs)

        self.user_auth_plugin = user_auth_plugin
        self.service_catalog = service_catalog
        self.tsigkey_id = tsigkey_id

        self.original_project_id = original_project_id

        self.all_tenants = all_tenants
        self.abandon = abandon
        self.edit_managed_records = edit_managed_records
        self.hard_delete = hard_delete
        self.hide_counts = hide_counts
        self.client_addr = client_addr
        self.delete_shares = delete_shares

    def deepcopy(self):
        return self.from_dict(self.to_dict())

    def to_dict(self):
        d = super().to_dict()

        # Override the user_identity field to account for TSIG. When a TSIG key
        # is used as authentication e.g. via MiniDNS, it will act as a form
        # of "user",
        user = self.user_id or '-'

        if self.tsigkey_id and not self.user_id:
            user = 'TSIG:%s' % self.tsigkey_id

        user_idt = (
            self.user_idt_format.format(
                user=user,
                project_id=self.project_id or '-',
                domain=self.domain_id or '-',
                user_domain=self.user_domain_id or '-',
                p_domain=self.project_domain_id or '-')
        )

        # Update the dict with Designate specific extensions and overrides
        d.update({
            'user_identity': user_idt,
            'original_project_id': self.original_project_id,
            'service_catalog': self.service_catalog,
            'all_tenants': self.all_tenants,
            'abandon': self.abandon,
            'edit_managed_records': self.edit_managed_records,
            'hard_delete': self.hard_delete,
            'tsigkey_id': self.tsigkey_id,
            'hide_counts': self.hide_counts,
            'client_addr': self.client_addr,
            'delete_shares': self.delete_shares,
        })

        return copy.deepcopy(d)

    def elevated(self, show_deleted=None, all_tenants=False,
                 edit_managed_records=False, hard_delete=False):
        """Return a version of this context with admin flag set.
        Optionally set all_tenants and edit_managed_records
        """
        context = self.deepcopy()
        context.is_admin = True

        # NOTE(kiall): Ugly - required to match http://tinyurl.com/o3y8qmw
        context.roles.append('admin')

        if show_deleted is not None:
            context.show_deleted = show_deleted

        if all_tenants:
            context.all_tenants = True

        if edit_managed_records:
            context.edit_managed_records = True

        if hard_delete:
            context.hard_delete = True

        return context

    def sudo(self, project_id):

        policy.check('use_sudo', self)

        LOG.info('Accepted sudo from user %(user)s to project_id %(project)s',
                 {'user': self.user_id, 'project': project_id})
        self.original_project_id = self.project_id
        self.project_id = project_id

    @classmethod
    def get_admin_context(cls, **kwargs):
        # TODO(kiall): Remove Me
        kwargs['is_admin'] = True
        kwargs['roles'] = ['admin', 'reader']

        return cls(None, **kwargs)

    @property
    def all_tenants(self):
        return self._all_tenants

    @all_tenants.setter
    def all_tenants(self, value):
        if value:
            policy.check('all_tenants', self)
        self._all_tenants = value

    @property
    def hide_counts(self):
        return self._hide_counts

    @hide_counts.setter
    def hide_counts(self, value):
        self._hide_counts = value

    @property
    def abandon(self):
        return self._abandon

    @abandon.setter
    def abandon(self, value):
        if value:
            policy.check('abandon_zone', self)
        self._abandon = value

    @property
    def edit_managed_records(self):
        return self._edit_managed_records

    @edit_managed_records.setter
    def edit_managed_records(self, value):
        if value:
            policy.check('edit_managed_records', self)
        self._edit_managed_records = value

    @property
    def hard_delete(self):
        return self._hard_delete

    @hard_delete.setter
    def hard_delete(self, value):
        if value:
            policy.check('hard_delete', self)
        self._hard_delete = value

    @property
    def client_addr(self):
        return self._client_addr

    @client_addr.setter
    def client_addr(self, value):
        self._client_addr = value

    @property
    def delete_shares(self):
        return self._delete_shares

    @delete_shares.setter
    def delete_shares(self, value):
        self._delete_shares = value

    def get_auth_plugin(self):
        if self.user_auth_plugin:
            return self.user_auth_plugin
        return _ContextAuthPlugin(self.auth_token, self.service_catalog)


class _ContextAuthPlugin(plugin.BaseAuthPlugin):
    """A keystoneauth auth plugin that uses the values from the Context.
    Ideally we would use the plugin provided by auth_token middleware however
    this plugin isn't serialized yet, so we construct one from the serialized
    auth data.
    """
    def __init__(self, auth_token, sc):
        super().__init__()

        self.auth_token = auth_token
        self.service_catalog = ksa_service_catalog.ServiceCatalogV2(sc)

    def get_token(self, *args, **kwargs):
        return self.auth_token

    def get_endpoint(self, session, service_type=None, interface=None,
                     region_name=None, service_name=None, **kwargs):
        endpoint = self.service_catalog.url_for(
            service_type=service_type, service_name=service_name,
            interface=interface, region_name=region_name
        )
        return self.get_endpoint_data(session, endpoint_override=endpoint).url


def get_current():
    return context.get_current()

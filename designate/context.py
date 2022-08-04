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
    _client_addr = None
    FROM_DICT_EXTRA_KEYS = [
        'original_project_id', 'service_catalog', 'all_tenants', 'abandon',
        'edit_managed_records', 'tsigkey_id', 'hide_counts', 'client_addr',
    ]

    def __init__(self, service_catalog=None, all_tenants=False, abandon=None,
                 tsigkey_id=None, original_project_id=None,
                 edit_managed_records=False, hide_counts=False,
                 client_addr=None, user_auth_plugin=None, **kwargs):
        super(DesignateContext, self).__init__(**kwargs)

        self.user_auth_plugin = user_auth_plugin
        self.service_catalog = service_catalog
        self.tsigkey_id = tsigkey_id

        self.original_project_id = original_project_id

        self.all_tenants = all_tenants
        self.abandon = abandon
        self.edit_managed_records = edit_managed_records
        self.hide_counts = hide_counts
        self.client_addr = client_addr

    def deepcopy(self):
        d = self.to_dict()

        return self.from_dict(d)

    def to_dict(self):
        d = super(DesignateContext, self).to_dict()

        # Override the user_identity field to account for TSIG. When a TSIG key
        # is used as authentication e.g. via MiniDNS, it will act as a form
        # of "user",
        user = self.user_id or '-'

        if self.tsigkey_id and not self.user_id:
            user = 'TSIG:%s' % self.tsigkey_id

        user_idt = (
            self.user_idt_format.format(
                user=user,
                # TODO(johnsom) Remove tenant once oslo.context>=4.0.0 is
                #               the lower bound version.
                tenant=self.project_id or '-',
                project_id=self.project_id or '-',
                domain=self.domain_id or '-',
                user_domain=self.user_domain_id or '-',
                p_domain=self.project_domain_id or '-')
        )

        # Update the dict with Designate specific extensions and overrides
        d.update({
            # TODO(johnsom) Remove project_id once oslo.context>=4.0.0 is
            #               the lower bound version.
            'project_id': self.project_id,
            'user_identity': user_idt,
            'original_project_id': self.original_project_id,
            'service_catalog': self.service_catalog,
            'all_tenants': self.all_tenants,
            'abandon': self.abandon,
            'edit_managed_records': self.edit_managed_records,
            'tsigkey_id': self.tsigkey_id,
            'hide_counts': self.hide_counts,
            'client_addr': self.client_addr,
        })

        return copy.deepcopy(d)

    def elevated(self, show_deleted=None, all_tenants=False,
                 edit_managed_records=False):
        """Return a version of this context with admin flag set.
        Optionally set all_tenants and edit_managed_records
        """
        context = self.deepcopy()
        context.is_admin = True

        # NOTE(kiall): Ugly - required to match http://tinyurl.com/o3y8qmw
        context.roles.append('admin')
        if policy.enforce_new_defaults():
            context.system_scope = 'all'

        if show_deleted is not None:
            context.show_deleted = show_deleted

        if all_tenants:
            context.all_tenants = True

        if edit_managed_records:
            context.edit_managed_records = True

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
        kwargs['system_scope'] = 'all'

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
    def client_addr(self):
        return self._client_addr

    @client_addr.setter
    def client_addr(self, value):
        self._client_addr = value

    def get_auth_plugin(self):
        if self.user_auth_plugin:
            return self.user_auth_plugin
        else:
            return _ContextAuthPlugin(self.auth_token, self.service_catalog)


class _ContextAuthPlugin(plugin.BaseAuthPlugin):
    """A keystoneauth auth plugin that uses the values from the Context.
    Ideally we would use the plugin provided by auth_token middleware however
    this plugin isn't serialized yet so we construct one from the serialized
    auth data.
    """
    def __init__(self, auth_token, sc):
        super(_ContextAuthPlugin, self).__init__()

        self.auth_token = auth_token
        self.service_catalog = ksa_service_catalog.ServiceCatalogV2(sc)

    def get_token(self, *args, **kwargs):
        return self.auth_token

    def get_endpoint(self, session, **kwargs):
        endpoint_data = self.get_endpoint_data(session, **kwargs)
        if not endpoint_data:
            return None
        return endpoint_data.url

    def get_endpoint_data(self, session,
                          endpoint_override=None,
                          discover_versions=True,
                          **kwargs):
        urlkw = {}
        for k in ('service_type', 'service_name', 'service_id', 'endpoint_id',
                  'region_name', 'interface'):
            if k in kwargs:
                urlkw[k] = kwargs[k]

        endpoint = endpoint_override or self.service_catalog.url_for(**urlkw)
        return super(_ContextAuthPlugin, self).get_endpoint_data(
            session, endpoint_override=endpoint,
            discover_versions=discover_versions, **kwargs)


def get_current():
    return context.get_current()

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
import itertools
import copy

from oslo_context import context
from oslo_log import log as logging

from designate import policy
from designate.i18n import _LI

LOG = logging.getLogger(__name__)


class DesignateContext(context.RequestContext):

    _all_tenants = False
    _hide_counts = False
    _abandon = None
    original_tenant = None
    _edit_managed_records = False
    _client_addr = None

    def __init__(self, service_catalog=None, all_tenants=False, abandon=None,
                 tsigkey_id=None, user_identity=None, original_tenant=None,
                 edit_managed_records=False, hide_counts=False,
                 client_addr=None, **kwargs):

        # NOTE: user_identity may be passed in, but will be silently dropped as
        #       it is a generated field based on several others.
        super(DesignateContext, self).__init__(**kwargs)

        self.service_catalog = service_catalog
        self.tsigkey_id = tsigkey_id

        self.original_tenant = original_tenant

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
        user = self.user or '-'

        if self.tsigkey_id and not self.user:
            user = 'TSIG:%s' % self.tsigkey_id

        user_idt = (
            self.user_idt_format.format(user=user,
                                        tenant=self.tenant or '-',
                                        domain=self.domain or '-',
                                        user_domain=self.user_domain or '-',
                                        p_domain=self.project_domain or '-'))

        # Update the dict with Designate specific extensions and overrides
        d.update({
            'user_identity': user_idt,
            'original_tenant': self.original_tenant,
            'service_catalog': self.service_catalog,
            'all_tenants': self.all_tenants,
            'abandon': self.abandon,
            'edit_managed_records': self.edit_managed_records,
            'tsigkey_id': self.tsigkey_id,
            'hide_counts': self.hide_counts,
            'client_addr': self.client_addr,
        })

        return copy.deepcopy(d)

    @classmethod
    def from_dict(cls, values):
        return cls(**values)

    def elevated(self, show_deleted=None, all_tenants=False,
                 edit_managed_records=False):
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

        return context

    def sudo(self, tenant):

        policy.check('use_sudo', self)

        LOG.info(_LI('Accepted sudo from user %(user)s to tenant %(tenant)s'),
                 {'user': self.user, 'tenant': tenant})
        self.original_tenant = self.tenant
        self.tenant = tenant

    @classmethod
    def get_admin_context(cls, **kwargs):
        # TODO(kiall): Remove Me
        kwargs['is_admin'] = True
        kwargs['roles'] = ['admin']

        return cls(None, **kwargs)

    @classmethod
    def get_context_from_function_and_args(cls, function, args, kwargs):
        """
        Find an arg of type DesignateContext and return it.

        This is useful in a couple of decorators where we don't
        know much about the function we're wrapping.
        """

        for arg in itertools.chain(kwargs.values(), args):
            if isinstance(arg, cls):
                return arg

        return None

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


def get_current():
    return context.get_current()

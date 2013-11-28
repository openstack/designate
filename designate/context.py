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
from designate.openstack.common import context
from designate.openstack.common import log as logging
from designate import policy

LOG = logging.getLogger(__name__)


class DesignateContext(context.RequestContext):
    def __init__(self, auth_token=None, user=None, tenant=None, is_admin=False,
                 read_only=False, show_deleted=False, request_id=None,
                 original_tenant_id=None, roles=[], service_catalog=None):
        super(DesignateContext, self).__init__(
            auth_token=auth_token,
            user=user,
            tenant=tenant,
            is_admin=is_admin,
            read_only=read_only,
            show_deleted=show_deleted,
            request_id=request_id)

        self._original_tenant_id = original_tenant_id
        self.roles = roles
        self.service_catalog = service_catalog

    def sudo(self, tenant_id, force=False):
        if force:
            allowed_sudo = True
        else:
            # We use exc=None here since the context is built early in the
            # request lifecycle, outside of our ordinary error handling.
            # For now, we silently ignore failed sudo requests.
            target = {'tenant_id': tenant_id}
            allowed_sudo = policy.check('use_sudo', self, target, exc=None)

        if allowed_sudo:
            LOG.warn('Accepted sudo from user_id %s for tenant_id %s'
                     % (self.user_id, tenant_id))
            self.original_tenant_id = self.tenant_id
            self.tenant_id = tenant_id

        else:
            LOG.warn('Rejected sudo from user_id %s for tenant_id %s'
                     % (self.user_id, tenant_id))

    def deepcopy(self):
        d = self.to_dict()

        # Remove the user and tenant id fields, this map to user and tenant
        d.pop('user_id')
        d.pop('tenant_id')

        return self.from_dict(d)

    def to_dict(self):
        d = super(DesignateContext, self).to_dict()

        d.update({
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'original_tenant_id': self.original_tenant_id,
            'roles': self.roles,
            'service_catalog': self.service_catalog
        })

        return d

    @classmethod
    def from_dict(cls, values):
        return cls(**values)

    def elevated(self, show_deleted=None):
        """Return a version of this context with admin flag set."""
        context = self.deepcopy()
        context.is_admin = True

        # NOTE(kiall): Ugly - required to match http://tinyurl.com/o3y8qmw
        context.roles.append('admin')

        if show_deleted is not None:
            context.show_deleted = show_deleted

        return context

    @property
    def user_id(self):
        return self.user

    @user_id.setter
    def user_id(self, value):
        self.user = value

    @property
    def tenant_id(self):
        return self.tenant

    @tenant_id.setter
    def tenant_id(self, value):
        self.tenant = value

    @property
    def original_tenant_id(self):
        if self._original_tenant_id:
            return self._original_tenant_id
        else:
            return self.tenant

    @original_tenant_id.setter
    def original_tenant_id(self, value):
        self._original_tenant_id = value

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

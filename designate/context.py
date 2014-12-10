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

from designate.openstack.common import local
from designate.openstack.common import log as logging
from designate import policy


LOG = logging.getLogger(__name__)


class DesignateContext(context.RequestContext):

    _all_tenants = False

    def __init__(self, auth_token=None, user=None, tenant=None, domain=None,
                 user_domain=None, project_domain=None, is_admin=False,
                 read_only=False, show_deleted=False, request_id=None,
                 resource_uuid=None, roles=None, service_catalog=None,
                 all_tenants=False, user_identity=None):
        # NOTE: user_identity may be passed in, but will be silently dropped as
        #       it is a generated field based on several others.

        roles = roles or []
        super(DesignateContext, self).__init__(
            auth_token=auth_token,
            user=user,
            tenant=tenant,
            domain=domain,
            user_domain=user_domain,
            project_domain=project_domain,
            is_admin=is_admin,
            read_only=read_only,
            show_deleted=show_deleted,
            request_id=request_id,
            resource_uuid=resource_uuid)

        self.roles = roles
        self.service_catalog = service_catalog

        self.all_tenants = all_tenants

        if not hasattr(local.store, 'context'):
            self.update_store()

    def update_store(self):
        local.store.context = self

    def deepcopy(self):
        d = self.to_dict()

        return self.from_dict(d)

    def to_dict(self):
        d = super(DesignateContext, self).to_dict()

        d.update({
            'roles': self.roles,
            'service_catalog': self.service_catalog,
            'all_tenants': self.all_tenants,
        })

        return copy.deepcopy(d)

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

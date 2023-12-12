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
import flask
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_middleware import base
from oslo_middleware import request_id
from oslo_serialization import jsonutils
from oslo_utils import strutils
import webob.dec

import designate.conf
from designate import context
from designate import exceptions
from designate import notifications
from designate import objects
from designate.objects.adapters import DesignateAdapter


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


def auth_pipeline_factory(loader, global_conf, **local_conf):
    """
    A paste pipeline replica that keys off of auth_strategy.

    Code nabbed from cinder.
    """
    pipeline = local_conf[CONF['service:api'].auth_strategy]
    pipeline = pipeline.split()
    LOG.info('Getting auth pipeline: %s', pipeline[:-1])
    filters = [loader.get_filter(n) for n in pipeline[:-1]]
    app = loader.get_app(pipeline[-1])
    filters.reverse()
    for filter in filters:
        app = filter(app)
    return app


class ContextMiddleware(base.Middleware):
    @staticmethod
    def _extract_sudo(ctxt, request):
        if request.headers.get('X-Auth-Sudo-Project-ID'):
            ctxt.sudo(request.headers.get('X-Auth-Sudo-Project-ID'))
        elif request.headers.get('X-Auth-Sudo-Tenant-ID'):
            ctxt.sudo(request.headers.get('X-Auth-Sudo-Tenant-ID'))

    @staticmethod
    def _extract_all_projects(ctxt, request):
        ctxt.all_tenants = False
        if request.headers.get('X-Auth-All-Projects'):
            value = request.headers.get('X-Auth-All-Projects')
            ctxt.all_tenants = strutils.bool_from_string(value)

        for name in ('all_projects', 'all_tenants', ):
            if name in request.GET:
                value = request.GET.pop(name)
                ctxt.all_tenants = strutils.bool_from_string(value)

    @staticmethod
    def _extract_dns_hide_counts(ctxt, request):
        ctxt.hide_counts = False
        value = request.headers.get('OpenStack-DNS-Hide-Counts')
        if value:
            ctxt.hide_counts = strutils.bool_from_string(value)

    @staticmethod
    def _extract_edit_managed_records(ctxt, request):
        ctxt.edit_managed_records = False
        if 'edit_managed_records' in request.GET:
            value = request.GET.pop('edit_managed_records')
            ctxt.edit_managed_records = strutils.bool_from_string(value)
        elif request.headers.get('X-Designate-Edit-Managed-Records'):
            ctxt.edit_managed_records = strutils.bool_from_string(
                request.headers.get('X-Designate-Edit-Managed-Records')
            )

    @staticmethod
    def _extract_hard_delete(ctxt, request):
        ctxt.hard_delete = False
        if request.headers.get('X-Designate-Hard-Delete'):
            ctxt.hard_delete = strutils.bool_from_string(
                request.headers.get('X-Designate-Hard-Delete')
            )

    @staticmethod
    def _extract_client_addr(ctxt, request):
        if hasattr(request, 'client_addr'):
            ctxt.client_addr = request.client_addr

    @staticmethod
    def _extract_delete_shares(ctxt, request):
        ctxt.delete_shares = False
        if request.headers.get('X-Designate-Delete-Shares'):
            ctxt.delete_shares = strutils.bool_from_string(
                request.headers.get('X-Designate-Delete-Shares')
            )

    def make_context(self, request, *args, **kwargs):
        req_id = request.environ.get(request_id.ENV_REQUEST_ID)
        kwargs.setdefault('request_id', req_id)

        ctxt = context.DesignateContext(*args, **kwargs)

        try:
            self._extract_sudo(ctxt, request)
            self._extract_all_projects(ctxt, request)
            self._extract_edit_managed_records(ctxt, request)
            self._extract_hard_delete(ctxt, request)
            self._extract_dns_hide_counts(ctxt, request)
            self._extract_client_addr(ctxt, request)
            self._extract_delete_shares(ctxt, request)
        finally:
            request.environ['context'] = ctxt
        return ctxt


class KeystoneContextMiddleware(ContextMiddleware):
    def __init__(self, application):
        super().__init__(application)

        LOG.info('Starting designate keystonecontext middleware')

    def process_request(self, request):
        headers = request.headers

        try:
            if headers['X-Identity-Status'] == 'Invalid':
                # TODO(graham) fix the return to use non-flask resources
                return flask.Response(status=401)
        except KeyError:
            # If the key is valid, Keystone does not include this header at all
            pass

        tenant_id = headers.get('X-Tenant-ID')

        catalog = None
        if headers.get('X-Service-Catalog'):
            catalog = jsonutils.loads(headers.get('X-Service-Catalog'))

        roles = headers.get('X-Roles').split(',')
        system_scope = headers.get('Openstack-System-Scope')

        try:
            self.make_context(
                request,
                auth_token=headers.get('X-Auth-Token'),
                user_id=headers.get('X-User-ID'),
                project_id=tenant_id,
                roles=roles,
                service_catalog=catalog,
                system_scope=system_scope
            )
        except exceptions.Forbidden:
            return flask.Response(status=403)


class NoAuthContextMiddleware(ContextMiddleware):
    def __init__(self, application):
        super().__init__(application)

        LOG.info('Starting designate noauthcontext middleware')

    def process_request(self, request):
        headers = request.headers

        self.make_context(
            request,
            auth_token=headers.get('X-Auth-Token'),
            user_id=headers.get('X-Auth-User-ID', 'noauth-user'),
            project_id=headers.get('X-Auth-Project-ID', 'noauth-project'),
            roles=headers.get('X-Roles', 'admin').split(',')
        )


class TestContextMiddleware(ContextMiddleware):
    def __init__(self, application, tenant_id=None, user_id=None):
        super().__init__(application)

        LOG.critical('Starting designate testcontext middleware')
        LOG.critical('**** DO NOT USE IN PRODUCTION ****')

        self.default_tenant_id = tenant_id
        self.default_user_id = user_id

    def process_request(self, request):
        headers = request.headers

        all_tenants = strutils.bool_from_string(
            headers.get('X-Test-All-Tenants', 'False')
        )

        role_header = headers.get('X-Test-Role', None)
        role_header = role_header.lower() if role_header else None
        if role_header == 'admin':
            roles = ['admin', 'member', 'reader']
        elif role_header == 'member':
            roles = ['member', 'reader']
        elif role_header == 'reader':
            roles = ['reader']
        else:
            roles = []

        self.make_context(
            request,
            user_id=headers.get('X-Test-User-ID', self.default_user_id),
            project_id=headers.get('X-Test-Tenant-ID', self.default_tenant_id),
            all_tenants=all_tenants, roles=roles
        )


class MaintenanceMiddleware(base.Middleware):
    def __init__(self, application):
        super().__init__(application)

        LOG.info('Starting designate maintenance middleware')

        self.enabled = CONF['service:api'].maintenance_mode
        self.role = CONF['service:api'].maintenance_mode_role

    def process_request(self, request):
        # If maintaince mode is not enabled, pass the request on as soon as
        # possible
        if not self.enabled:
            return None

        # If the caller has the bypass role, let them through
        if ('context' in request.environ and
                self.role in request.environ['context'].roles):
            LOG.warning('Request authorized to bypass maintenance mode')
            return None

        # Otherwise, reject the request with a 503 Service Unavailable
        return flask.Response(status=503, headers={'Retry-After': 60})


class NormalizeURIMiddleware(base.Middleware):
    @webob.dec.wsgify
    def __call__(self, request):
        # Remove any trailing /'s.
        request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')

        return request.get_response(self.application)


class FaultWrapperMiddleware(base.Middleware):
    def __init__(self, application):
        super().__init__(application)

        LOG.info('Starting designate faultwrapper middleware')

    @webob.dec.wsgify
    def __call__(self, request):
        try:
            return request.get_response(self.application)
        except exceptions.DesignateException as e:
            # Handle Designate Exceptions
            status = e.error_code if hasattr(e, 'error_code') else 500

            # Start building up a response
            response = {
                'code': status
            }

            if e.error_type:
                response['type'] = e.error_type

            if e.error_message:
                response['message'] = e.error_message

            if e.errors:
                response['errors'] = e.errors

            return self._handle_exception(request, e, status, response)
        except messaging.MessagingTimeout as e:
            # Special case for RPC timeout's
            response = {
                'code': 504,
                'type': 'timeout',
            }

            return self._handle_exception(request, e, 504, response)
        except Exception as e:
            # Handle all other exception types
            return self._handle_exception(request, e)

    def _format_error(self, data):
        pass

    def _handle_exception(self, request, e, status=500, response=None):
        response = response or {}
        # Log the exception ASAP unless it is a 404 Not Found
        if not getattr(e, 'expected', False):
            LOG.exception(e)

        headers = [
            ('Content-Type', 'application/json'),
        ]

        url = getattr(request, 'url', None)

        # Set a response code and type, if they are missing.
        if 'code' not in response:
            response['code'] = status

        if 'type' not in response:
            response['type'] = 'unknown'

        self._format_error(response)

        # Return the new response
        if 'context' in request.environ:
            response['request_id'] = request.environ['context'].request_id

            notifications.send_api_fault(request.environ['context'], url,
                                         response['code'], e)
        else:
            # TODO(ekarlso): Remove after verifying that there's actually a
            # context always set
            LOG.error('Missing context in request, please check.')

        return flask.Response(status=status, headers=headers,
                              response=jsonutils.dump_as_bytes(response))


class APIv2ValidationErrorMiddleware(base.Middleware):

    def __init__(self, application):
        super().__init__(application)
        self.api_version = 'API_v2'
        LOG.info('Starting designate validation middleware')

    @webob.dec.wsgify
    def __call__(self, request):
        try:
            return request.get_response(self.application)
        except exceptions.InvalidObject as e:
            # Allow current views validation to pass through to FaultWapper
            if not isinstance(e.errors, objects.ValidationErrorList):
                raise
            return self._handle_errors(request, e)

    def _handle_errors(self, request, exception):
        response = {}

        headers = [
            ('Content-Type', 'application/json'),
        ]

        rendered_errors = DesignateAdapter.render(
            self.api_version, exception.errors, failed_object=exception.object
        )

        url = getattr(request, 'url', None)

        response['code'] = exception.error_code
        response['type'] = exception.error_type or 'unknown'
        response['errors'] = rendered_errors

        # Return the new response
        if 'context' in request.environ:
            response['request_id'] = request.environ['context'].request_id

            notifications.send_api_fault(request.environ['context'], url,
                                         response['code'], exception)
        else:
            # TODO(ekarlso): Remove after verifying that there's actually a
            # context always set
            LOG.error('Missing context in request, please check.')

        return flask.Response(status=exception.error_code, headers=headers,
                              response=jsonutils.dump_as_bytes(response))

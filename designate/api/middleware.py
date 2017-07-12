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
from debtcollector import removals
import flask
import webob.dec
from oslo_config import cfg
import oslo_messaging as messaging
from oslo_log import log as logging
from oslo_middleware import base
from oslo_middleware import request_id
from oslo_serialization import jsonutils as json
from oslo_utils import strutils

from designate import exceptions
from designate import notifications
from designate import context
from designate import objects
from designate.objects.adapters import DesignateAdapter
from designate.i18n import _LI
from designate.i18n import _LW
from designate.i18n import _LE
from designate.i18n import _LC


LOG = logging.getLogger(__name__)


def auth_pipeline_factory(loader, global_conf, **local_conf):
    """
    A paste pipeline replica that keys off of auth_strategy.

    Code nabbed from cinder.
    """
    pipeline = local_conf[cfg.CONF['service:api'].auth_strategy]
    pipeline = pipeline.split()
    LOG.info(_LI('Getting auth pipeline: %s'), pipeline[:-1])
    filters = [loader.get_filter(n) for n in pipeline[:-1]]
    app = loader.get_app(pipeline[-1])
    filters.reverse()
    for filter in filters:
        app = filter(app)
    return app


class ContextMiddleware(base.Middleware):
    def _extract_sudo(self, ctxt, request):
        if request.headers.get('X-Auth-Sudo-Tenant-ID') or \
                request.headers.get('X-Auth-Sudo-Project-ID'):
            ctxt.sudo(
                request.headers.get('X-Auth-Sudo-Tenant-ID') or
                request.headers.get('X-Auth-Sudo-Project-ID')
            )

    def _extract_all_projects(self, ctxt, request):
        ctxt.all_tenants = False
        if request.headers.get('X-Auth-All-Projects'):
            value = request.headers.get('X-Auth-All-Projects')
            ctxt.all_tenants = strutils.bool_from_string(value)

        for i in ('all_projects', 'all_tenants', ):
            if i in request.GET:
                value = request.GET.pop(i)
                ctxt.all_tenants = strutils.bool_from_string(value)

    def _extract_dns_hide_counts(self, ctxt, request):
        ctxt.hide_counts = False
        value = request.headers.get('OpenStack-DNS-Hide-Counts')
        if value:
            ctxt.hide_counts = strutils.bool_from_string(value)

    def _extract_edit_managed_records(self, ctxt, request):
        ctxt.edit_managed_records = False
        if 'edit_managed_records' in request.GET:
            value = request.GET.pop('edit_managed_records')
            ctxt.edit_managed_records = strutils.bool_from_string(value)
        elif request.headers.get('X-Designate-Edit-Managed-Records'):
            ctxt.edit_managed_records = \
                strutils.bool_from_string(
                    request.headers.get('X-Designate-Edit-Managed-Records'))

    def _extract_client_addr(self, ctxt, request):
        if hasattr(request, 'client_addr'):
            ctxt.client_addr = request.client_addr

    def make_context(self, request, *args, **kwargs):
        req_id = request.environ.get(request_id.ENV_REQUEST_ID)
        kwargs.setdefault('request_id', req_id)

        ctxt = context.DesignateContext(*args, **kwargs)

        try:
            self._extract_sudo(ctxt, request)
            self._extract_all_projects(ctxt, request)
            self._extract_edit_managed_records(ctxt, request)
            self._extract_dns_hide_counts(ctxt, request)
            self._extract_client_addr(ctxt, request)
        finally:
            request.environ['context'] = ctxt
        return ctxt


class KeystoneContextMiddleware(ContextMiddleware):
    def __init__(self, application):
        super(KeystoneContextMiddleware, self).__init__(application)

        LOG.info(_LI('Starting designate keystonecontext middleware'))

    def process_request(self, request):
        headers = request.headers

        try:
            if headers['X-Identity-Status'] is 'Invalid':
                # TODO(graham) fix the return to use non-flask resources
                return flask.Response(status=401)
        except KeyError:
            # If the key is valid, Keystone does not include this header at all
            pass

        tenant_id = headers.get('X-Tenant-ID')
        if tenant_id is None:
            return flask.Response(status=401)

        if headers.get('X-Service-Catalog'):
            catalog = json.loads(headers.get('X-Service-Catalog'))
        else:
            catalog = None

        roles = headers.get('X-Roles').split(',')

        try:
            self.make_context(
                request,
                auth_token=headers.get('X-Auth-Token'),
                user=headers.get('X-User-ID'),
                tenant=tenant_id,
                roles=roles,
                service_catalog=catalog)
        except exceptions.Forbidden:
            return flask.Response(status=403)


class NoAuthContextMiddleware(ContextMiddleware):
    def __init__(self, application):
        super(NoAuthContextMiddleware, self).__init__(application)

        LOG.info(_LI('Starting designate noauthcontext middleware'))

    def process_request(self, request):
        headers = request.headers

        self.make_context(
            request,
            auth_token=headers.get('X-Auth-Token', None),
            user=headers.get('X-Auth-User-ID', 'noauth-user'),
            tenant=headers.get('X-Auth-Project-ID', 'noauth-project'),
            roles=headers.get('X-Roles', 'admin').split(',')
        )


class TestContextMiddleware(ContextMiddleware):
    def __init__(self, application, tenant_id=None, user_id=None):
        super(TestContextMiddleware, self).__init__(application)

        LOG.critical(_LC('Starting designate testcontext middleware'))
        LOG.critical(_LC('**** DO NOT USE IN PRODUCTION ****'))

        self.default_tenant_id = tenant_id
        self.default_user_id = user_id

    def process_request(self, request):
        headers = request.headers

        all_tenants = strutils.bool_from_string(
            headers.get('X-Test-All-Tenants', 'False'))

        self.make_context(
            request,
            user=headers.get('X-Test-User-ID', self.default_user_id),
            tenant=headers.get('X-Test-Tenant-ID', self.default_tenant_id),
            all_tenants=all_tenants)


class MaintenanceMiddleware(base.Middleware):
    def __init__(self, application):
        super(MaintenanceMiddleware, self).__init__(application)

        LOG.info(_LI('Starting designate maintenance middleware'))

        self.enabled = cfg.CONF['service:api'].maintenance_mode
        self.role = cfg.CONF['service:api'].maintenance_mode_role

    def process_request(self, request):
        # If maintaince mode is not enabled, pass the request on as soon as
        # possible
        if not self.enabled:
            return None

        # If the caller has the bypass role, let them through
        if ('context' in request.environ
                and self.role in request.environ['context'].roles):
            LOG.warning(_LW('Request authorized to bypass maintenance mode'))
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
        super(FaultWrapperMiddleware, self).__init__(application)

        LOG.info(_LI('Starting designate faultwrapper middleware'))

    @webob.dec.wsgify
    def __call__(self, request):
        try:
            return request.get_response(self.application)
        except exceptions.Base as e:
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
            LOG.error(_LE('Missing context in request, please check.'))

        return flask.Response(status=status, headers=headers,
                              response=json.dumps(response))


class FaultWrapperMiddlewareV1(FaultWrapperMiddleware):
    def _format_error(self, data):
        replace_map = [
            ("zone", "domain",)
        ]

        for i in replace_map:
            data["type"] = data["type"].replace(i[0], i[1])
        print(data)


class ValidationErrorMiddleware(base.Middleware):

    def __init__(self, application):
        super(ValidationErrorMiddleware, self).__init__(application)

        LOG.info(_LI('Starting designate validation middleware'))

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
            self.api_version, exception.errors, failed_object=exception.object)

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
            LOG.error(_LE('Missing context in request, please check.'))

        return flask.Response(status=exception.error_code, headers=headers,
                              response=json.dumps(response))


class APIv1ValidationErrorMiddleware(ValidationErrorMiddleware):
    def __init__(self, application):
        super(APIv1ValidationErrorMiddleware, self).__init__(application)
        self.api_version = 'API_v1'


class APIv2ValidationErrorMiddleware(ValidationErrorMiddleware):
    def __init__(self, application):
        super(APIv2ValidationErrorMiddleware, self).__init__(application)
        self.api_version = 'API_v2'


class SSLMiddleware(base.Middleware):
    """A middleware that replaces the request wsgi.url_scheme environment
    variable with the value of HTTP header configured in
    secure_proxy_ssl_header if exists in the incoming request.
    This is useful if the server is behind a SSL termination proxy.

    Code nabbed from Heat.
    """
    # Replaced by oslo.middleware's http_proxy_to_wsgi middleware
    @removals.remove
    def __init__(self, application):
        super(SSLMiddleware, self).__init__(application)
        LOG.info(_LI('Starting designate ssl middleware'))
        self.secure_proxy_ssl_header = 'HTTP_{0}'.format(
            cfg.CONF['service:api'].secure_proxy_ssl_header.upper().
            replace('-', '_'))
        self.override = cfg.CONF['service:api'].override_proto

    def process_request(self, request):
        request.environ['wsgi.url_scheme'] = request.environ.get(
            self.secure_proxy_ssl_header, request.environ['wsgi.url_scheme'])
        if self.override:
            request.environ['wsgi.url_scheme'] = self.override

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
import webob.dec
from oslo.config import cfg
from designate import exceptions
from designate import notifications
from designate import wsgi
from designate.context import DesignateContext
from designate.openstack.common import jsonutils as json
from designate.openstack.common import local
from designate.openstack.common import log as logging
from designate.openstack.common import uuidutils
from designate.openstack.common.rpc import common as rpc_common

LOG = logging.getLogger(__name__)

cfg.CONF.register_opts([
    cfg.BoolOpt('maintenance-mode', default=False,
                help='Enable API Maintenance Mode'),
    cfg.StrOpt('maintenance-mode-role', default='admin',
               help='Role allowed to bypass maintaince mode'),
], group='service:api')


class MaintenanceMiddleware(wsgi.Middleware):
    def __init__(self, application):
        super(MaintenanceMiddleware, self).__init__(application)

        LOG.info('Starting designate maintenance middleware')

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
            LOG.warning('Request authorized to bypass maintenance mode')
            return None

        # Otherwise, reject the request with a 503 Service Unavailable
        return flask.Response(status=503, headers={'Retry-After': 60})


def auth_pipeline_factory(loader, global_conf, **local_conf):
    """
    A paste pipeline replica that keys off of auth_strategy.

    Code nabbed from cinder.
    """
    pipeline = local_conf[cfg.CONF['service:api'].auth_strategy]
    pipeline = pipeline.split()
    LOG.info('Getting auth pipeline: %s' % pipeline[:-1])
    filters = [loader.get_filter(n) for n in pipeline[:-1]]
    app = loader.get_app(pipeline[-1])
    filters.reverse()
    for filter in filters:
        app = filter(app)
    return app


class ContextMiddleware(wsgi.Middleware):
    def process_response(self, response):
        try:
            context = local.store.context
        except Exception:
            pass
        else:
            # Add the Request ID as a response header
            response.headers['X-DNS-Request-ID'] = context.request_id

        return response


class KeystoneContextMiddleware(ContextMiddleware):
    def __init__(self, application):
        super(KeystoneContextMiddleware, self).__init__(application)

        LOG.info('Starting designate keystonecontext middleware')

    def process_request(self, request):
        headers = request.headers

        try:
            if headers['X-Identity-Status'] is 'Invalid':
                #TODO(graham) fix the return to use non-flask resources
                return flask.Response(status=401)
        except KeyError:
            #If the key is valid, Keystone does not include this header at all
            pass

        if headers.get('X-Service-Catalog'):
            catalog = json.loads(headers.get('X-Service-Catalog'))
        else:
            catalog = None

        roles = headers.get('X-Roles').split(',')

        context = DesignateContext(auth_token=headers.get('X-Auth-Token'),
                                   user=headers.get('X-User-ID'),
                                   tenant=headers.get('X-Tenant-ID'),
                                   roles=roles,
                                   service_catalog=catalog)

        # Store the context where oslo-log exepcts to find it.
        local.store.context = context

        # Attempt to sudo, if requested.
        sudo_tenant_id = headers.get('X-Designate-Sudo-Tenant-ID', None)

        if sudo_tenant_id and (uuidutils.is_uuid_like(sudo_tenant_id)
                               or sudo_tenant_id.isdigit()):
            context.sudo(sudo_tenant_id)

        # Attach the context to the request environment
        request.environ['context'] = context


class NoAuthContextMiddleware(ContextMiddleware):
    def __init__(self, application):
        super(NoAuthContextMiddleware, self).__init__(application)

        LOG.info('Starting designate noauthcontext middleware')

    def process_request(self, request):
        # NOTE(kiall): This makes the assumption that disabling authentication
        #              means you wish to allow full access to everyone.
        context = DesignateContext(is_admin=True)

        # Store the context where oslo-log exepcts to find it.
        local.store.context = context

        # Attach the context to the request environment
        request.environ['context'] = context


class FaultWrapperMiddleware(wsgi.Middleware):
    def __init__(self, application):
        super(FaultWrapperMiddleware, self).__init__(application)

        LOG.info('Starting designate faultwrapper middleware')

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
        except rpc_common.Timeout as e:
            # Special case for RPC timeout's
            response = {
                'code': 504,
                'type': 'timeout',
            }

            return self._handle_exception(request, e, 504, response)
        except Exception as e:
            # Handle all other exception types
            return self._handle_exception(request, e)

    def _handle_exception(self, request, e, status=500, response={}):
        # Log the exception ASAP
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

        if 'context' in request.environ:
            response['request_id'] = request.environ['context'].request_id

            notifications.send_api_fault(url, response['code'], e)
        else:
            #TODO(ekarlso): Remove after verifying that there's actually a
            # context always set
            LOG.error('Missing context in request, please check.')

        # Return the new response
        return flask.Response(status=status, headers=headers,
                              response=json.dumps(response))

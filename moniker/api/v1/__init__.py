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
from stevedore import extension
from stevedore import named
from werkzeug import exceptions as wexceptions
from werkzeug.routing import BaseConverter, ValidationError
from moniker.openstack.common import cfg
from moniker.openstack.common import jsonutils as json
from moniker.openstack.common import log as logging
from moniker.openstack.common import uuidutils
from moniker.openstack.common.rpc import common as rpc_common
from moniker import exceptions
from moniker import wsgi

LOG = logging.getLogger(__name__)

cfg.CONF.register_opts([
    cfg.ListOpt('enabled-extensions-v1', default=[],
                help='Enabled API Extensions'),
], group='service:api')


def factory(global_config, **local_conf):
    app = flask.Flask('moniker.api.v1')
    app.config.update(
        PROPAGATE_EXCEPTIONS=True
    )

    # Install custom converters (URL param varidators)
    app.url_map.converters['uuid'] = UUIDConverter

    # Ensure all error responses are JSON
    def _json_error(ex):
        code = ex.code if isinstance(ex, wexceptions.HTTPException) else 500

        response = {
            'code': code
        }

        if code == 405:
            response['type'] = 'invalid_method'

        response = flask.jsonify(**response)
        response.status_code = code

        return response

    for code in wexceptions.default_exceptions.iterkeys():
        app.error_handler_spec[None][code] = _json_error

    # TODO(kiall): Ideally, we want to make use of the Plugin class here.
    #              This works for the moment though.
    def _register_blueprint(ext):
        app.register_blueprint(ext.plugin)

    # Add all in-built APIs
    mgr = extension.ExtensionManager('moniker.api.v1')
    mgr.map(_register_blueprint)

    # Add any (enabled) optional extensions
    extensions = cfg.CONF['service:api'].enabled_extensions_v1

    if len(extensions) > 0:
        extmgr = named.NamedExtensionManager('moniker.api.v1.extensions',
                                             names=extensions)
        extmgr.map(_register_blueprint)

    return app


class UUIDConverter(BaseConverter):
    """ Validates UUID URL paramaters """

    def to_python(self, value):
        if not uuidutils.is_uuid_like(value):
            raise ValidationError()

        return value

    def to_url(self, value):
        return str(value)


class FaultWrapperMiddleware(wsgi.Middleware):
    @webob.dec.wsgify
    def __call__(self, request):
        try:
            return request.get_response(self.application)
        except exceptions.Base, e:
            # Handle Moniker Exceptions
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
        except rpc_common.Timeout, e:
            # Special case for RPC timeout's
            response = {
                'code': 504,
                'type': 'timeout',
            }

            return self._handle_exception(request, e, 504, response)
        except Exception, e:
            # Handle all other exception types
            return self._handle_exception(request, e)

    def _handle_exception(self, request, e, status=500, response={}):
        # Log the exception ASAP
        LOG.exception(e)

        headers = [
            ('Content-Type', 'application/json'),
        ]

        # Set a response code and type, if they are missing.
        if 'code' not in response:
            response['code'] = status

        if 'type' not in response:
            response['type'] = 'unknown'

        # Set the request ID, if we have one
        if 'context' in request.environ:
            response['request_id'] = request.environ['context'].request_id

        # TODO(kiall): Send a fault notification

        # Return the new response
        return flask.Response(status=status, headers=headers,
                              response=json.dumps(response))

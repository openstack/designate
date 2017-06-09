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
import six
import flask
from stevedore import extension
from stevedore import named
from werkzeug import exceptions as wexceptions
from werkzeug import wrappers
from werkzeug.routing import BaseConverter
from werkzeug.routing import ValidationError
from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils

from designate import exceptions
from designate import utils


LOG = logging.getLogger(__name__)


class DesignateRequest(flask.Request, wrappers.AcceptMixin,
                       wrappers.CommonRequestDescriptorsMixin):
    def __init__(self, *args, **kwargs):
        super(DesignateRequest, self).__init__(*args, **kwargs)

        self._validate_content_type()
        self._validate_accept()

    def _validate_content_type(self):
        if (self.method in ['POST', 'PUT', 'PATCH']
                and self.mimetype != 'application/json'):

            msg = 'Unsupported Content-Type: %s' % self.mimetype
            raise exceptions.UnsupportedContentType(msg)

    def _validate_accept(self):
        if 'accept' in self.headers and not self.accept_mimetypes.accept_json:
            msg = 'Unsupported Accept: %s' % self.accept_mimetypes
            raise exceptions.UnsupportedAccept(msg)


class JSONEncoder(flask.json.JSONEncoder):
    @staticmethod
    def default(o):
        return jsonutils.to_primitive(o)


def factory(global_config, **local_conf):
    if not cfg.CONF['service:api'].enable_api_v1:
        def disabled_app(environ, start_response):
            status = '404 Not Found'
            start_response(status, [])
            return []

        return disabled_app

    app = flask.Flask('designate.api.v1')
    app.request_class = DesignateRequest
    app.json_encoder = JSONEncoder
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

    for code in six.iterkeys(wexceptions.default_exceptions):
        app.register_error_handler(code, _json_error)

    # TODO(kiall): Ideally, we want to make use of the Plugin class here.
    #              This works for the moment though.
    def _register_blueprint(ext):
        app.register_blueprint(ext.plugin)

    # Add all in-built APIs
    mgr = extension.ExtensionManager('designate.api.v1')
    mgr.map(_register_blueprint)

    # Add any (enabled) optional extensions
    extensions = cfg.CONF['service:api'].enabled_extensions_v1

    if len(extensions) > 0:
        extmgr = named.NamedExtensionManager('designate.api.v1.extensions',
                                             names=extensions)
        extmgr.map(_register_blueprint)

    return app


class UUIDConverter(BaseConverter):
    """Validates UUID URL parameters"""

    def to_python(self, value):
        if not utils.is_uuid_like(value):
            raise ValidationError()

        return value

    def to_url(self, value):
        return str(value)


def load_values(request, valid_keys):
    """Load valid attributes from request"""
    result = {}
    error_keys = []
    values = request.json
    for k in values:
        if k in valid_keys:
            result[k] = values[k]
        else:
            error_keys.append(k)

    if error_keys:
        error_msg = 'Provided object does not match schema. Keys {0} are not \
                     valid in the request body', error_keys
        raise exceptions.InvalidObject(error_msg)

    return result

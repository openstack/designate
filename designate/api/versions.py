# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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

from designate.common import constants
import designate.conf


CONF = designate.conf.CONF


def _add_a_version(versions, version, api_url, status, timestamp):
    versions.append({
        'id': version,
        'status': status,
        'updated': timestamp,
        'links': [{'href': api_url,
                   'rel': 'self'},
                  {'href': constants.API_REF_URL,
                   'rel': 'help'}]
    })


def factory(global_config, **local_conf):
    app = flask.Flask('designate.api.versions')

    @app.route('/', methods=['GET'])
    def version_list():
        if CONF['service:api'].enable_host_header:
            url_root = flask.request.url_root
        else:
            url_root = CONF['service:api'].api_base_uri
        api_url = url_root.rstrip('/') + '/v2'

        versions = []
        # Initial API version for v2 API
        _add_a_version(versions, 'v2', api_url, constants.SUPPORTED,
                       '2022-06-29T00:00:00Z')
        _add_a_version(versions, 'v2.0', api_url, constants.SUPPORTED,
                       '2022-06-29T00:00:00Z')
        # 2.1 Shared Zones
        _add_a_version(versions, 'v2.1', api_url, constants.CURRENT,
                       '2023-01-25T00:00:00Z')

        return flask.jsonify({'versions': versions})

    return app

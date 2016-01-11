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
from oslo_config import cfg

cfg.CONF.import_opt('enable_host_header', 'designate.api', group='service:api')


def factory(global_config, **local_conf):
    app = flask.Flask('designate.api.versions')

    versions = []

    base = cfg.CONF['service:api'].api_base_uri.rstrip('/')

    def _host_header_links():
        del versions[:]
        host_url = flask.request.host_url.rstrip('/')
        _version('v1', 'DEPRECATED', host_url)
        _version('v2', 'CURRENT', host_url)

    def _version(version, status, base_uri):
        versions.append({
            'id': '%s' % version,
            'status': status,
            'links': [{
                'href': base_uri + '/' + version,
                'rel': 'self'
            }]
        })

    if cfg.CONF['service:api'].enable_api_v1:
        _version('v1', 'DEPRECATED', base)

    if cfg.CONF['service:api'].enable_api_v2:
        _version('v2', 'CURRENT', base)

    @app.route('/', methods=['GET'])
    def version_list():
        if cfg.CONF['service:api'].enable_host_header:
            _host_header_links()

        return flask.jsonify({
            "versions": {
                "values": versions
            }
        })

    return app

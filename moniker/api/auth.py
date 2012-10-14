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
from moniker.openstack.common.context import RequestContext
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker import wsgi

LOG = logging.getLogger(__name__)


def pipeline_factory(loader, global_conf, **local_conf):
    """
    A paste pipeline replica that keys off of auth_strategy.

    Code nabbed from cinder.
    """
    pipeline = local_conf[cfg.CONF.auth_strategy]
    pipeline = pipeline.split()
    filters = [loader.get_filter(n) for n in pipeline[:-1]]
    app = loader.get_app(pipeline[-1])
    filters.reverse()
    for filter in filters:
        app = filter(app)
    return app


class KeystoneContextMiddleware(wsgi.Middleware):
    def process_request(self, request):
        headers = request.headers
        context = RequestContext(auth_tok=headers.get('X-Auth-Token'),
                                 user=headers.get('X-User-ID'),
                                 tenant=headers.get('X-Tenant-ID'))
        request.environ['context'] = context


class NoAuthMiddleware(wsgi.Middleware):
    def process_request(self, request):
        request.environ['context'] = RequestContext()

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
from paste import deploy
from designate.openstack.common import log as logging
from designate.openstack.common import wsgi
from oslo.config import cfg
from designate import exceptions
from designate import utils
from designate import policy


LOG = logging.getLogger(__name__)


class Service(wsgi.Service):
    def __init__(self, backlog=128, threads=1000):

        api_paste_config = cfg.CONF['service:api'].api_paste_config
        config_paths = utils.find_config(api_paste_config)

        if len(config_paths) == 0:
            msg = 'Unable to determine appropriate api-paste-config file'
            raise exceptions.ConfigurationError(msg)

        LOG.info('Using api-paste-config found at: %s' % config_paths[0])

        policy.init_policy()

        application = deploy.loadapp("config:%s" % config_paths[0],
                                     name='osapi_dns')

        super(Service, self).__init__(application=application,
                                      host=cfg.CONF['service:api'].api_host,
                                      port=cfg.CONF['service:api'].api_port,
                                      backlog=backlog,
                                      threads=threads)

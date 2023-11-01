# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
import pecan
import pecan.deploy

from designate.api.v2 import patches
import designate.conf


CONF = designate.conf.CONF


def setup_app(pecan_config):
    config = dict(pecan_config)

    config['app']['debug'] = CONF['service:api'].pecan_debug

    pecan.configuration.set_config(config, overwrite=True)

    app = pecan.make_app(
        pecan_config.app.root,
        debug=getattr(pecan_config.app, 'debug', False),
        force_canonical=getattr(pecan_config.app, 'force_canonical', True),
        request_cls=patches.Request
    )

    return app

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
from oslo_log import log as logging

import designate.conf
from designate.quota import base


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


def get_quota():
    quota_driver = CONF.quota_driver

    LOG.debug("Loading quota driver: %s", quota_driver)

    cls = base.Quota.get_driver(quota_driver)

    return cls()

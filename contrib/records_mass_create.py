#!/usr/bin/env python
# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
import os
import sys

from designateclient import v1
from oslo_config import cfg
from oslo_log import log as logging

from designate.utils import generate_uuid


cfg.CONF.register_cli_opts([
    cfg.StrOpt("domain_id", help="ID of domain to use."),
    cfg.IntOpt("records", default=100,
               help="Records to create (name will be <uuid>.<domain name>.")
])

LOG = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.register_options(cfg.CONF)
    cfg.CONF(sys.argv[1:], project="designate")
    logging.setup(cfg.CONF, "designate")

    project_name = os.environ.get(
        'OS_PROJECT_NAME', os.environ.get('OS_TENANT_NAME'))

    client = v1.Client(
        auth_url=os.environ.get('OS_AUTH_URL'),
        username=os.environ.get('OS_USERNAME'),
        password=os.environ.get('OS_PASSWORD'),
        project_name=project_name
    )

    domain = client.domains.get(cfg.CONF.domain_id)

    msg = "Creating %s records", cfg.CONF.records
    LOG.info(msg)
    for i in range(0, cfg.CONF.records):
        name = '%s.%s' % (generate_uuid(), domain.name)
        record = {"name": name, "type": "A", "data": "10.0.0.1"}
        client.records.create(domain, record)

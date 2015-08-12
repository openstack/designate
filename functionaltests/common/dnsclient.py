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

import dns.resolver
from oslo_config import cfg

from functionaltests.common import utils


def query(name, type_, server="127.0.0.1", port=53, timeout=3):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [server]
    resolver.port = int(port)
    resolver.timeout = timeout

    try:
        return resolver.query(name, type_)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return False


def query_servers(name, type_, servers=None, timeout=3):
    servers = servers or os.environ.get("DESIGNATE_SERVERS",
                                        cfg.CONF.designate.nameservers)

    results = []
    for srv in servers:
        server, port = srv.split(":")
        port = port or 53
        result = utils.wait_for_condition(
            lambda: query(name, type_, server, port))
        results.append(result)

    return results

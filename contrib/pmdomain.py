# Copyright (C) 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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
import sys
import getopt

import eventlet
from oslo.config import cfg

from designate import utils
from designate.pool_manager import rpcapi
from designate.context import DesignateContext
from designate.objects import Domain
from designate import rpc


# This is required to ensure ampq works without hanging.
eventlet.monkey_patch(os=False)


def main(argv):
    # TODO(Ron): remove this application once unit testing is in place.

    usage = 'pmdomain.py -c <domain-name> | -d <domain-name>'
    domain_name = None
    create = False
    delete = False

    try:
        opts, args = getopt.getopt(
            argv, "hc:d:", ["help", "create=", "delete="])
    except getopt.GetoptError:
        print('%s' % usage)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('%s' % usage)
            sys.exit()
        elif opt in ("-c", "--create"):
            create = True
            domain_name = arg
        elif opt in ("-d", "--delete"):
            delete = True
            domain_name = arg

    if (delete and create) or (not delete and not create):
        print('%s' % usage)
        sys.exit(2)

    # Read the Designate configuration file.
    utils.read_config('designate', [])
    rpc.init(cfg.CONF)

    context = DesignateContext.get_admin_context(
        tenant=utils.generate_uuid(),
        user=utils.generate_uuid())
    pool_manager_api = rpcapi.PoolManagerAPI()

    # For the BIND9 backend, all that is needed is a name.
    values = {
        'name': domain_name
    }
    domain = Domain(**values)

    if create:
        pool_manager_api.create_domain(context, domain)

    if delete:
        pool_manager_api.delete_domain(context, domain)


if __name__ == "__main__":
    main(sys.argv[1:])

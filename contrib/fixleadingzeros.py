#!/usr/bin/env python
# Copyright (C) 2018 Verizon
#
# Author: Graham Hayes <gr@ham.ie>
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
import argparse
import ipaddress
import logging
import sys

import dns.exception
from dns.ipv4 import inet_aton
from keystoneauth1.identity import generic
from keystoneauth1 import session as keystone_session

from designateclient import shell
from designateclient.v2 import client


auth = generic.Password(
    auth_url=shell.env('OS_AUTH_URL'),
    username=shell.env('OS_USERNAME'),
    password=shell.env('OS_PASSWORD'),
    project_name=shell.env('OS_PROJECT_NAME'),
    project_domain_id=shell.env('OS_PROJECT_DOMAIN_ID'),
    user_domain_id=shell.env('OS_USER_DOMAIN_ID'))

session = keystone_session.Session(auth=auth)

client = client.Client(session=session)

logging.basicConfig()
LOG = logging.getLogger('fixleadingzeros')


def find_bad_recordsets():
    bad_recordsets = {}
    LOG.debug("Looking for all A recordsets")
    recordsets = client.recordsets.list_all_zones(criterion={'type': 'A', })
    LOG.debug("Found %d A recordsets", len(recordsets))
    LOG.debug("Filtering recordsets")
    for recordset in recordsets:
        for record in recordset['records']:
            try:
                inet_aton(record)
            except dns.exception.SyntaxError:
                bad_recordsets[recordset['id']] = recordset
    LOG.debug("Found %d A invaild recordsets", len(bad_recordsets))
    return bad_recordsets


def show_recordsets(recordsets):
    for rs in recordsets:
        LOG.info(
            ("%(name)s - %(records)s - Zone ID: %(zone_id)s - "
             "Project ID: %(project_id)s ") % recordsets[rs])


def fix_bad_recordsets(bad_recordsets):
    LOG.debug("Removing leading zeros in IPv4 addresses")
    for rs in bad_recordsets:
        new_records = []
        for ip in bad_recordsets[rs]['records']:
            ip = '.'.join(f'{int(i)}' for i in ip.split('.'))
            new_records.append(
                str(ipaddress.IPv4Address(ip))
            )
        bad_recordsets[rs]['records'] = new_records
    return bad_recordsets


def update_recordsets(recordsets):
    LOG.info("Updating recordsets")
    for rs in recordsets:
        LOG.debug(("Updating %(name)s - %(records)s - Zone ID: %(zone_id)s - "
                   "Project ID: %(project_id)s ") % recordsets[rs])
        client.recordsets.update(
            recordsets[rs]['zone_id'],
            recordsets[rs]['id'],
            {'records': recordsets[rs]['records']}
        )


def main():
    parser = argparse.ArgumentParser(
        description='Fix any recordsets that have leading zeros in A records')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='verbose output')
    parser.add_argument('-d', '--dry-run', action='store_true',
                        help='do not modify records, just log bad records')
    parser.add_argument('-a', '--all-projects', action='store_true',
                        help="Run on all projects")
    args = parser.parse_args()
    if args.verbose:
        LOG.setLevel(logging.DEBUG)
    else:
        LOG.setLevel(logging.INFO)

    if args.all_projects:
        client.session.all_projects = True

    bad_recordsets = find_bad_recordsets()

    LOG.info("Bad recordsets")
    show_recordsets(bad_recordsets)

    fixed_recordsets = fix_bad_recordsets(bad_recordsets)
    LOG.info("Fixed recordsets")
    show_recordsets(fixed_recordsets)

    if not args.dry_run:
        update_recordsets(fixed_recordsets)


if __name__ == '__main__':
    sys.exit(main())

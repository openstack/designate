#!/usr/bin/env python
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
from setuptools import setup, find_packages
import textwrap
from moniker.openstack.common import setup as common_setup

install_requires = common_setup.parse_requirements(['tools/pip-requires'])
install_options = common_setup.parse_requirements(['tools/pip-options'])
tests_require = common_setup.parse_requirements(['tools/test-requires'])
setup_require = common_setup.parse_requirements(['tools/setup-requires'])
dependency_links = common_setup.parse_dependency_links([
    'tools/pip-requires',
    'tools/pip-options',
    'tools/test-requires',
    'tools/setup-requires'
])

setup(
    name='moniker',
    version=common_setup.get_version('moniker'),
    description='DNS as a Service',
    author='Kiall Mac Innes',
    author_email='kiall@managedit.ie',
    url='https://launchpad.net/moniker',
    packages=find_packages(exclude=['bin']),
    include_package_data=True,
    test_suite='nose.collector',
    setup_requires=setup_require,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        'optional': install_options,
    },
    dependency_links=dependency_links,
    scripts=[
        'bin/moniker-central',
        'bin/moniker-api',
        'bin/moniker-agent',
        'bin/moniker-manage',
        'bin/moniker-rootwrap'
    ],
    cmdclass=common_setup.get_cmdclass(),
    entry_points=textwrap.dedent("""
        [moniker.storage]
        sqlalchemy = moniker.storage.impl_sqlalchemy:SQLAlchemyStorage

        [moniker.notification.handler]
        nova_fixed = moniker.notification_handler.nova:NovaFixedHandler
        quantum_floatingip = moniker.notification_handler.quantum\
                             :QuantumFloatingHandler

        [moniker.backend]
        bind9 = moniker.backend.impl_bind9:Bind9Backend
        mysqlbind9 = moniker.backend.impl_mysqlbind9:MySQLBind9Backend
        powerdns = moniker.backend.impl_powerdns:PowerDNSBackend
        rpc = moniker.backend.impl_rpc:RPCBackend
        fake = moniker.backend.impl_fake:FakeBackend

        [moniker.manage]
        database-init = moniker.manage.database:InitCommand
        database-sync = moniker.manage.database:SyncCommand
        powerdns database-init = moniker.manage.powerdns:DatabaseInitCommand
        powerdns database-sync = moniker.manage.powerdns:DatabaseSyncCommand

        server-list = moniker.manage.servers:ListServersCommand
        server-get = moniker.manage.servers:GetServerCommand
        server-create = moniker.manage.servers:CreateServerCommand
        server-update = moniker.manage.servers:UpdateServerCommand
        server-delete = moniker.manage.servers:DeleteServerCommand

        tsigkey-list = moniker.manage.tsigkeys:ListTsigKeysCommand
        tsigkey-get = moniker.manage.tsigkeys:GetTsigKeyCommand
        tsigkey-create = moniker.manage.tsigkeys:CreateTsigKeyCommand
        tsigkey-update = moniker.manage.tsigkeys:UpdateTsigKeyCommand
        tsigkey-delete = moniker.manage.tsigkeys:DeleteTsigKeyCommand
        """),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Internet :: Name Service (DNS)',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Environment :: No Input/Output (Daemon)',
        'Environment :: OpenStack',
    ],
)

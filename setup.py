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
from moniker.openstack.common import setup as common_setup

install_requires = common_setup.parse_requirements(['tools/pip-requires'])
dependency_links = common_setup.parse_dependency_links(['tools/pip-requires'])

setup(
    name='moniker',
    version='0.0',
    description='DNS as a Service',
    author='Kiall Mac Innes',
    author_email='kiall@managedit.ie',
    url='https://launchpad.net/moniker',
    packages=find_packages(exclude=['bin']),
    include_package_data=True,
    test_suite='nose.collector',
    setup_requires=['setuptools-git>=0.4'],
    install_requires=install_requires,
    dependency_links=dependency_links,
    scripts=[
        'bin/moniker-agent-bind9',
        'bin/moniker-api',
        'bin/moniker-central',
    ],
    cmdclass=common_setup.get_cmdclass(),
)

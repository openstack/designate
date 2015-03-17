"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import random

from functionaltests.api.v2.models.zone_model import ZoneModel


def random_ip():
    return ".".join(str(random.randrange(0, 256)) for _ in range(4))


def random_string(prefix='rand', n=8, suffix=''):
    """Return a string containing random digits

    :param prefix: the exact text to start the string. Defaults to "rand"
    :param n: the number of random digits to generate
    :param suffix: the exact text to end the string
    """
    digits = "".join(str(random.randrange(0, 10)) for _ in range(n))
    return prefix + digits + suffix


def random_zone_data(name=None, email=None, ttl=None, description=None):
    """Generate random zone data, with optional overrides

    :return: A ZoneModel
    """
    if name is None:
        name = random_string(prefix='testdomain', suffix='.com.')
    if email is None:
        email = ("admin@" + name).strip('.')
    if description is None:
        description = random_string(prefix='Description ')
    if ttl is None:
        ttl = random.randint(1200, 8400),
    return ZoneModel.from_dict({
        'zone': {
            'name': name,
            'email': email,
            'ttl': random.randint(1200, 8400),
            'description': description}})

# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from __future__ import absolute_import

from horizon import exceptions
from django.conf import settings
import logging

from designateclient.v1 import Client  # noqa
from designateclient.v1.domains import Domain  # noqa
from designateclient.v1.records import Record  # noqa

from openstack_dashboard.api.base import url_for  # noqa

LOG = logging.getLogger(__name__)


def designateclient(request):
    designate_url = ""
    try:
        designate_url = url_for(request, 'dns')
    except exceptions.ServiceCatalogException:
        LOG.debug('no dns service configured.')
        return None

    LOG.debug('designateclient connection created using token "%s"'
              'and url "%s"' % (request.user.token.id, designate_url))

    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)

    return Client(endpoint=designate_url,
                  token=request.user.token.id,
                  username=request.user.username,
                  tenant_id=request.user.project_id,
                  insecure=insecure,
                  cacert=cacert)


def domain_get(request, domain_id):
    d_client = designateclient(request)
    if d_client is None:
        return []
    return d_client.domains.get(domain_id)


def domain_list(request):
    d_client = designateclient(request)
    if d_client is None:
        return []
    return d_client.domains.list()


def domain_create(request, name, email, ttl=None, description=None):
    d_client = designateclient(request)
    if d_client is None:
        return None

    options = {
        'description': description,
    }

    # TTL needs to be optionally added as argument because the client
    # won't accept a None value
    if ttl is not None:
        options['ttl'] = ttl

    domain = Domain(name=name, email=email, **options)

    return d_client.domains.create(domain)


def domain_update(request, domain_id, email, ttl, description=None):
    d_client = designateclient(request)
    if d_client is None:
        return None

    # A quirk of the designate client is that you need to start with a
    # base record and then update individual fields in order to persist
    # the data. The designate client will only send the 'changed' fields.
    domain = Domain(id=domain_id, name='', email='')

    domain.email = email
    domain.ttl = ttl
    domain.description = description

    return d_client.domains.update(domain)


def domain_delete(request, domain_id):
    d_client = designateclient(request)
    if d_client is None:
        return []
    return d_client.domains.delete(domain_id)


def server_list(request, domain_id):
    d_client = designateclient(request)
    if d_client is None:
        return []
    return d_client.domains.list_domain_servers(domain_id)


def record_list(request, domain_id):
    d_client = designateclient(request)
    if d_client is None:
        return []
    return d_client.records.list(domain_id)


def record_get(request, domain_id, record_id):
    d_client = designateclient(request)
    if d_client is None:
        return []
    return d_client.records.get(domain_id, record_id)


def record_delete(request, domain_id, record_id):
    d_client = designateclient(request)
    if d_client is None:
        return []
    return d_client.records.delete(domain_id, record_id)


def record_create(request, domain_id, **kwargs):
    d_client = designateclient(request)
    if d_client is None:
        return []

    record = Record(**kwargs)
    return d_client.records.create(domain_id, record)


def record_update(request, domain_id, record_id, **kwargs):
    d_client = designateclient(request)
    if d_client is None:
        return []

    # A quirk of the designate client is that you need to start with a
    # base record and then update individual fields in order to persist
    # the data. The designate client will only send the 'changed' fields.
    record = Record(
        id=record_id,
        type='A',
        name='',
        data='')

    record.type = kwargs.get('type', None)
    record.name = kwargs.get('name', None)
    record.data = kwargs.get('data', None)
    record.priority = kwargs.get('priority', None)
    record.ttl = kwargs.get('ttl', None)
    record.description = kwargs.get('description', None)

    return d_client.records.update(domain_id, record)

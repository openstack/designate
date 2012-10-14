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
import flask
from moniker.openstack.common import log as logging
from moniker import exceptions
from moniker.api.v1 import blueprint
from moniker.api.v1.schemas import domain_schema, domains_schema
from moniker.central import api as central_api

LOG = logging.getLogger(__name__)


def _append_domain_links(values, domain_id):
    values['self'] = flask.url_for('.get_domain', domain_id=domain_id)
    values['records'] = flask.url_for('.get_records', domain_id=domain_id)
    values['schema'] = flask.url_for('.get_domain_schema')

    return values


@blueprint.route('/schemas/domain', methods=['GET'])
def get_domain_schema():
    return flask.jsonify(domain_schema.raw())


@blueprint.route('/schemas/domains', methods=['GET'])
def get_domains_schema():
    return flask.jsonify(domains_schema.raw())


@blueprint.route('/domains', methods=['POST'])
def create_domain():
    context = flask.request.environ.get('context')
    values = flask.request.json

    try:
        domain_schema.validate(values)
        domain = central_api.create_domain(context, values)
    except exceptions.InvalidObject, e:
        return flask.Response(status=400, response=str(e))
    except exceptions.DuplicateDomain:
        return flask.Response(status=409)
    else:
        domain = _append_domain_links(domain, domain['id'])

        domain = domain_schema.filter(domain)

        response = flask.jsonify(domain)
        response.status_int = 201
        response.location = flask.url_for('.get_domain',
                                          domain_id=domain['id'])
        return response


@blueprint.route('/domains', methods=['GET'])
def get_domains():
    context = flask.request.environ.get('context')

    domains = central_api.get_domains(context)

    domains = domains_schema.filter(domains)

    return flask.jsonify(domains=domains)


@blueprint.route('/domains/<domain_id>', methods=['GET'])
def get_domain(domain_id):
    context = flask.request.environ.get('context')

    try:
        domain = central_api.get_domain(context, domain_id)
    except exceptions.DomainNotFound:
        return flask.Response(status=404)
    else:
        domain = _append_domain_links(domain, domain['id'])

        domain = domain_schema.filter(domain)

        return flask.jsonify(domain)


@blueprint.route('/domains/<domain_id>', methods=['PUT'])
def update_domain(domain_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    try:
        domain_schema.validate(values)
        domain = central_api.update_domain(context, domain_id, values)
    except exceptions.InvalidObject, e:
        return flask.Response(status=400, response=str(e))
    except exceptions.DomainNotFound:
        return flask.Response(status=404)
    except exceptions.DuplicateDomain:
        return flask.Response(status=409)
    else:
        domain = _append_domain_links(domain, domain['id'])

        domain = domain_schema.filter(domain)

        return flask.jsonify(domain)


@blueprint.route('/domains/<domain_id>', methods=['DELETE'])
def delete_domain(domain_id):
    context = flask.request.environ.get('context')

    try:
        central_api.delete_domain(context, domain_id)
    except exceptions.DomainNotFound:
        return flask.Response(status=404)
    else:
        return flask.Response(status=200)

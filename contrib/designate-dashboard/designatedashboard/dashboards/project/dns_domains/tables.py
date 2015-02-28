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
import logging

from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tables

from designatedashboard import api

LOG = logging.getLogger(__name__)

EDITABLE_RECORD_TYPES = (
    "A",
    "AAAA",
    "CNAME",
    "MX",
    "PTR",
    "SPF",
    "SRV",
    "SSHFP",
    "TXT",
)


class CreateDomain(tables.LinkAction):

    '''Link action for navigating to the CreateDomain view.'''
    name = "create_domain"
    verbose_name = _("Create Domain")
    url = "horizon:project:dns_domains:create_domain"
    classes = ("ajax-modal", "btn-create")


class EditDomain(tables.LinkAction):

    '''Link action for navigating to the UpdateDomain view.'''
    name = "edit_domain"
    verbose_name = _("Edit Domain")
    url = "horizon:project:dns_domains:update_domain"
    classes = ("ajax-modal", "btn-edit")


class ManageRecords(tables.LinkAction):

    '''Link action for navigating to the ManageRecords view.'''
    name = "manage_records"
    verbose_name = _("Manage Records")
    url = "horizon:project:dns_domains:records"
    classes = ("btn-edit")


class DeleteDomain(tables.BatchAction):

    '''Batch action for deleting domains.'''
    name = "delete"
    action_present = _("Delete")
    action_past = _("Deleted")
    data_type_singular = _("Domain")
    data_type_plural = _("Domains")
    classes = ('btn-danger', 'btn-delete')

    def action(self, request, domain_id):
        api.designate.domain_delete(request, domain_id)


class CreateRecord(tables.LinkAction):

    '''Link action for navigating to the CreateRecord view.'''
    name = "create_record"
    verbose_name = _("Create Record")
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        url = "horizon:project:dns_domains:create_record"
        return urlresolvers.reverse(url, kwargs=self.table.kwargs)


class EditRecord(tables.LinkAction):

    '''Link action for navigating to the UpdateRecord view.'''
    name = "edit_record"
    verbose_name = _("Edit Record")
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, datum=None):
        url = "horizon:project:dns_domains:update_record"
        kwargs = {
            'domain_id': datum.domain_id,
            'record_id': datum.id,
        }

        return urlresolvers.reverse(url, kwargs=kwargs)

    def allowed(self, request, record=None):
        return record.type in EDITABLE_RECORD_TYPES


class DeleteRecord(tables.DeleteAction):

    '''Link action for navigating to the UpdateRecord view.'''
    data_type_singular = _("Record")

    def delete(self, request, record_id):
        domain_id = self.table.kwargs['domain_id']
        return api.designate.record_delete(request, domain_id, record_id)

    def allowed(self, request, record=None):
        return record.type in EDITABLE_RECORD_TYPES


class BatchDeleteRecord(tables.BatchAction):

    '''Batch action for deleting domain records.'''

    name = "delete"
    action_present = _("Delete")
    action_past = _("Deleted")
    data_type_singular = _("Record")
    classes = ('btn-danger', 'btn-delete')

    def action(self, request, record_id):
        domain_id = self.table.kwargs['domain_id']
        api.designate.record_delete(request, domain_id, record_id)


class DomainsTable(tables.DataTable):

    '''Data table for displaying domain summary information.'''

    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link=("horizon:project:dns_domains:update_domain"),
                         link_classes=('ajax-modal',))

    email = tables.Column("email",
                          verbose_name=_("Email"))

    ttl = tables.Column("ttl",
                        verbose_name=_("TTL"))

    serial = tables.Column("serial",
                           verbose_name=_("Serial"))

    class Meta:
        name = "domains"
        verbose_name = _("Domains")
        table_actions = (CreateDomain, DeleteDomain,)
        row_actions = (ManageRecords, EditDomain, DeleteDomain,)


def update_record_link(record):
    '''Returns a link to the view for updating DNS records.'''

    return urlresolvers.reverse(
        "horizon:project:dns_domains:update_record",
        args=(record.domain_id, record.id))


class RecordsTable(tables.DataTable):

    '''Data table for displaying summary information for a domains records.'''

    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link=update_record_link,
                         link_classes=('ajax-modal',)
                         )

    type = tables.Column("type",
                         verbose_name=_("Type")
                         )

    data = tables.Column("data",
                         verbose_name=_("Data")
                         )

    priority = tables.Column("priority",
                             verbose_name=_("Priority"),
                             )

    ttl = tables.Column("ttl",
                        verbose_name=_("TTL")
                        )

    class Meta:
        name = "records"
        verbose_name = _("Records")
        table_actions = (CreateRecord,)
        row_actions = (EditRecord, DeleteRecord,)
        multi_select = False

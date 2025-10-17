# Copyright 2018 Red Hat Inc.
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

from oslo_upgradecheck import common_checks
from oslo_upgradecheck import upgradecheck
from sqlalchemy import MetaData, Table, select, func

import designate.conf
from designate.i18n import _
from designate.storage import sql
# This import is not used, but is needed to register the storage:sqlalchemy
# group.
import designate.storage.sqlalchemy  # noqa
from designate import utils


class Checks(upgradecheck.UpgradeCommands):
    def _duplicate_service_status(self):
        engine = sql.get_read_engine()
        metadata = MetaData()
        metadata.bind = engine

        status = Table('service_statuses', metadata, autoload_with=engine)
        service_select = (
            select(func.count())
            .select_from(status)
            .group_by('service_name', 'hostname')
        )

        with sql.get_read_session() as session:
            service_counts = session.execute(service_select).fetchall()

        duplicated_services = [i for i in service_counts if i[0] > 1]
        if duplicated_services:
            return upgradecheck.Result(upgradecheck.Code.FAILURE,
                                       _('Duplicated services found in '
                                         'service_statuses table.'))
        return upgradecheck.Result(upgradecheck.Code.SUCCESS)

    _upgrade_checks = ((_('Duplicate service status'),
                        _duplicate_service_status),
                       (_('Policy File JSON to YAML Migration'),
                        (common_checks.check_policy_json,
                         {'conf': designate.conf.CONF})),
                       )


def main():
    config_files = utils.find_config('designate.conf')
    checker = Checks()
    return upgradecheck.main(
        conf=designate.conf.CONF,
        project='designate',
        upgrade_command=checker,
        default_config_files=config_files,
    )

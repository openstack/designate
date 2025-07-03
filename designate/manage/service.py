# Copyright (c) 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import timeutils

import designate.conf
from designate.manage import base
from designate import rpc
from designate import storage


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class ServiceCommands(base.Commands):
    def __init__(self):
        super().__init__()
        self.heartbeat_interval = None
        self.storage = storage.get_storage()

    def clean(self):
        rpc.init(CONF)
        self.heartbeat_interval = CONF.heartbeat_emitter.heartbeat_interval
        LOG.info("Start cleaning dead services.")
        try:
            statuses = self.storage.find_service_statuses(self.context)
            for status in statuses:
                if status.heartbeated_at:
                    # Clean stale servcie if it pass 2*(heartbeat_interval)
                    check_interval = (
                        timeutils.utcnow() - status.heartbeated_at
                    ).total_seconds()
                    if check_interval > 2 * self.heartbeat_interval:
                        LOG.warning("Found dead service for delete: "
                                    "%(service_name)s. "
                                    "Last service heartbeat time is "
                                    "%(check_interval)s seconds ago.",
                                    {
                                        'service_name': status.service_name,
                                        'check_interval': check_interval
                                    }
                                    )
                        self.storage.delete_service_status(
                            self.context, status)
        except messaging.exceptions.MessagingTimeout:
            LOG.critical(
                'No response received from designate-central. '
                'Check it is running, and retry'
            )
            raise SystemExit(1)

        LOG.info("Job finished.")

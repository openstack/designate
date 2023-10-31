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

import collections
import functools
import itertools
import threading

from oslo_log import log as logging

from designate import context as designate_context
from designate import notifications

LOG = logging.getLogger(__name__)


class NotificationThreadLocal(threading.local):
    def __init__(self):
        super().__init__()
        self.stack = 0
        self.queue = collections.deque()

    def reset_queue(self):
        self.queue.clear()


def notify_type(notification_type):
    def outer(f):
        @functools.wraps(f)
        def notification_wrapper(cls, *args, **kwargs):
            cls.notification_thread_local.stack += 1

            context = None
            for arg in itertools.chain(args, kwargs.values()):
                if isinstance(arg, designate_context.DesignateContext):
                    context = arg
                    break

            try:
                result = f(cls, *args, **kwargs)

                payloads = notifications.get_plugin().emit(
                    notification_type, context, result, args, kwargs
                )
                for payload in payloads:
                    LOG.debug(
                        'Queueing notification for %(type)s',
                        {
                            'type': notification_type
                        }
                    )
                    cls.notification_thread_local.queue.appendleft(
                        (context, notification_type, payload,)
                    )

                return result

            finally:
                cls.notification_thread_local.stack -= 1

                if cls.notification_thread_local.stack == 0:
                    LOG.debug(
                        'Emitting %(count)d notifications',
                        {
                            'count': len(cls.notification_thread_local.queue)
                        }
                    )

                    for message in cls.notification_thread_local.queue:
                        LOG.debug(
                            'Emitting %(type)s notification',
                            {
                                'type': message[1]
                            }
                        )
                        cls.notifier.info(message[0], message[1], message[2])

                    cls.notification_thread_local.reset_queue()

        return notification_wrapper
    return outer

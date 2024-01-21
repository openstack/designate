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

import functools
import itertools
import threading

from oslo_log import log as logging

from designate import objects

LOG = logging.getLogger(__name__)


class ZoneLockLocal(threading.local):
    def __init__(self):
        super().__init__()
        self._held = set()

    def hold(self, name):
        self._held.add(name)

    def release(self, name):
        self._held.remove(name)

    def has_lock(self, name):
        return name in self._held


def extract_zone_id(args, kwargs):
    zone_id = None

    if 'zone_id' in kwargs:
        zone_id = kwargs['zone_id']
    elif 'zone' in kwargs:
        zone_id = kwargs['zone'].id
    elif 'recordset' in kwargs:
        zone_id = kwargs['recordset'].zone_id
    elif 'record' in kwargs:
        zone_id = kwargs['record'].zone_id

    if not zone_id:
        for arg in itertools.chain(args, kwargs.values()):
            if not isinstance(arg, objects.DesignateObject):
                continue
            elif isinstance(arg, objects.Zone):
                zone_id = arg.id
                if zone_id:
                    break
            elif isinstance(arg, (objects.RecordSet,
                                  objects.Record,
                                  objects.ZoneTransferRequest,
                                  objects.ZoneTransferAccept)):
                zone_id = arg.zone_id
                if zone_id:
                    break

    if not zone_id and len(args) > 1:
        arg = args[1]
        if isinstance(arg, str):
            zone_id = arg

    return zone_id


def synchronized_zone(new_zone=False):
    """Ensures only a single operation is in progress for each zone

    A Decorator which ensures only a single operation can be happening
    on a single zone at once, within the current designate-central instance
    """
    def outer(f):
        @functools.wraps(f)
        def sync_wrapper(cls, *args, **kwargs):
            if new_zone is True:
                lock_name = b'create-new-zone'
            else:
                zone_id = extract_zone_id(args, kwargs)
                if zone_id:
                    lock_name = f'zone-{zone_id}'.encode('ascii')
                else:
                    raise Exception('Failed to determine zone id for '
                                    'synchronized operation')

            if cls.zone_lock_local.has_lock(lock_name):
                return f(cls, *args, **kwargs)

            with cls.coordination.get_lock(lock_name):
                try:
                    cls.zone_lock_local.hold(lock_name)
                    return f(cls, *args, **kwargs)
                finally:
                    cls.zone_lock_local.release(lock_name)

        return sync_wrapper
    return outer

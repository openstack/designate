# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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

"""
Unit test utilities
"""


class RoObject:
    """Read-only object: raise exception on unexpected
    __setitem__ or __setattr__
    """
    def __init__(self, d=None, **kw):
        if d:
            kw.update(d)

        self.__dict__.update(kw)

    def __getitem__(self, k):
        try:
            return self.__dict__[k]
        except KeyError:
            raise NotImplementedError(
                "Attempt to perform __getitem__"
                " %r on RoObject %r" % (k, self.__dict__)
            )

    def __setitem__(self, k, v):
        raise NotImplementedError(
            "Attempt to perform __setitem__ or __setattr__"
            " %r on RoObject %r" % (k, self.__dict__)
        )

    def __setattr__(self, k, v):
        self.__setitem__(k, v)

    def __iter__(self):
        for k in self.__dict__:
            yield k, self.__dict__[k]

    def to_dict(self):
        return self.__dict__


class RwObject:
    """Object mock: raise exception on __setitem__ or __setattr__
    on any item/attr created after initialization.
    Allows updating existing items/attrs
    """
    def __init__(self, d=None, **kw):
        if d:
            kw.update(d)
        self.__dict__.update(kw)

    def __getitem__(self, k):
        try:
            return self.__dict__[k]
        except KeyError:
            cn = self.__class__.__name__
            raise NotImplementedError(
                "Attempt to perform __getitem__"
                " %r on %s %r" % (cn, k, self.__dict__)
            )

    def __setitem__(self, k, v):
        if k in self.__dict__:
            self.__dict__.update({k: v})
            return

        cn = self.__class__.__name__
        raise NotImplementedError(
            "Attempt to perform __setitem__ or __setattr__"
            " %r on %s %r" % (cn, k, self.__dict__)
        )

    def __setattr__(self, k, v):
        self.__setitem__(k, v)

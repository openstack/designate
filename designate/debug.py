# Copyright 2013 Hewlett-Packard Development Company, L.P. All Rights Reserved.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
import cProfile
import functools
import tempfile
import pstats


def profile(lines=20, sort='cumtime'):
    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            f = tempfile.NamedTemporaryFile()

            # Profile the function
            prof = cProfile.Profile()
            result = prof.runcall(func, *args, **kwargs)
            prof.dump_stats(f.name)

            # Read the results, and print the stats
            stats = pstats.Stats(f.name)
            stats.sort_stats(sort).print_stats(lines)

            return result
        return inner
    return outer

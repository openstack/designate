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
import collections
import functools
import time

import six
import netaddr


def def_method(f, *args, **kwargs):
    @functools.wraps(f)
    def new_method(self):
        return f(self, *args, **kwargs)
    return new_method


def parameterized_class(cls):
    """A class decorator for running parameterized test cases.

    Mark your class with @parameterized_class.
    Mark your test cases with @parameterized.
    """
    test_functions = {
        k: v for k, v in vars(cls).items() if k.startswith('test')
    }
    for name, f in test_functions.items():
        if not hasattr(f, '_test_data'):
            continue

        # remove the original test function from the class
        delattr(cls, name)

        # add a new test function to the class for each entry in f._test_data
        for tag, args in f._test_data.items():
            new_name = "{0}_{1}".format(f.__name__, tag)
            if hasattr(cls, new_name):
                raise Exception(
                    "Parameterized test case '{0}.{1}' created from '{0}.{2}' "
                    "already exists".format(cls.__name__, new_name, name))

            # Using `def new_method(self): f(self, **args)` is not sufficient
            # (all new_methods use the same args value due to late binding).
            # Instead, use this factory function.
            new_method = def_method(f, **args)

            # To add a method to a class, available for all instances:
            #   MyClass.method = types.MethodType(f, None, MyClass)
            setattr(cls, new_name, six.create_unbound_method(new_method, cls))
    return cls


def parameterized(data):
    """A function decorator for parameterized test cases.

    Example:

        @parameterized({
            'zero': dict(val=0),
            'one': dict(val=1),
        })
        def test_val(self, val):
            self.assertEqual(self.get_val(), val)

    The above will generate two test cases:
        `test_val_zero` which runs with val=0
        `test_val_one` which runs with val=1

    :param data: A dictionary that looks like {tag: {arg1: val1, ...}}
    """
    def wrapped(f):
        f._test_data = data
        return f
    return wrapped


def wait_for_condition(condition, interval=5, timeout=45):
    end_time = time.time() + timeout
    while time.time() < end_time:
        result = condition()
        if result:
            return result
        time.sleep(interval)
    raise Exception("Timed out after {0} seconds".format(timeout))


def memoized(func):
    """A decorator to cache function's return value"""
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        if not isinstance(args, collections.Hashable):
            # args is not cacheable. just call the function.
            return func(*args)
        if args in cache:
            return cache[args]
        else:
            value = func(*args)
            cache[args] = value
            return value
    return wrapper


def shorten_ipv6_addrs(addrs):
    """Shorten ipv6 addresses"""
    new_addrs = []
    for a in addrs:
        an = netaddr.IPAddress(a, version=6)
        new_addrs.append(an.format(netaddr.ipv6_compact))
    return new_addrs

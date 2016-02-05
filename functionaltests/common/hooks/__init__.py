"""
Copyright 2016 Rackspace

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

# a dictionary mapping the class name to the hook class
_HOOKS = {}


def register_hook(cls):
    """Register the request hook. This does not enable the hook. Hooks are
    enable via the config file.

    Usage:
        >>> register_hook(MyHook)
    """
    _HOOKS[cls.__name__] = cls


def get_class(name):
    """Get a hook class by it's class name:

    Usage:
        >>> get_hook_class('MyHook')
    """
    return _HOOKS.get(name)

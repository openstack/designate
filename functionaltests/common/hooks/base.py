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


class BaseRequestHook(object):
    """When writing your own hook, do three things:

        1. Implement this hook interface
        2. Register your hook in a global lookup using hook.register_hook()
        3. Specify the name of your hook in a config file

    A new instance of a hook is created before for each request, for storing
    per request state if you want.
    """

    def before(self, req_args, req_kwargs):
        """A hook called before each request

        :param req_args: a list (mutable)
        :param req_kwargs: a dictionary
        """
        pass

    def after(self, resp, resp_body):
        """A hook called after each request"""
        pass

    def on_exception(self, exception):
        """A hook called when an exception occurs on a request"""
        pass

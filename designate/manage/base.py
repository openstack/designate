# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import abc
from cliff.command import Command as CliffCommand
from designate.context import DesignateContext


class Command(CliffCommand):
    __metaclass__ = abc.ABCMeta

    def run(self, parsed_args):
        self.context = DesignateContext.get_admin_context(
            request_id="designate-manage")

        return super(Command, self).run(parsed_args)

    @abc.abstractmethod
    def execute(self, parsed_args):
        """
        Execute something, this is since we overload self.take_action()
        in order to format the data

        This method __NEEDS__ to be overloaded!

        :param parsed_args: The parsed args that are given by take_action()
        """

    def post_execute(self, data):
        """
        Format the results locally if needed, by default we just return data

        :param data: Whatever is returned by self.execute()
        """
        return data

    def take_action(self, parsed_args):
        # TODO(kiall): Common Exception Handling Here
        results = self.execute(parsed_args)
        return self.post_execute(results)

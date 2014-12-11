# flake8: noqa
# Copyright (c) <2011>, Jonathan LaCour
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import inspect

import six
import pecan
import pecan.rest
import pecan.routing

from designate import exceptions
from designate.central import rpcapi as central_rpcapi
from designate.openstack.common import log as logging
from designate.i18n import _


LOG = logging.getLogger(__name__)


class RestController(pecan.rest.RestController):
    """
    Extension for Pecan's RestController to better handle POST/PUT/PATCH
    requests.

    Ideally, we get these additions merged upstream.
    """

    # default sort_keys.  The Controllers can override this.
    SORT_KEYS = ['created_at', 'id']

    @property
    def central_api(self):
        return central_rpcapi.CentralAPI.get_instance()

    def _get_paging_params(self, params):
        """
        Extract any paging parameters
        """
        marker = params.pop('marker', None)
        limit = params.pop('limit', None)
        sort_key = params.pop('sort_key', None)
        sort_dir = params.pop('sort_dir', None)

        # Negative and zero limits are not caught in storage.
        # With a number bigger than MAXSIZE, rpc throws an 'OverflowError long
        #  too big to convert'.
        # So the parameter 'limit' is checked here.
        if limit:
            try:
                invalid_limit_message = _(str.format(
                    'limit should be an integer between 1 and {0}',
                    six.MAXSIZE))
                int_limit = int(limit)
                if int_limit <= 0 or int_limit > six.MAXSIZE:
                    raise exceptions.InvalidLimit(invalid_limit_message)
            # This exception is raised for non ints when int(limit) is called
            except ValueError:
                raise exceptions.InvalidLimit(invalid_limit_message)

        # sort_dir is checked in paginate_query.
        # We duplicate the sort_dir check here to throw a more specific
        # exception than ValueError.
        if sort_dir and sort_dir not in ['asc', 'desc']:
            raise exceptions.InvalidSortDir(_("Unknown sort direction, "
                                              "must be 'desc' or 'asc'"))

        if sort_key and sort_key not in self.SORT_KEYS:
            raise exceptions.InvalidSortKey(_(str.format(
                'sort key must be one of {0}', str(self.SORT_KEYS))))

        return marker, limit, sort_key, sort_dir

    def _apply_filter_params(self, params, accepted_filters, criterion):

        for k in accepted_filters:
            if k in params:
                criterion[k] = params[k]

        return criterion

    def _handle_post(self, method, remainder):
        '''
        Routes ``POST`` actions to the appropriate controller.
        '''
        # route to a post_all or get if no additional parts are available
        if not remainder or remainder == ['']:
            controller = self._find_controller('post_all', 'post')
            if controller:
                return controller, []
            pecan.abort(405)

        controller = getattr(self, remainder[0], None)
        if controller and not inspect.ismethod(controller):
            return pecan.routing.lookup_controller(controller, remainder[1:])

        # finally, check for the regular post_one/post requests
        controller = self._find_controller('post_one', 'post')
        if controller:
            return controller, remainder

        pecan.abort(405)

    def _handle_patch(self, method, remainder):
        '''
        Routes ``PATCH`` actions to the appropriate controller.
        '''
        # route to a patch_all or get if no additional parts are available
        if not remainder or remainder == ['']:
            controller = self._find_controller('patch_all', 'patch')
            if controller:
                return controller, []
            pecan.abort(405)

        controller = getattr(self, remainder[0], None)
        if controller and not inspect.ismethod(controller):
            return pecan.routing.lookup_controller(controller, remainder[1:])

        # finally, check for the regular patch_one/patch requests
        controller = self._find_controller('patch_one', 'patch')
        if controller:
            return controller, remainder

        pecan.abort(405)

    def _handle_put(self, method, remainder):
        '''
        Routes ``PUT`` actions to the appropriate controller.
        '''
        # route to a put_all or get if no additional parts are available
        if not remainder or remainder == ['']:
            controller = self._find_controller('put_all', 'put')
            if controller:
                return controller, []
            pecan.abort(405)

        controller = getattr(self, remainder[0], None)
        if controller and not inspect.ismethod(controller):
            return pecan.routing.lookup_controller(controller, remainder[1:])

        # finally, check for the regular put_one/put requests
        controller = self._find_controller('put_one', 'put')
        if controller:
            return controller, remainder

        pecan.abort(405)

    def _handle_delete(self, method, remainder):
        '''
        Routes ``DELETE`` actions to the appropriate controller.
        '''
        # route to a delete_all or get if no additional parts are available
        if not remainder or remainder == ['']:
            controller = self._find_controller('delete_all', 'delete')
            if controller:
                return controller, []
            pecan.abort(405)

        controller = getattr(self, remainder[0], None)
        if controller and not inspect.ismethod(controller):
            return pecan.routing.lookup_controller(controller, remainder[1:])

        # finally, check for the regular delete_one/delete requests
        controller = self._find_controller('delete_one', 'delete')
        if controller:
            return controller, remainder

        pecan.abort(405)

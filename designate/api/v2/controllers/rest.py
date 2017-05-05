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

import pecan
import pecan.rest
import pecan.routing

from designate import exceptions
from designate.central import rpcapi as central_rpcapi
from designate.pool_manager import rpcapi as pool_mgr_rpcapi
from designate.i18n import _


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

    @property
    def pool_mgr_api(self):
        return pool_mgr_rpcapi.PoolManagerAPI.get_instance()

    def _apply_filter_params(self, params, accepted_filters, criterion):
        invalid = []
        for k in params:
            if k in accepted_filters:
                criterion[k] = params[k].replace("*", "%")
            else:
                invalid.append(k)
        if invalid:
            raise exceptions.BadRequest(
                'Invalid filters %s' % ', '.join(invalid))
        else:
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

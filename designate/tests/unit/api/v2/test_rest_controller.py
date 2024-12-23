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

from unittest import mock

import oslotest.base
from webob import exc

from designate.api.v2.controllers import rest
from designate import exceptions


class TestRestController(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

        self.controller = rest.RestController()

    def test_handle_post(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = mock.Mock()

        self.assertEqual(
            (mock.ANY, []), self.controller._handle_post(mock.Mock(), None)
        )

    def test_handle_patch(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = mock.Mock()

        self.assertEqual(
            (mock.ANY, []), self.controller._handle_patch(mock.Mock(), None)
        )

    def test_handle_put(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = mock.Mock()

        self.assertEqual(
            (mock.ANY, []), self.controller._handle_put(mock.Mock(), None)
        )

    def test_handle_delete(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = mock.Mock()

        self.assertEqual(
            (mock.ANY, []), self.controller._handle_delete(mock.Mock(), None)
        )

    def test_handle_post_method_not_allowed(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = None

        self.assertRaisesRegex(
            exc.HTTPMethodNotAllowed,
            'The server could not comply with the request since it is either '
            'malformed or otherwise incorrect.',
            self.controller._handle_post, mock.Mock(), None
        )

    def test_handle_patch_method_not_allowed(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = None

        self.assertRaisesRegex(
            exc.HTTPMethodNotAllowed,
            'The server could not comply with the request since it is either '
            'malformed or otherwise incorrect.',
            self.controller._handle_patch, mock.Mock(), None
        )

    def test_handle_put_method_not_allowed(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = None

        self.assertRaisesRegex(
            exc.HTTPMethodNotAllowed,
            'The server could not comply with the request since it is either '
            'malformed or otherwise incorrect.',
            self.controller._handle_put, mock.Mock(), None
        )

    def test_handle_delete_method_not_allowed(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = None

        self.assertRaisesRegex(
            exc.HTTPMethodNotAllowed,
            'The server could not comply with the request since it is either '
            'malformed or otherwise incorrect.',
            self.controller._handle_delete, mock.Mock(), None
        )

    def test_handle_post_controller_not_found(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = None

        self.assertRaisesRegex(
            exc.HTTPMethodNotAllowed,
            'The server could not comply with the request since it is either '
            'malformed or otherwise incorrect.',
            self.controller._handle_post, mock.Mock(), ['fake']
        )

    def test_handle_patch_controller_not_found(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = None

        self.assertRaisesRegex(
            exc.HTTPMethodNotAllowed,
            'The server could not comply with the request since it is either '
            'malformed or otherwise incorrect.',
            self.controller._handle_patch, mock.Mock(), ['fake']
        )

    def test_handle_put_controller_not_found(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = None

        self.assertRaisesRegex(
            exc.HTTPMethodNotAllowed,
            'The server could not comply with the request since it is either '
            'malformed or otherwise incorrect.',
            self.controller._handle_put, mock.Mock(), ['fake']
        )

    def test_handle_delete_controller_not_found(self):
        self.controller._find_controller = mock.Mock()
        self.controller._find_controller.return_value = None

        self.assertRaisesRegex(
            exc.HTTPMethodNotAllowed,
            'The server could not comply with the request since it is either '
            'malformed or otherwise incorrect.',
            self.controller._handle_delete, mock.Mock(), ['fake']
        )


class TestFilterParams(oslotest.base.BaseTestCase):

    def test_invalid_filter_parameters(self):
        exc = self.assertRaises(
            exceptions.BadRequest,
            rest.RestController._apply_filter_params,
            {'alpha': 'foo', 'beta': 'bar'},
            ['alpha'],
            {},
        )
        self.assertIn('Invalid filters', str(exc))

    def test_duplicate_filter_parameters(self):
        exc = self.assertRaises(
            exceptions.BadRequest,
            rest.RestController._apply_filter_params,
            {'alpha': ['foo', 'baz'], 'beta': 'bar'},
            ['alpha', 'beta'],
            {},
        )
        self.assertIn('Duplicate filters', str(exc))

    def test_valid_filter_parameters(self):
        rest.RestController._apply_filter_params(
            {'alpha': 'foo', 'beta': 'bar'},
            ['alpha', 'beta'],
            {},
        )

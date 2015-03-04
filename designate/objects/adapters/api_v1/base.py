# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from oslo_log import log as logging

from designate.objects.adapters import base

LOG = logging.getLogger(__name__)


class APIv1Adapter(base.DesignateAdapter):

    ADAPTER_FORMAT = 'API_v1'

    #####################
    # Rendering methods #
    #####################

    @classmethod
    def render(cls, object, *args, **kwargs):
        return super(APIv1Adapter, cls).render(
            cls.ADAPTER_FORMAT, object, *args, **kwargs)

    @classmethod
    def _render_list(cls, list_object, *args, **kwargs):
        inner = cls._render_inner_list(list_object, *args, **kwargs)

        return {cls.MODIFICATIONS['options']['collection_name']: inner}

    @classmethod
    def _render_object(cls, object, *args, **kwargs):
        return cls._render_inner_object(object, *args, **kwargs)

    #####################
    #  Parsing methods  #
    #####################

    @classmethod
    def parse(cls, values, output_object, *args, **kwargs):
        return super(APIv1Adapter, cls).parse(
            cls.ADAPTER_FORMAT, values, output_object, *args, **kwargs)

    @classmethod
    def _parse_list(cls, values, output_object, *args, **kwargs):
        return cls._parse_inner_list(values, output_object, *args, **kwargs)

    @classmethod
    def _parse_object(cls, values, output_object, *args, **kwargs):
        return cls._parse_inner_object(values, output_object, *args, **kwargs)

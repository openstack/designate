# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from django.conf.urls import url, patterns  # noqa

from .views import CreateDomainView  # noqa
from .views import CreateRecordView  # noqa
from .views import DomainDetailView  # noqa
from .views import IndexView  # noqa
from .views import RecordsView  # noqa
from .views import UpdateDomainView  # noqa
from .views import UpdateRecordView  # noqa
from .views import ViewRecordDetailsView  # noqa


urlpatterns = patterns(
    '',
    url(r'^$',
        IndexView.as_view(),
        name='index'),
    url(r'^create/$',
        CreateDomainView.as_view(),
        name='create_domain'),
    url(r'^(?P<domain_id>[^/]+)/update$',
        UpdateDomainView.as_view(),
        name='update_domain'),
    url(r'^(?P<domain_id>[^/]+)$',
        DomainDetailView.as_view(),
        name='domain_detail'),
    url(r'^(?P<domain_id>[^/]+)/records$',
        RecordsView.as_view(),
        name='records'),
    url(r'^(?P<domain_id>[^/]+)/records/create$',
        CreateRecordView.as_view(),
        name='create_record'),
    url(r'^(?P<domain_id>[^/]+)/records/(?P<record_id>[^/]+)/update$',
        UpdateRecordView.as_view(),
        name='update_record'),
    url(r'^(?P<domain_id>[^/]+)/records/(?P<record_id>[^/]+)/$',
        ViewRecordDetailsView.as_view(),
        name='view_record'),
)

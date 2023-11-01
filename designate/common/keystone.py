#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from keystoneauth1 import exceptions as kse
from keystoneauth1 import loading as ksa_loading
from oslo_log import log as logging

import designate.conf
from designate import exceptions
from designate.i18n import _


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


def verify_project_id(context, project_id):
    """verify that a project_id exists.

    This attempts to verify that a project id exists. If it does not,
    an HTTPBadRequest is emitted.

    """
    session = ksa_loading.load_session_from_conf_options(
        CONF, 'keystone', auth=context.get_auth_plugin()
    )
    adapter = ksa_loading.load_adapter_from_conf_options(
        CONF, 'keystone',
        session=session, min_version=(3, 0), max_version=(3, 'latest')
    )
    try:
        response = adapter.get('/projects/%s' % project_id, raise_exc=False)
    except kse.EndpointNotFound:
        LOG.error(
            'Keystone identity service version 3.0 was not found. This might '
            'be because your endpoint points to the v2.0 versioned endpoint '
            'which is not supported. Please fix this.'
        )
        raise exceptions.KeystoneCommunicationFailure(
            _('KeystoneV3 endpoint not found')
        )
    except kse.ClientException:
        # something is wrong, like there isn't a keystone v3 endpoint,
        # or nova isn't configured for the interface to talk to it;
        # we'll take the pass and default to everything being ok.
        LOG.info('Unable to contact keystone to verify project_id')
        return True

    if response.ok:
        # All is good with this 20x status
        return True
    elif response.status_code == 403:
        # we don't have enough permission to verify this, so default
        # to "it's ok".
        LOG.info(
            'Insufficient permissions for user %(user)s to verify '
            'existence of project_id %(pid)s',
            {
                'user': context.user_id,
                'pid': project_id
            }
        )
        return True
    elif response.status_code == 404:
        # we got access, and we know this project is not there
        raise exceptions.InvalidProject(
            _('%s is not a valid project ID.') % project_id
        )
    else:
        LOG.warning(
            'Unexpected response from keystone trying to '
            'verify project_id %(pid)s - response: %(code)s %(content)s',
            {
                'pid': project_id,
                'code': response.status_code,
                'content': response.content
            }
        )
        return True

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
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate.openstack.common import policy
from designate import utils
from designate import exceptions

LOG = logging.getLogger(__name__)

cfg.CONF.register_opts([
    cfg.StrOpt('policy-file', default='policy.json'),
    cfg.StrOpt('policy-default-rule', default='default'),
])


def init_policy():
    LOG.info('Initializing Policy')

    policy_files = utils.find_config(cfg.CONF.policy_file)

    if len(policy_files) == 0:
        msg = 'Unable to determine appropriate policy json file'
        raise exceptions.ConfigurationError(msg)

    LOG.info('Using policy_file found at: %s' % policy_files[0])

    with open(policy_files[0]) as fh:
        policy_json = fh.read()

    rules = policy.Rules.load_json(policy_json, cfg.CONF.policy_default_rule)

    policy.set_rules(rules)


def check(rule, ctxt, target={}, exc=exceptions.Forbidden):
    creds = ctxt.to_dict()

    try:
        result = policy.check(rule, target, creds, exc)
    except Exception:
        result = False
        raise
    else:
        return result
    finally:
        extra = {'policy': {'rule': rule, 'target': target}}

        if result:
            LOG.audit("Policy check succeeded for rule '%s' on target %s",
                      rule, repr(target), extra=extra)
        else:
            LOG.audit("Policy check failed for rule '%s' on target: %s",
                      rule, repr(target), extra=extra)

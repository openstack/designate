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
from oslo_config import cfg
from oslo_log import log as logging
from oslo_policy import opts
from oslo_policy import policy

from designate.common import policies
from designate import exceptions


CONF = cfg.CONF

# Add the default policy opts
# TODO(gmann): Remove setting the default value of config policy_file
# once oslo_policy change the default value to 'policy.yaml'.
# https://github.com/openstack/oslo.policy/blob/a626ad12fe5a3abd49d70e3e5b95589d279ab578/oslo_policy/opts.py#L49
DEFAULT_POLICY_FILE = 'policy.yaml'
opts.set_defaults(CONF, DEFAULT_POLICY_FILE)

LOG = logging.getLogger(__name__)


_ENFORCER = None


def reset():
    global _ENFORCER
    if _ENFORCER:
        _ENFORCER.clear()
    _ENFORCER = None


def set_rules(data, default_rule=None, overwrite=True):
    default_rule = default_rule or cfg.CONF.policy_default_rule
    if not _ENFORCER:
        LOG.debug("Enforcer not present, recreating at rules stage.")
        init()

    if default_rule:
        _ENFORCER.default_rule = default_rule

    msg = "Loading rules %s, default: %s, overwrite: %s"
    LOG.debug(msg, data, default_rule, overwrite)

    if isinstance(data, dict):
        rules = policy.Rules.from_dict(data, default_rule)
    else:
        rules = policy.Rules.load_json(data, default_rule)

    _ENFORCER.set_rules(rules, overwrite=overwrite)


def init(default_rule=None, policy_file=None):
    global _ENFORCER
    if not _ENFORCER:
        LOG.debug("Enforcer is not present, recreating.")
        _ENFORCER = policy.Enforcer(CONF, policy_file=policy_file)
        _ENFORCER.register_defaults(policies.list_rules())


def check(rule, ctxt, target=None, do_raise=True, exc=exceptions.Forbidden):
    if enforce_new_defaults():
        creds = ctxt.to_policy_values()
    else:
        creds = ctxt.to_dict()
    target = target or {}
    try:
        result = _ENFORCER.enforce(rule, target, creds, do_raise, exc)
    except policy.InvalidScope:
        result = False
        if do_raise:
            raise exceptions.InvalidTokenScope
    except Exception:
        result = False
        raise
    else:
        return result
    finally:
        extra = {'policy': {'rule': rule, 'target': target}}

        if result:
            LOG.trace("Policy check succeeded for rule '%(rule)s' "
                      "on target %(target)s",
                      {'rule': rule, 'target': repr(target)}, extra=extra)
        else:
            LOG.info("Policy check failed for rule '%(rule)s' "
                     "on target %(target)s",
                     {'rule': rule, 'target': repr(target)}, extra=extra)


def enforce_new_defaults():
    if CONF.get('oslo_policy'):
        return CONF['oslo_policy'].get('enforce_new_defaults', False)
    return False


def get_enforcer():
    # This method is used by oslopolicy CLI scripts in order to generate policy
    # files from overrides on disk and defaults in code.
    cfg.CONF([], project='designate')
    init()
    return _ENFORCER

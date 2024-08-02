==================
Designate Policies
==================

.. warning::

   JSON formatted policy file is deprecated since Designate 12.0.0 (Wallaby).
   This `oslopolicy-convert-json-to-yaml`__ tool will migrate your existing
   JSON-formatted policy file to YAML in a backward-compatible way.

.. __: https://docs.openstack.org/oslo.policy/latest/cli/oslopolicy-convert-json-to-yaml.html

.. _oslo policy: https://docs.openstack.org/oslo.policy/latest/

.. _Keystone Default Roles: https://docs.openstack.org/keystone/latest/admin/service-api-protection.html

.. _Keystone Scoped Tokens: https://docs.openstack.org/keystone/latest/admin/tokens-overview.html#authorization-scopes

Designate, like most OpenStack services, supports Role Based Access Control
(RBAC) using `oslo policy`_ to define default RBAC policies in the Designate
code. These default policies can be overridden by operators using a yaml policy
file. For a sample policy file, refer to :doc:`samples/policy-yaml`.

Currently Designate defaults to the OpenStack legacy "admin or owner" scheme,
but Designate also supports a newer RBAC model using `Keystone Default Roles`_
and `Keystone Scoped Tokens`_ via configuration settings.

Enabling Keystone Default Roles and Scoped Tokens
-------------------------------------------------

Starting with the Xena release of Designate, Keystone token scopes and
default roles can be enforced. By default, in the Xena release, `oslo policy`_
will not be enforcing these new roles and scopes. However, at some point in the
future they may become the default. You may want to enable them now to be ready
for the later transition. This section will describe those settings.

The Oslo Policy project defines two configuration settings, among others, that
can be set in the Designate configuration file to influence how policies are
handled by Designate. Those two settings are `enforce_scope
<https://docs.openstack.org/oslo.policy/latest/configuration/index.html#oslo_policy.enforce_scope>`_ and `enforce_new_defaults
<https://docs.openstack.org/oslo.policy/latest/configuration/index.html#oslo_policy.enforce_new_defaults>`_.

When you enable `Keystone Default Roles`_ and `Keystone Scoped Tokens`_ the
Designate policy honors the following roles:

* Admin
* Project scoped - Reader
* Project scoped - Member

[oslo_policy] enforce_scope
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Keystone has introduced the concept of `token scopes
<https://docs.openstack.org/keystone/latest/admin/tokens-overview.html#authorization-scopes>`_.
To ensure backward compatibility, Oslo Policy does not enforce scope validation
of tokens by default.

In the Xena release, Designate supports enforcing Keystone token scopes. To
enable Keystone token scoping, add the following to your Designate
configuration file::

    [oslo_policy]
    enforce_scope = True

The primary effect of this setting is to allow only project scoped calls
to the Designate API. The system scope token will return 403.

[oslo_policy] enforce_new_defaults
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Designate Xena release added support for `Keystone Default Roles`_ in
the default policies.
To be backward compatible, Oslo Policy currently uses deprecated policies
that do not require the new `Keystone Default Roles`_ by default.

Designate supports requiring these new `Keystone Default Roles`_ as of
the Xena release. To start requiring these roles in Designate, enable the new
policies by adding the following setting to your Designate configuration file::

    [oslo_policy]
    enforce_new_defaults = True

Oslo Tools For Policy Management
--------------------------------

This section describes how to use Oslo Policy tools to managing Designate
policies.

Sample File Generation
~~~~~~~~~~~~~~~~~~~~~~

To generate a sample policy.yaml file from the Designate defaults, run the
oslo policy generation script::

    oslopolicy-sample-generator
    --config-file etc/designate/designate-policy-generator.conf
    --output-file policy.yaml.sample

Merged File Generation
~~~~~~~~~~~~~~~~~~~~~~

To generate a policy file which shows the effective policy in use by the
project, including all registered policy defaults and the policy overrides
included in a policy.yaml file, run this command::

    oslopolicy-policy-generator
    --config-file etc/designate/designate-policy-generator.conf

This tool uses the output_file path from the config-file.

List Redundant Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To generate a list of matches for policy rules that are defined in a
configuration file where the rule does not differ from a registered default
rule, run this command::

    oslopolicy-list-redundant
    --config-file etc/designate/designate-policy-generator.conf

These are rules that can be removed from the policy file with no change
in effective policy.


Designate Default Policy Overview
---------------------------------

The following is an overview of all available policies in Designate. For a
sample configuration file, refer to :doc:`samples/policy-yaml`.

.. show-policy::
   :config-file: ../../etc/designate/designate-policy-generator.conf

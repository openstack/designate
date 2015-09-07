# Copyright 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2012, Cloudscaling
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
import re

import pep8


# D701: Default parameter value is a mutable type
# D702: Log messages require translation
# D703: Found use of _() without explicit import of _!
# D704: Found import of %s. This oslo library has been graduated!
# D705: timeutils.utcnow() must be used instead of datetime.%s()
# D706: Don't translate debug level logs
# D707: basestring is not Python3-compatible, use six.string_types instead.
# D708: Do not use xrange. Use range, or six.moves.range for large loops.
# D709: LOG.audit is deprecated, please use LOG.info!


UNDERSCORE_IMPORT_FILES = []


mutable_default_argument_check = re.compile(
    r"^\s*def .+\((.+=\{\}|.+=\[\])")
string_translation = re.compile(r"[^_]*_\(\s*('|\")")
log_translation = re.compile(
    r"(.)*LOG\.(audit|error|info|warn|warning|critical|exception)\(\s*('|\")")
translated_log = re.compile(
    r"(.)*LOG\.(audit|error|info|warn|warning|critical|exception)"
    "\(\s*_\(\s*('|\")")
underscore_import_check = re.compile(r"(.)*import _(.)*")
# We need this for cases where they have created their own _ function.
custom_underscore_check = re.compile(r"(.)*_\s*=\s*(.)*")
graduated_oslo_libraries_import_re = re.compile(
    r"^\s*(?:import|from) designate\.openstack\.common\.?.*?"
    "(gettextutils|rpc)"
    ".*?")


def mutable_default_arguments(logical_line, physical_line, filename):
    if pep8.noqa(physical_line):
        return

    if mutable_default_argument_check.match(logical_line):
        yield (0, "D701: Default parameter value is a mutable type")


def validate_log_translations(logical_line, physical_line, filename):
    # Translations are not required in the test directory
    if "designate/tests" in filename:
        return
    if pep8.noqa(physical_line):
        return
    msg = "D702: Log messages require translation"
    if log_translation.match(logical_line):
        yield (0, msg)


def no_translate_debug_logs(logical_line, filename):
    """Check for 'LOG.debug(_('
    As per our translation policy,
    https://wiki.openstack.org/wiki/LoggingStandards#Log_Translation
    we shouldn't translate debug level logs.
    * This check assumes that 'LOG' is a logger.
    * Use filename so we can start enforcing this in specific folders instead
      of needing to do so all at once.
    N319
    """
    if logical_line.startswith("LOG.debug(_("):
        yield(0, "D706: Don't translate debug level logs")


def check_explicit_underscore_import(logical_line, filename):
    """Check for explicit import of the _ function

    We need to ensure that any files that are using the _() function
    to translate logs are explicitly importing the _ function.  We
    can't trust unit test to catch whether the import has been
    added so we need to check for it here.
    """
    # Build a list of the files that have _ imported.  No further
    # checking needed once it is found.
    if filename in UNDERSCORE_IMPORT_FILES:
        pass
    elif (underscore_import_check.match(logical_line) or
          custom_underscore_check.match(logical_line)):
        UNDERSCORE_IMPORT_FILES.append(filename)
    elif (translated_log.match(logical_line) or
         string_translation.match(logical_line)):
        yield(0, "D703: Found use of _() without explicit import of _!")


def no_import_graduated_oslo_libraries(logical_line, filename):
    """Check that we don't continue to use o.c. oslo libraries after graduation

    After a library graduates from oslo-incubator, as we make the switch, we
    should ensure we don't continue to use the oslo-incubator versions.

    In many cases, it's not possible to immediately remove the code from the
    openstack/common folder due to dependency issues.
    """
    # We can't modify oslo-incubator code, so ignore it here.
    if "designate/openstack/common" in filename:
        return

    matches = graduated_oslo_libraries_import_re.match(logical_line)
    if matches:
        yield(0, "D704: Found import of %s. This oslo library has been "
                 "graduated!" % matches.group(1))


def use_timeutils_utcnow(logical_line, filename):
    # tools are OK to use the standard datetime module
    if "/tools/" in filename:
        return

    msg = "D705: timeutils.utcnow() must be used instead of datetime.%s()"

    datetime_funcs = ['now', 'utcnow']
    for f in datetime_funcs:
        pos = logical_line.find('datetime.%s' % f)
        if pos != -1:
            yield (pos, msg % f)


def check_no_basestring(logical_line):
    if re.search(r"\bbasestring\b", logical_line):
        msg = ("D707: basestring is not Python3-compatible, use "
               "six.string_types instead.")
        yield(0, msg)


def check_python3_xrange(logical_line):
    if re.search(r"\bxrange\s*\(", logical_line):
        yield(0, "D708: Do not use xrange. Use range, or six.moves.range for "
                 "large loops.")


def check_no_log_audit(logical_line):
    """Ensure that we are not using LOG.audit messages
    Plans are in place going forward as discussed in the following
    spec (https://review.openstack.org/#/c/132552/) to take out
    LOG.audit messages. Given that audit was a concept invented
    for OpenStack we can enforce not using it.
    """
    if "LOG.audit(" in logical_line:
        yield(0, "D709: LOG.audit is deprecated, please use LOG.info!")


def factory(register):
    register(mutable_default_arguments)
    register(validate_log_translations)
    register(no_translate_debug_logs)
    register(check_explicit_underscore_import)
    register(no_import_graduated_oslo_libraries)
    register(use_timeutils_utcnow)
    register(check_no_basestring)
    register(check_python3_xrange)
    register(check_no_log_audit)

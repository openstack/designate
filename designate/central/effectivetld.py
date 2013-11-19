# Copyright (c) 2013 Rackspace Hosting
# All Rights Reserved.
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

import codecs
import re
from designate import utils
from designate.openstack.common import log as logging
from oslo.config import cfg

LOG = logging.getLogger(__name__)


class EffectiveTld(object):
    def __init__(self, *args, **kwargs):
        self._load_accepted_tld_list()
        self._load_effective_tld_list()

    def _load_accepted_tld_list(self):
        """
        This loads the accepted TLDs from a file to a list - accepted_tld_list.
        The file is expected to have one TLD per line.  TLDs need to be in the
        IDN format.  Comments in the file are lines beginning with a #
        The normal source for this file is
        http://data.iana.org/TLD/tlds-alpha-by-domain.txt
        """
        self.accepted_tld_list = []
        accepted_tld_files = utils.find_config(
            cfg.CONF['service:central'].accepted_tlds_file)

        # We do not require the accepted_tld_files to be present to be
        # compatible with stable/havana release.
        if len(accepted_tld_files) == 0:
            LOG.info('Unable to determine appropriate accepted tlds file')
            return

        LOG.info('Using accepted_tld_file found at: %s'
                 % accepted_tld_files[0])

        with open(accepted_tld_files[0]) as fh:
            for line in fh:
                if line.startswith('#'):
                    continue
                line = line.strip()
                self.accepted_tld_list.append(line.lower())

        LOG.info("Entries in Accepted TLD List: %d"
                 % len(self.accepted_tld_list))
        # LOG.info("Accepted TLD List:\n%s" % self.accepted_tld_list)

    def _load_effective_tld_list(self):
        """
        This loads the effective TLDs from a file.  Effective TLDs are the SLDs
        that act as TLDs - e.g. co.uk.  The file is in UTF-8 format.
        The normal source for this file is at http://publicsuffix.org/list/
        The format of the file is:
        1. Lines beginning with a // or ! are ignored.
        2. The domain names are 1 per line.
        3. The wildcard character * (asterisk) may only be used to wildcard the
        topmost level in a domain name.

        The publicsuffix.org has more rules and !'s are treated differently but
        this code ignores those until we find that we need to do otherwise.

        The file is put into a dictionary and a list.  Domain names with only 1
        label are ignored as they are already present in the accepted_tld_list.
        All the entries are converted to IDN format.
        All the effective TLDs without a wildcard are put into a dictionary -
        _effective_tld_dict.
        The entries with a wildcard are converted to a regular expression and
        put into a separate list - _effective_re_tld_list.
        The separation to a dictionary and a regular expression list is done
        to make it easier for searching.
        The maximum labels in the dictionary and list are tracked to short
        circuit checks later as needed.
        """
        self._effective_tld_dict = {}

        # _max_effective_tld_labels tracks the maximum labels in the
        # dictionary self._effective_tld_dict
        # This helps to determine if we need to search the dictionary while
        # creating a domain
        self._max_effective_tld_labels = 0

        # The list _effective_re_tld_list contains domains with a *
        self._effective_re_tld_list = []

        # _max_effective_re_tld_labels tracks the maximum labels in the
        # list self._effective_re_tld_list
        self._max_effective_re_tld_labels = 0

        effective_tld_files = utils.find_config(
            cfg.CONF['service:central'].effective_tlds_file)

        # We do not require the effective_tld_file to be present to be
        # compatible with stable/havana release.
        if len(effective_tld_files) == 0:
            LOG.info('Unable to determine appropriate effective tlds file')
            return

        LOG.info('Using effective_tld_file found at: %s'
                 % effective_tld_files[0])

        with codecs.open(effective_tld_files[0], "r", "utf-8") as fh:
            for line in fh:
                line = line.strip()

                if line.startswith('//') or line.startswith('!') or not line:
                    continue
                labels_len = len(line.split('.'))

                # skip TLDs as they are already in the accepted_tld_list
                if labels_len == 1:
                    continue

                # Convert the public suffix list to idna format
                line = line.encode('idna')

                # Entries with wildcards go to a separate list.
                if (line.startswith('*')):
                    if labels_len > self._max_effective_re_tld_labels:
                        self._max_effective_re_tld_labels = labels_len

                    # Convert the wildcard entry to a regular expression
                    # The ^ and $ at the beginning and end respectively are to
                    # match the whole term.  The [^.]* is to match anything
                    # other than a "."  This is so that only one label is
                    # matched.  The rest of the label separators "." are
                    # escaped to match the "." and not any character.
                    self._effective_re_tld_list.append(
                        '^[^.]*' + '\.'.join(line.split('.'))[1:] + '$')
                    continue

                if labels_len > self._max_effective_tld_labels:
                    self._max_effective_tld_labels = labels_len

                # The rest of the entries go into a dictionary.
                self._effective_tld_dict[line.lower()] = 1

        LOG.info("Entries in Effective TLD List Dict: %d"
                 % len(self._effective_tld_dict))
        # LOG.info("Effective TLD Dict:\n%s" % self._effective_tld_dict)

        LOG.info("Entries in Effective RE TLD List: %d"
                 % len(self._effective_re_tld_list))
        # LOG.info("Effective RE TLD List:\n%s" % self._effective_re_tld_list)

    def is_effective_tld(self, domain_name):
        """
        Returns True if the domain_name is the same as an effective TLD else
        returns False.
        """
        # Break the domain name up into its component labels
        stripped_domain_name = domain_name.strip('.').lower()
        domain_labels = stripped_domain_name.split('.')

        if len(domain_labels) <= self._max_effective_tld_labels:
            # First search the dictionary
            if stripped_domain_name in self._effective_tld_dict.keys():
                return True

        # Now search the list of regular expressions for effective TLDs
        if len(domain_labels) <= self._max_effective_re_tld_labels:
            for eff_re_label in self._effective_re_tld_list:
                if bool(re.search(eff_re_label, stripped_domain_name)):
                    return True

        return False

# Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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
import dns

from debtcollector import removals

"""
    backend.private_codes
    ~~~~~~~~~~~~~~~~~~~~~~
    Private DNS opcodes, classes, RR codes for communication between the
    agent and its backends
"""

# Command and Control OPCODE
CC = 14

# Private DNS CLASS Uses
CLASSCC = 65280

# Private RR Code Uses
SUCCESS = 65280
FAILURE = 65281
CREATE = 65282
DELETE = 65283

# TODO(johnsom) Remove this after the agents framework is removed or the
#               protocol has been updated to not use an unassigned opcode(14).
#
# This is an Opcode Enum class that includes the unassigned[1][2]
# opcode 14 used in the Designate agent framework until the agent framework
# can be removed or fixed.
# [1] https://www.rfc-editor.org/rfc/rfc6895.html#section-2.2
# [2] https://www.iana.org/assignments/dns-parameters/
#     dns-parameters.xhtml#dns-parameters-5
#
# Based on dns.opcode.Opcode:
#
# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license
# Copyright (C) 2001-2017 Nominum, Inc.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose with or without fee is hereby granted,
# provided that the above copyright notice and this permission notice
# appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NOMINUM DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NOMINUM BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


@removals.removed_class("OpcodeWith14")
class OpcodeWith14(dns.enum.IntEnum):
    #: Query
    QUERY = 0
    #: Inverse Query (historical)
    IQUERY = 1
    #: Server Status (unspecified and unimplemented anywhere)
    STATUS = 2
    #: Notify
    NOTIFY = 4
    #: Dynamic Update
    UPDATE = 5

    # Unassigned, but used by Designate for command/control in the agents
    UNASSIGNED14 = 14

    @classmethod
    def _maximum(cls):
        return 15

    @classmethod
    def _unknown_exception_class(cls):
        return dns.opcode.UnknownOpcode

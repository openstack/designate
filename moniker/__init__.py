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
import os
import socket
from moniker.openstack.common import cfg

cfg.CONF.register_opts([
    cfg.StrOpt('pybasedir',
               default=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    '../')),
               help='Directory where the nova python module is installed'),
    cfg.StrOpt('host', default=socket.gethostname(),
               help='Name of this node'),
    cfg.StrOpt('control-exchange', default='moniker',
               help='AMQP exchange to connect to if using RabbitMQ or Qpid'),
    cfg.StrOpt('central-topic', default='central', help='Central Topic'),
    cfg.StrOpt('agent-topic', default='agent', help='Agent Topic'),
    cfg.StrOpt('state-path', default='$pybasedir', help='State Path'),
    cfg.StrOpt('templates-path', default='$pybasedir/templates',
               help='Templates Path'),
])

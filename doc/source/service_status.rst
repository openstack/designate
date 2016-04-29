..
    Copyright 2016 Hewlett Packard Enterprise Development Company LP
    All Rights Reserved.

       Licensed under the Apache License, Version 2.0 (the "License"); you may
       not use this file except in compliance with the License. You may obtain
       a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing, software
       distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
       WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
       License for the specific language governing permissions and limitations
       under the License.


Service Statuses
================

Overview
--------

The Service Status entries are used to track the health state of the services
in the Designate system. Each service will report in it's health via RPC or
using HTTP.

Explanation
-----------

============  ==============================================================
Attribute     Description
============  ==============================================================
service_name  The name of the service, typically `central` or alike.
hostname      The hostname where the service is running.
capabilities  Service capabilities, used to tell a service of the same type
              apart.
stats         Statistics are optional per service metrics.
status        An enum describing the status of the service.
              UP for health and ok, DOWN for down (Ie the service hasn't
              reported in for a while) and WARNING if the service is having
              issues.
============  ==============================================================

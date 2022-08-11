..
    Copyright 2022 Red Hat

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


==================
Designate Glossary
==================

The following is a glossary of terms that may be used througout the Designate
documentation and code.

.. glossary:: :sorted:

   Fully Qualified Domain Name
       A domain name that includes all levels of the domain hierarchy,
       including the root domain (represented by a period at the end). Fully
       Qualified Domain Name is sometimes abreviated as FQDN.
       Example: ``www.example.com.``

   Record
       The data (also known as the RDATA in RFC1034) part of a recordset.
       Recordsets may have one or more records. An example of a record for a
       recordset of type **A** would be an IP address, such as 192.0.2.1.

   Recordset
       A recordset represents one or more DNS :term:`records<Record>` that
       share the same `Name` and `Type`. For example, a recordset `named`
       ``www.example.com.``, with a `Type` of **A**, may contain two records;
       192.0.2.1 and 192.0.2.2.

   Zone
       A zone represents a namespace in DNS, for example the zone
       ``example.com.`` may contain a :term:`recordset<Recordset>` for ``www``.

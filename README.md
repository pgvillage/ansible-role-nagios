Nagios
=========

Nagios is a tool to monitor endpoints, such as PostgreSQL systems.
This role installs postgres-nrpe and additionally adds configuration to configure endpoint monitoring.
And it can enable endpoint monitoring on a cental Nagios monitoring system.
This role is part of PgVillage, which is an opinated PostgreSQL deployment for Virtual Machines.

Requirements
------------

This role aims at using an RPM from the MannemSolutions repo.

Role Variables
--------------

Please see [defaults](https://github.com/pgvillage/ansible-role-nagios/blob/main/defaults/main.yml) for all variables


Dependencies
------------

No dependencies


Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - pgvillage.nagios

License
-------

PostgreSQL

Author Information
------------------

PgVillage is an Open Community.
Main contributor is Nibble-IT.

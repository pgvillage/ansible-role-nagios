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

Please see the [API documentation](docs/api.md) for a description of all variables.
Defaults are defined in [defaults/main.yml](defaults/main.yml).


Multiple PostgreSQL instances
----------------------------

The role discovers `stolon_clusters` when `stolon_multicluster` is enabled.
It creates nrpe in each cluster through `<cluster>-master`, and generates local
database and Stolon service checks with cluster-specific names and ports.
Central Nagios definitions use the same command names.

You can also supply `nagios_clusters` explicitly or configure a single-instance
connection with `nagios_pg_service`, `nagios_pg_host` and `nagios_pg_port`.
See [PostgreSQL instances](docs/api.md#postgresql-instances) for examples and
authentication requirements.

Validation
----------

Run `python3 -m unittest discover -s tests -v`. The tests require Ansible and
PyYAML. They render configuration and exercise the multi-database wrapper using
temporary files and mock commands; they do not connect to PostgreSQL or change
services.

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

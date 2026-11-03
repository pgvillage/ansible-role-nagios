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

Define monitoring targets in `nagios_clusters` using inventory variables.
Each target accepts a primary service, check host, PostgreSQL port and SSL mode;
the role's defaults apply to omitted options. Cluster configuration is independent
of other roles.

The role creates nrpe in each configured cluster and generates local database
checks with cluster-specific names and ports. Systemd service checks can opt into
per-cluster instances with `per_cluster: true`. Central Nagios definitions use
the same command names.

The default `nagios_clusters: {}` uses a single-instance connection configured
with `nagios_pg_service`, `nagios_pg_host` and `nagios_pg_port`.
See [PostgreSQL instances](docs/api.md#postgresql-instances) for examples and
authentication requirements.

Validation
----------

Install the Molecule dependencies and run the default scenario:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r molecule/requirements.txt
molecule test
```

The scenario uses a local Ansible connection and Molecule's Ansible verifier. It covers
single-instance defaults, explicit clusters, connection overrides, service checks,
invalid ports, matching central Nagios definitions, and the multi-database wrapper.
It uses temporary files and mock database commands; it does not install packages,
connect to PostgreSQL or change services. Container software and sudo are not required.
This checks configuration and wrapper behavior rather than a full system deployment.

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

# pgvillage.nagios — API

This document describes all variables that can be set for the `pgvillage.nagios` role.
Defaults are defined in [defaults/main.yml](../defaults/main.yml).

The role:

- installs nrpe and check_postgres on hosts in the `postgres` group;
- creates a PostgreSQL superuser for nrpe;
- deploys custom nrpe scripts and nrpe command configuration for all checks in `nagios_checks`;
- installs SELinux modules on RedHat family systems with SELinux enabled;
- optionally registers the host and its services on one or more central Nagios servers.

## Custom filters

Many thresholds are derived using filters shipped in [filter_plugins/core.py](../filter_plugins/core.py):

| Filter | Description |
| --- | --- |
| `percent(f=100, minimum=0, digits=0)` | Returns `f` percent of the input, with a lower bound of `minimum`, rounded to `digits` digits. |
| `human(digits=0)` | Converts a number of bytes into a human readable value (e.g. `1G`). |
| `unhuman` | Converts a human readable value (e.g. `1k`) back into a number. |

## General

| Variable | Default | Description |
| --- | --- | --- |
| `nagios_enabled` | `true` | Enable or disable this role. When `false`, no tasks are run (e.g. on platforms where nrpe is unavailable). |
| `nagios_package_state` | `present` | State of the packages in `nagios_packages` (e.g. `present` or `latest`). |
| `nagios_packages` | `[nrpe, check_postgres]` | Packages to install on the PostgreSQL servers. |
| `nagios_scripts_folder` | `/opt/nagios/nrpe` | Folder where the custom nrpe scripts and the `check_postgres.pl` symlinks are deployed. |
| `nagios_config_folder` | `/etc/nrpe.d/` | Folder where the nrpe command configuration files are written. |
| `nagios_nrpe_user` | `nrpe` | PostgreSQL user (created as SUPERUSER) used by nrpe to connect, and owner of the nrpe config files. |
| `nagios_nrpe_group` | `{{ nagios_nrpe_user }}` | Group owner of the nrpe config files. |
| `nagios_selinux_modules` | `[my-nrpe, my-check-postgres]` | SELinux modules (`files/<name>.te`) to compile and install on RedHat family systems with SELinux enabled. |

## Running PostgreSQL processes (check_procs)

| Variable | Default | Description |
| --- | --- | --- |
| `nagios_running_postgresql_user` | `postgres` | OS user running the PostgreSQL processes. |
| `nagios_running_postgresql_search` | `postgres` | Argument string to search for in the process list. |
| `nagios_running_postgresql_warning` | `7:{{ nagios_connections_value }}` | Warning range for the number of running PostgreSQL processes. |
| `nagios_running_postgresql_critical` | `1:{{ nagios_connections_value + 100 }}` | Critical range for the number of running PostgreSQL processes. |

## Locks and connections

| Variable | Default | Description |
| --- | --- | --- |
| `nagios_locks_value` | `800` | Expected maximum number of locks; warning and critical are derived as a percentage of this value. |
| `nagios_locks_warning` | 50% of `nagios_locks_value` | Warning threshold for the number of locks. |
| `nagios_locks_critical` | 75% of `nagios_locks_value` | Critical threshold for the number of locks. |
| `nagios_connections_value` | `100` | Maximum number of connections (should match `max_connections`); used for several derived thresholds. |
| `nagios_connections_warning` | 70% of `nagios_connections_value` | Warning threshold for the number of connections. |
| `nagios_connections_critical` | 80% of `nagios_connections_value` | Critical threshold for the number of connections. |
| `nagios_backends_value` | `100` | Maximum number of backends (should match `max_connections`). |
| `nagios_backends_alert_percent` | `95` | Percentage of `nagios_backends_value` at which the backends check goes critical. |
| `nagios_backends_warning` | `2 * alert percent - 100`% of `nagios_backends_value` | Warning threshold for backends. |
| `nagios_backends_critical` | alert percent of `nagios_backends_value` | Critical threshold for backends. |
| `nagios_prepared_txns` | `{{ nagios_connections_value }}` | Warning threshold for the number of prepared transactions; critical is twice this. |

## Version

| Variable | Default | Description |
| --- | --- | --- |
| `nagios_pg_version` | `17` | Expected PostgreSQL major version (`check_postgres_version`). |

## WAL

The role runs `df` on `nagios_data_dir_mp` and `nagios_wal_dir_mp` to determine the available space.
WAL thresholds are derived from the number of 16MB WAL files that fit on the WAL mount point.

| Variable | Default | Description |
| --- | --- | --- |
| `nagios_wal_dir_mp` | `/` | Mount point of the WAL directory. |
| `nagios_mp_sizes` | derived | Internal: dict of mount point => available bytes, built from the registered `df` output. Normally there is no need to change this. |
| `nagios_wal_dir_mp_size` | derived | Available space (bytes) on the WAL mount point. |
| `nagios_max_wal_size_warning_percent` | `65` | Percentage of the WAL mount point that may be filled with WAL files before warning. |
| `nagios_max_wal_size_critical_percent` | `75` | Percentage of the WAL mount point that may be filled with WAL files before critical. |
| `nagios_wal_files_value` | derived | Number of 16MB WAL files that fit on the WAL mount point. |
| `nagios_wal_files_warning` | derived (minimum 10) | Warning threshold for the number of WAL files. |
| `nagios_wal_files_critical` | derived (minimum 100) | Critical threshold for the number of WAL files. |
| `nagios_archive_ready` | `15` | Warning threshold for the number of WAL files ready to be archived; critical is twice this. |

## Sizes

All size thresholds default to a percentage of the available space on the data mount point and are rendered with the `human` filter.

| Variable | Default | Description |
| --- | --- | --- |
| `nagios_data_dir_mp` | `/` | Mount point of the data directory. |
| `nagios_data_dir_mp_size` | derived | Available space (bytes) on the data mount point. |
| `nagios_db_size_value` | `{{ nagios_data_dir_mp_size }}` | Reference size (bytes) for the database size check. |
| `nagios_db_size_warning` | 80% of `nagios_db_size_value` | Warning threshold for database size. |
| `nagios_db_size_critical` | 90% of `nagios_db_size_value` | Critical threshold for database size. |
| `nagios_relation_size_value` | `{{ nagios_data_dir_mp_size }}` | Reference size (bytes) for the relation size check. |
| `nagios_relation_size_warning` | 70% of `nagios_relation_size_value` | Warning threshold for relation size. |
| `nagios_relation_size_critical` | 80% of `nagios_relation_size_value` | Critical threshold for relation size. |
| `nagios_table_size_value` | `{{ nagios_data_dir_mp_size }}` | Reference size (bytes) for the table size check. |
| `nagios_table_size_warning` | 70% of `nagios_table_size_value` | Warning threshold for table size. |
| `nagios_table_size_critical` | 80% of `nagios_table_size_value` | Critical threshold for table size. |
| `nagios_idx_size_value` | `{{ nagios_data_dir_mp_size }}` | Reference size (bytes) for the index size check. |
| `nagios_idx_size_warning` | 20% of `nagios_idx_size_value` | Warning threshold for index size. |
| `nagios_idx_size_critical` | 25% of `nagios_idx_size_value` | Critical threshold for index size. |
| `nagios_disk_space_warning` | `80%` | Warning threshold for disk space usage. |
| `nagios_disk_space_critical` | `90%` | Critical threshold for disk space usage. |

## Maintenance and health

| Variable | Default | Description |
| --- | --- | --- |
| `nagios_txn_time` | `1` | Critical threshold (seconds) for the longest running transaction; warning is half of this. |
| `nagios_autovac_freeze` | `98` | Critical percentage towards `autovacuum_freeze_max_age`; warning is `2 * value - 100`. |
| `nagios_bloat_warning` | `125% and 1G` | Warning when table size is more than 125% of the expected table size (data is 80% or less of relation size), only for relations larger than 1G. |
| `nagios_bloat_critical` | `150% and 5G` | Critical when table size is more than 150% of the expected table size (data is 66% or less of relation size), only for relations larger than 5G. |
| `nagios_commitratio` | `15` | Critical threshold (percent) for the commit ratio; warning is twice this. |
| `nagios_disabled_triggers` | `1` | Warning threshold for the number of disabled triggers; critical is twice this. |
| `nagios_hitratio` | `0` | Threshold (percent) for the buffer cache hit ratio; `0` effectively disables this check. |
| `nagios_sequence_space` | `90` | Critical percentage of used sequence space; warning is `2 * value - 100`. |
| `nagios_timesync` | `5` | Critical threshold (seconds) for clock difference between server and database; warning is half of this. |
| `nagios_txn_wraparound` | `200000000` | Base value for transaction id wraparound thresholds. |
| `nagios_txn_wraparound_warning` | 120% of `nagios_txn_wraparound` | Warning threshold for transaction id wraparound. |
| `nagios_txn_wraparound_criticial` | 150% of `nagios_txn_wraparound` | Critical threshold for transaction id wraparound. |

## Checks

### `nagios_checks`

A dict of all checks to configure in nrpe, grouped per check type.
Every group key maps to a template (`templates/<group>.j2`) which is rendered to `<nagios_config_folder>/<group>.cfg`.
All checks are also registered as services on the central Nagios servers (see `nagios_servers`).

| Group | Implementation | Keys per check |
| --- | --- | --- |
| `multi_check` | `pg_multi_db_checks.sh`, run against all databases | `warning`, `critical` |
| `check_postgres` | `check_postgres.pl` action, called through a symlink named after the check | `warning`, `critical` |
| `service_check` | `check_service_wrapper.sh`, checks a systemd service | `service` |
| `proces_check` | `check_procs` | `user`, `search`, `warning`, `critical` |

Default checks:

| Group | Check | Thresholds |
| --- | --- | --- |
| `multi_check` | `check_postgres_last_analyze` | 5 days / 5 days |
| `multi_check` | `check_postgres_last_vacuum` | 5 days / 7 days |
| `multi_check` | `check_postgres_locks` | `nagios_locks_*` |
| `multi_check` | `check_postgres_connection` | `nagios_connections_*` |
| `check_postgres` | `check_postgres_wal_files` | `nagios_wal_files_*` |
| `check_postgres` | `check_postgres_txn_time` | `nagios_txn_time` |
| `check_postgres` | `check_postgres_database_size` | `nagios_db_size_*` |
| `check_postgres` | `check_postgres_indexes_size` | `nagios_idx_size_*` |
| `check_postgres` | `check_postgres_version` | `nagios_pg_version` |
| `check_postgres` | `check_postgres_relation_size` | `nagios_relation_size_*` |
| `check_postgres` | `check_postgres_table_size` | `nagios_table_size_*` |
| `check_postgres` | `check_postgres_archive_ready` | `nagios_archive_ready` |
| `check_postgres` | `check_postgres_autovac_freeze` | `nagios_autovac_freeze` |
| `check_postgres` | `check_postgres_backends` | `nagios_backends_*` |
| `check_postgres` | `check_postgres_bloat` | `nagios_bloat_*` |
| `check_postgres` | `check_postgres_commitratio` | `nagios_commitratio` |
| `check_postgres` | `check_postgres_disabled_triggers` | `nagios_disabled_triggers` |
| `check_postgres` | `check_postgres_hitratio` | `nagios_hitratio` |
| `check_postgres` | `check_postgres_prepared_txns` | `nagios_prepared_txns` |
| `check_postgres` | `check_postgres_sequence` | `nagios_sequence_space` |
| `check_postgres` | `check_postgres_timesync` | `nagios_timesync` |
| `check_postgres` | `check_postgres_txn_wraparound` | `nagios_txn_wraparound_*` |
| `check_postgres` | `check_postgres_disk_space` | `nagios_disk_space_*` |
| `service_check` | `service_stolon_keeper` | service `stolon-keeper` |
| `service_check` | `service_stolon_proxy` | service `stolon-proxy` |
| `service_check` | `service_stolon_sentinel` | service `stolon-sentinel` |
| `service_check` | `service_crond` | service `crond` |
| `proces_check` | `running_postgresql` | `nagios_running_postgresql_*` |

Overriding `nagios_checks` replaces the whole dict, so copy the default and adapt it when you want to add or remove checks.

### `nagios_check_postgres_links`

Default: all keys of `nagios_checks.multi_check` and `nagios_checks.check_postgres`.

Names of the symlinks to `/usr/bin/check_postgres.pl` created in `nagios_scripts_folder`.

## Central Nagios servers

### `nagios_servers`

Default: `[]`

List of central Nagios servers on which host and service definitions for this host are created (tasks are delegated to `hostname`).

| Key | Description |
| --- | --- |
| `hostname` | Server to delegate to. |
| `path` | Folder in which `<inventory_hostname>.cfg` and `<inventory_hostname>-custom.cfg` are written. |
| `enabled` | When `true` the config is created; when `false` the custom config is removed. |
| `hostgroups` | List of hostgroups this host is added to. |

Example:

```yaml
nagios_servers:
  - hostname: nagios1.example.com
    path: /opt/nagios/etc/host.cfg.d
    enabled: true
    hostgroups:
      - serverhosting
      - postgres_dba
```

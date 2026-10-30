import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

import yaml


ROLE = Path(__file__).resolve().parents[1]


class MulticlusterTests(unittest.TestCase):
    def render(self, variables, expect_failure=False):
        with tempfile.TemporaryDirectory(prefix="nagios-role-test-") as work:
            work = Path(work)
            role = work / "roles" / "nagios_under_test"
            shutil.copytree(ROLE, role, ignore=shutil.ignore_patterns(".git", "__pycache__", "tests"))
            tasks = yaml.safe_load((ROLE / "tasks/postgres.yml").read_text())
            user_task = next(t for t in tasks if "community.postgresql.postgresql_user" in t)
            validation = yaml.safe_load((ROLE / "tests/render.yml").read_text())
            validation.insert(0, tasks[0])
            (role / "tasks/validate.yml").write_text(yaml.safe_dump(validation, sort_keys=False))
            output = work / "rendered.json"
            play = [{
                "hosts": "localhost", "gather_facts": False, "become": False,
                "vars": {
                    "nagios_mp_sizes": {"/": 107374182400},
                    "nagios_test_user_task": user_task, "nagios_test_output": str(output),
                    **variables,
                },
                "tasks": [{"ansible.builtin.include_role": {
                    "name": "nagios_under_test", "tasks_from": "validate",
                }}],
            }]
            playbook = work / "validate.yml"
            playbook.write_text(yaml.safe_dump(play, sort_keys=False))
            env = {
                **os.environ, "ANSIBLE_LOCAL_TEMP": str(work / "ansible-tmp"),
                "ANSIBLE_REMOTE_TEMP": str(work / "ansible-remote-tmp"),
                "ANSIBLE_ROLES_PATH": str(work / "roles"), "ANSIBLE_NOCOLOR": "1",
            }
            env.pop("ANSIBLE_CONFIG", None)
            result = subprocess.run(
                ["ansible-playbook", "-i", "localhost,", "-c", "local", str(playbook)],
                cwd=work, env=env, capture_output=True, text=True, timeout=60,
            )
            if expect_failure:
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("Nagios cluster targets need valid names", result.stdout)
                self.assertFalse(output.exists())
                return
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            rendered = json.loads(output.read_text())
            config = "\n".join(rendered["configs"].values())
            nrpe = re.findall(r"^command\[([^]]+)\]", config, re.MULTILINE)
            central = re.findall(r"check_nrpe_ssl!(\S+)", rendered["central"])
            self.assertEqual(len(nrpe), len(set(nrpe)), "Duplicate NRPE command")
            self.assertEqual(sorted(nrpe), sorted(central))
            return rendered

    def test_legacy_single_instance(self):
        result = self.render({})
        self.assertEqual(result["users"], [{
            "cluster": "", "service": "master", "port": 5432,
            "ssl_mode": "prefer", "name": "nrpe", "run_once": True,
        }])
        self.assertIn("command[check_postgres_version]", result["configs"]["check_postgres"])
        self.assertIn(" -H /tmp -p 5432 ", result["configs"]["check_postgres"])
        self.assertIn("-s stolon-keeper\n", result["configs"]["service_check"])

    def test_configurable_single_instance_connection(self):
        result = self.render({
            "nagios_pg_service": "pgv-testcluster-1-master", "nagios_pg_host": "/run/pgsql",
            "nagios_pg_port": 5544, "nagios_pg_ssl_mode": "verify-full",
        })
        self.assertEqual(result["users"][0]["service"], "pgv-testcluster-1-master")
        self.assertEqual(result["users"][0]["port"], 5544)
        self.assertEqual(result["users"][0]["ssl_mode"], "verify-full")
        self.assertIn(" -H /run/pgsql -p 5544 ", result["configs"]["check_postgres"])
        self.assertIn("PGHOST=/run/pgsql PGPORT=5544", result["configs"]["multi_check"])

    def test_stolon_clusters_use_distinct_primary_services_and_ports(self):
        result = self.render({
            "stolon_multicluster": True,
            "stolon_clusters": {
                "app-one": {"sysconfig": {"stkeeper": {"pg_port": 5433}}},
                "reporting_2": {"sysconfig": {"stkeeper": {"pg_port": 5544}}},
            },
        })
        self.assertEqual(
            [(u["service"], u["port"], u["ssl_mode"]) for u in result["users"]],
            [("app-one-master", 5433, "verify-full"), ("reporting_2-master", 5544, "verify-full")],
        )
        for cluster, port in [("app-one", 5433), ("reporting_2", 5544)]:
            line = next(
                line for line in result["configs"]["check_postgres"].splitlines()
                if line.startswith("command[check_postgres_version_" + cluster + "]")
            )
            self.assertIn("/check_postgres_version -H /tmp -p " + str(port), line)
            self.assertNotIn("/check_postgres_version_" + cluster, line)
            self.assertIn("PGPORT=" + str(port), result["configs"]["multi_check"])
            self.assertIn("pg_multi_db_checks.sh check_postgres_last_vacuum ", result["configs"]["multi_check"])
            for component in ["keeper", "proxy", "sentinel"]:
                self.assertIn("service_stolon_" + component + "_" + cluster, result["configs"]["service_check"])
                self.assertIn("-s stolon-" + component + "@" + cluster, result["configs"]["service_check"])
        self.assertEqual(result["configs"]["service_check"].count("command[service_crond]"), 1)
        self.assertEqual(result["configs"]["proces_check"].count("command[running_postgresql]"), 1)
        self.assertTrue(all(user["run_once"] for user in result["users"]))

    def test_explicit_targets_override_stolon_discovery(self):
        result = self.render({
            "stolon_multicluster": True,
            "stolon_clusters": {"ignored": {"sysconfig": {"stkeeper": {"pg_port": 5433}}}},
            "nagios_clusters": {
                "custom": {"service": "other-admin", "host": "/run/custom", "port": 5441, "ssl_mode": "require"},
            },
        })
        self.assertEqual(result["users"][0]["service"], "other-admin")
        self.assertEqual(result["users"][0]["port"], 5441)
        self.assertEqual(result["users"][0]["ssl_mode"], "require")
        self.assertIn(" -H /run/custom -p 5441 ", result["configs"]["check_postgres"])
        self.assertNotIn("ignored", result["central"])

    def test_empty_targets_restore_legacy_mode(self):
        result = self.render({
            "stolon_multicluster": True,
            "stolon_clusters": {"ignored": {"sysconfig": {"stkeeper": {"pg_port": 5433}}}},
            "nagios_clusters": {}, "nagios_pg_service": "fallback-master",
        })
        self.assertEqual(result["users"][0]["service"], "fallback-master")
        self.assertIn("command[check_postgres_version]", result["configs"]["check_postgres"])

    def test_named_target_defaults_to_its_master_service(self):
        result = self.render({"nagios_clusters": {"app": {"port": 5433}}})
        self.assertEqual(result["users"][0]["service"], "app-master")
        self.assertEqual(result["users"][0]["port"], 5433)

    def test_explicit_service_check_overrides_are_preserved(self):
        services = "stolon-keeper@app-one,stolon-keeper@reporting_2"
        result = self.render({
            "nagios_clusters": {"app-one": {"port": 5433}, "reporting_2": {"port": 5544}},
            "nagios_checks": {
                "multi_check": {"check_postgres_locks": {"warning": 10, "critical": 20}},
                "check_postgres": {},
                "service_check": {"service_stolon_keeper": {"service": services}},
                "proces_check": {},
            },
        })
        self.assertIn("command[service_stolon_keeper]", result["configs"]["service_check"])
        self.assertIn("-s " + services, result["configs"]["service_check"])
        self.assertEqual(result["configs"]["service_check"].count("command["), 1)

    def test_invalid_port_is_rejected_before_provisioning(self):
        self.render({"nagios_clusters": {"bad": {"port": 0}}}, expect_failure=True)

    def test_multi_database_wrapper_forwards_connection_to_every_check(self):
        with tempfile.TemporaryDirectory(prefix="nagios-wrapper-test-") as work:
            work = Path(work)
            scripts = work / "scripts with spaces"
            scripts.mkdir()
            wrapper = scripts / "pg_multi_db_checks.sh"
            shutil.copy2(ROLE / "files/nrpe/pg_multi_db_checks.sh", wrapper)
            trace = work / "trace.jsonl"
            psql = work / "psql"
            psql.write_text(
                "#!/usr/bin/env python3\nimport json, os\n"
                "with open(os.environ['NAGIOS_TEST_TRACE'], 'a') as f:\n"
                "    f.write(json.dumps({'command':'psql', 'port':os.environ['PGPORT'], "
                "'host':os.environ['PGHOST'], 'user':os.environ['PGUSER']}) + '\\n')\n"
                "print('postgres\\napp')\n"
            )
            check = scripts / "check_postgres_locks"
            check.write_text(
                "#!/usr/bin/env python3\nimport json, os, sys\n"
                "with open(os.environ['NAGIOS_TEST_TRACE'], 'a') as f:\n"
                "    f.write(json.dumps({'command':'check', 'args':sys.argv[1:]}) + '\\n')\n"
                "print('CHECK_POSTGRES_LOCKS OK: DB example')\n"
            )
            psql.chmod(0o755)
            check.chmod(0o755)
            result = subprocess.run(
                ["bash", str(wrapper), "check_postgres_locks", "-w", "10", "-c", "20"],
                env={
                    **os.environ, "PATH": str(work) + os.pathsep + os.environ["PATH"],
                    "PGPORT": "5544", "PGHOST": "/tmp/custom", "PGUSER": "monitor",
                    "NAGIOS_TEST_TRACE": str(trace),
                },
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            calls = [json.loads(line) for line in trace.read_text().splitlines()]
            self.assertEqual(calls[0], {
                "command": "psql", "port": "5544", "host": "/tmp/custom", "user": "monitor",
            })
            self.assertEqual(len(calls), 3)
            for call, database in zip(calls[1:], ["postgres", "app"]):
                self.assertEqual(call["args"], [
                    "-H", "/tmp/custom", "-p", "5544", "-u", "monitor",
                    "--db=" + database, "-w", "10", "-c", "20",
                ])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Isolated installer/doctor regressions; no real Claude or cloud tools are called."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
NODE = shutil.which("node")

FIXTURE = r'''
import json, os
from pathlib import Path
import sys
kind, *args = sys.argv[1:]
state_path = Path(os.environ["LAUNCHPAD_TEST_STATE"])
state = json.loads(state_path.read_text(encoding="utf-8"))
with Path(os.environ["LAUNCHPAD_TEST_LOG"]).open("a", encoding="utf-8") as log:
    log.write(json.dumps({"kind":kind,"args":args,"cwd":os.getcwd()})+"\n")
if kind != "claude":
    print(kind + " fixture version")
    sys.exit(0)
if args == ["--version"]:
    print("2.1.318 (fixture)")
elif args[:3] == ["plugin", "marketplace", "add"]:
    if args[-1] == os.environ.get("LAUNCHPAD_FAIL_MARKET"):
        print("Marketplace fixture failure", file=sys.stderr)
        sys.exit(1)
elif args[:2] == ["plugin", "install"]:
    plugin = args[-1]
    if plugin == os.environ.get("LAUNCHPAD_FAIL_PLUGIN"):
        print("Plugin fixture failure", file=sys.stderr)
        sys.exit(1)
    state["plugins"] = [p for p in state["plugins"] if p["id"] != plugin]
    state["plugins"].append({"id":plugin,"scope":"user","enabled":True})
elif args == ["plugin", "list", "--json"]:
    if os.environ.get("LAUNCHPAD_BROKEN_LIST"):
        print("NEVER_LEAK_TOKEN invalid JSON")
    else:
        print(json.dumps(state["plugins"]))
elif args[:2] == ["mcp", "get"]:
    server = state.get("pricing")
    if not server:
        # A project .mcp.json would hide a missing user entry in an unsafe cwd.
        for parent in (Path.cwd(), *Path.cwd().parents):
            if (parent/".mcp.json").exists():
                server = {"scope":"project","connected":True}
                break
    if not server:
        sys.exit(1)
    print("Scope: " + ("User config" if server.get("scope") == "user" else "Project config"))
    print("Status: " + ("✓ Connected" if server.get("connected") else "✗ Failed to connect"))
    print("Environment: NEVER_LEAK_TOKEN")
elif args[:2] == ["mcp", "add"]:
    if os.environ.get("LAUNCHPAD_FAIL_MCP"):
        print("MCP fixture failure", file=sys.stderr)
        sys.exit(1)
    if state.get("pricing"):
        print("Existing server must not be overwritten",file=sys.stderr)
        sys.exit(1)
    state["pricing"]={"scope":"user","connected":True,"command":args[6],"args":args[7:]}
else:
    print("Unexpected fixture call: "+repr(args),file=sys.stderr)
    sys.exit(2)
state_path.write_text(json.dumps(state), encoding="utf-8")
'''


@unittest.skipUnless(BASH and NODE, "Bash and Node.js are required to test setup")
class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="launchpad tests ")
        self.root = Path(self.temp.name)
        self.checkout = self.root / "checkout with spaces"
        (self.checkout / "scripts").mkdir(parents=True)
        for name in ("install.sh", "doctor.sh", "profiles.json", "scripts/setup-common.sh"):
            shutil.copy2(REPO / name, self.checkout / name)
        self.bin = self.root / "fixture bin"
        self.bin.mkdir()
        self.fixture = self.root / "fixture.py"
        self.fixture.write_text(FIXTURE, encoding="utf-8")
        self.state = self.root / "state.json"
        self.state.write_text(json.dumps({"plugins":[]}), encoding="utf-8")
        self.log = self.root / "calls.jsonl"
        self.config = self.root / "isolated claude profile"
        self.config.mkdir()
        self.env = os.environ.copy()
        for key in list(self.env):
            if key.startswith(("AWS_", "ANTHROPIC_", "OPENAI_", "SLACK_", "ATLASSIAN_")) or key in {"GH_TOKEN", "GITHUB_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDECODE"}:
                self.env.pop(key, None)
        self.env.update({
            "PATH": str(self.bin),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "CLAUDE_CONFIG_DIR": str(self.config),
            "LAUNCHPAD_TEST_PYTHON": Path(sys.executable).as_posix(),
            "LAUNCHPAD_TEST_NODE": Path(NODE).resolve().as_posix(),
            "LAUNCHPAD_TEST_FIXTURE": self.fixture.as_posix(),
            "LAUNCHPAD_TEST_STATE": str(self.state),
            "LAUNCHPAD_TEST_LOG": str(self.log),
        })
        for command in ("claude", "git", "npx"):
            self.wrapper(command, 'exec "$LAUNCHPAD_TEST_PYTHON" "$LAUNCHPAD_TEST_FIXTURE" ' + command + ' "$@"')
        self.wrapper("node", 'exec "$LAUNCHPAD_TEST_NODE" "$@"')
        # These two POSIX helpers are supplied by macOS and Git for Windows.
        for command in ("dirname", "rm"):
            executable = shutil.which(command)
            self.assertIsNotNone(executable, command + " is required")
            self.wrapper(command, 'exec "' + Path(executable).as_posix() + '" "$@"')
        self.profiles = json.loads((REPO / "profiles.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.temp.cleanup()

    def wrapper(self, name, body):
        path = self.bin / name
        path.write_bytes(("#!/bin/sh\n" + body + "\n").encode("utf-8"))
        path.chmod(0o755)

    def call(self, script="install", *args):
        return subprocess.run([BASH, (self.checkout / (script + ".sh")).as_posix(), *args],
                              env=self.env, cwd=self.checkout, text=True,
                              encoding="utf-8", errors="replace", capture_output=True, timeout=45)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()] if self.log.exists() else []

    def saved(self):
        return json.loads(self.state.read_text(encoding="utf-8"))

    def save(self, value):
        self.state.write_text(json.dumps(value), encoding="utf-8")

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_profiles_are_exact_and_user_scoped(self):
        for profile in ("aws", "collaboration", "full"):
            with self.subTest(profile=profile):
                self.save({"plugins": []})
                self.log.unlink(missing_ok=True)
                result = self.call("install", "--profile", profile)
                self.assert_success(result)
                self.assertIn("Done. Setup completed.", result.stdout)
                self.assertEqual({p["id"] for p in self.saved()["plugins"]}, set(self.profiles["profiles"][profile]))
                self.assertEqual("pricing" in self.saved(), profile != "collaboration")
                for call in self.calls():
                    if call["args"][:2] == ["plugin", "install"] or call["args"][:2] == ["mcp", "add"] or call["args"][:3] == ["plugin", "marketplace", "add"]:
                        index = call["args"].index("--scope")
                        self.assertEqual(call["args"][index+1], "user")
                self.assert_success(self.call("doctor", "--profile", profile))

    def test_default_profile_is_full(self):
        self.assert_success(self.call())
        self.assertEqual(len(self.saved()["plugins"]), 9)

    def test_help_and_bad_options_never_call_claude(self):
        for script in ("install", "doctor"):
            with self.subTest(script=script):
                self.assert_success(self.call(script, "--help"))
                for args in (("--unknown",), ("--profile",), ("--profile", "wrong")):
                    self.assertEqual(self.call(script, *args).returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_missing_prerequisites_stop_before_changes(self):
        for command in ("git", "node", "claude", "npx"):
            with self.subTest(command=command):
                path = self.bin / command
                old = path.read_text(encoding="utf-8")
                path.unlink()
                try:
                    result = self.call()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("NEEDS SETUP", result.stdout)
                    self.assertEqual(self.calls(), [])
                    self.assertEqual(self.saved(), {"plugins": []})
                finally:
                    path.write_bytes(old.encode("utf-8"))
                    path.chmod(0o755)

    def test_collaboration_does_not_require_npx(self):
        (self.bin / "npx").unlink()
        self.assert_success(self.call("install", "--profile", "collaboration"))
        self.assert_success(self.call("doctor", "--profile", "collaboration"))
        self.assertFalse(any(call["args"][:1] == ["mcp"] for call in self.calls()))

    def test_existing_pricing_and_unrelated_plugins_are_preserved(self):
        server = {"scope":"user", "connected":True, "command":"custom-command", "args":["--custom"], "env":{"TOKEN":"NEVER_LEAK_TOKEN"}}
        unrelated = {"id":"other@local", "scope":"user", "enabled":True}
        self.save({"plugins":[unrelated], "pricing":server})
        self.assert_success(self.call())
        self.assert_success(self.call())
        self.assertEqual(self.saved()["pricing"], server)
        self.assertIn(unrelated, self.saved()["plugins"])
        self.assertFalse(any(call["args"][:2] == ["mcp", "add"] for call in self.calls()))
        before = self.state.read_bytes()
        result = self.call("doctor")
        self.assert_success(result)
        self.assertNotIn("NEVER_LEAK_TOKEN", result.stdout + result.stderr)
        self.assertEqual(self.state.read_bytes(), before)

    def test_project_tmpdir_cannot_hide_missing_user_pricing(self):
        project_temp = self.checkout / "custom temp"
        project_temp.mkdir()
        (self.checkout / ".mcp.json").write_text('{"mcpServers":{"aws-pricing-calculator":{}}}', encoding="utf-8")
        (self.checkout / ".git").mkdir()
        self.env.update({"TMPDIR":str(project_temp), "TMP":str(project_temp), "TEMP":str(project_temp)})
        self.assert_success(self.call("install", "--profile", "aws"))
        self.assertEqual(self.saved()["pricing"]["scope"], "user")
        for call in self.calls():
            self.assertNotIn(str(self.checkout.resolve()).replace("\\", "/"), call["cwd"].replace("\\", "/"))
            self.assertFalse(Path(call["cwd"]).exists(), "Neutral temp directory should be cleaned")

    def test_marketplace_failure_returns_failure_and_skips_its_plugins(self):
        self.env["LAUNCHPAD_FAIL_MARKET"] = "anthropics/claude-plugins-official"
        result = self.call()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Finished with errors", result.stdout)
        self.assertEqual([p["id"] for p in self.saved()["plugins"]], ["design@knowledge-work-plugins"])

    def test_plugin_and_mcp_failures_return_failure(self):
        for variable, value in (("LAUNCHPAD_FAIL_PLUGIN", "aws-core@claude-plugins-official"), ("LAUNCHPAD_FAIL_MCP", "1")):
            with self.subTest(failure=variable):
                self.save({"plugins": []})
                self.env[variable] = value
                result = self.call()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Finished with errors", result.stdout)
                self.env.pop(variable)

    def test_doctor_rejects_missing_disabled_and_project_plugins(self):
        self.assert_success(self.call())
        initial = self.saved()
        for condition in ("missing", "disabled", "project", "errors"):
            with self.subTest(condition=condition):
                state = json.loads(json.dumps(initial))
                if condition == "missing":
                    state["plugins"].pop(0)
                elif condition == "disabled":
                    state["plugins"][0]["enabled"] = False
                elif condition == "project":
                    state["plugins"][0]["scope"] = "project"
                else:
                    state["plugins"][0]["errors"] = ["NEVER_LEAK_TOKEN"]
                self.save(state)
                before = self.state.read_bytes()
                result = self.call("doctor")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("NEEDS SETUP", result.stdout)
                self.assertNotIn("NEVER_LEAK_TOKEN", result.stdout + result.stderr)
                self.assertEqual(self.state.read_bytes(), before)

    def test_doctor_rejects_bad_json_without_echoing_it(self):
        self.env["LAUNCHPAD_BROKEN_LIST"] = "1"
        result = self.call("doctor")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cannot read", result.stdout)
        self.assertNotIn("NEVER_LEAK_TOKEN", result.stdout + result.stderr)

    def test_doctor_rejects_missing_disconnected_or_project_pricing(self):
        self.assert_success(self.call())
        initial = self.saved()
        for condition in ("missing", "disconnected", "project"):
            with self.subTest(condition=condition):
                state = json.loads(json.dumps(initial))
                if condition == "missing":
                    state.pop("pricing")
                elif condition == "disconnected":
                    state["pricing"]["connected"] = False
                else:
                    state["pricing"]["scope"] = "project"
                self.save(state)
                result = self.call("doctor")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("NEEDS SETUP Pricing", result.stdout)
                self.assertNotIn("NEVER_LEAK_TOKEN", result.stdout + result.stderr)

    def test_invalid_manifest_does_not_make_changes(self):
        (self.checkout / "profiles.json").write_text('{"broken":true}', encoding="utf-8")
        result = self.call()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.saved(), {"plugins": []})


if __name__ == "__main__":
    unittest.main(verbosity=2)

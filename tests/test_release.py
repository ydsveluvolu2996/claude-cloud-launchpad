#!/usr/bin/env python3
"""Offline release guards: no GitHub calls, uploads, or publishing."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("launchpad_release", ROOT / "scripts/package_release.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)
COMMIT = "a" * 40


class WorkflowEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.names = {"Repository checks (macos-latest)", "Repository checks (windows-latest)", "ShellCheck and Ruff"}
        self.run = {
            "repository": {"full_name": "example/project"},
            "head_repository": {"full_name": "example/project"},
            "head_sha": COMMIT, "head_branch": "main", "path": ".github/workflows/checks.yml",
            "status": "completed", "conclusion": "success", "id": 123, "run_attempt": 1,
            "html_url": "https://github.com/example/project/actions/runs/123",
        }
        self.jobs = {"total_count": 3, "jobs": [{"name": name, "status": "completed", "conclusion": "success"} for name in sorted(self.names)]}

    def validate(self):
        return release.validate_run(self.run, "example/project", COMMIT, ".github/workflows/checks.yml", self.names, self.jobs)

    def test_successful_evidence(self):
        self.assertEqual(self.validate()["id"], 123)

    def test_wrong_commit_repository_branch_or_workflow(self):
        original = copy.deepcopy(self.run)
        changes = {
            "head_sha": "b" * 40, "head_branch": "feature", "path": ".github/workflows/other.yml",
            "repository": {"full_name": "elsewhere/project"}, "head_repository": {"full_name": "fork/project"},
            "status": "in_progress", "conclusion": "failure",
        }
        for key, value in changes.items():
            with self.subTest(field=key):
                self.run = {**copy.deepcopy(original), key: value}
                with self.assertRaises(RuntimeError):
                    self.validate()

    def test_missing_duplicate_wrong_or_failed_jobs(self):
        original = copy.deepcopy(self.jobs)
        for condition in ("missing", "duplicate", "wrong", "failed", "skipped", "running"):
            with self.subTest(condition=condition):
                self.jobs = copy.deepcopy(original)
                if condition == "missing":
                    self.jobs["jobs"].pop()
                elif condition == "duplicate":
                    self.jobs["jobs"][1] = self.jobs["jobs"][0]
                elif condition == "wrong":
                    self.jobs["jobs"][0]["name"] = "A different check"
                elif condition == "running":
                    self.jobs["jobs"][0]["status"] = "in_progress"
                else:
                    self.jobs["jobs"][0]["conclusion"] = condition
                with self.assertRaises(RuntimeError):
                    self.validate()


class CreatedReleaseTests(unittest.TestCase):
    def test_draft_lookup_retries_visibility_delay(self):
        with patch.object(release, "command", side_effect=[RuntimeError("Not visible yet"), '{"databaseId": 123}']), patch.object(release, "api", return_value={"id": 123, "tag_name": "v1.0.0"}) as api, patch.object(release.time, "sleep") as sleep:
            self.assertEqual(release.find_created_release("example/project", "v1.0.0")["id"], 123)
            api.assert_called_once_with("repos/example/project/releases/123")
            sleep.assert_called_once_with(2)

    def test_wrong_tag_is_never_accepted_and_retries_are_bounded(self):
        with patch.object(release, "command", return_value='{"databaseId": 123}') as command, patch.object(release, "api", return_value={"tag_name": "v2.0.0"}), patch.object(release.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "tag mismatch"):
                release.find_created_release("example/project", "v1.0.0")
            self.assertEqual(command.call_count, 3)


class VersionReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="launchpad report fixture ")
        self.path = Path(self.temp.name) / "report.json"
        self.manifest = json.loads((ROOT / "profiles.json").read_text(encoding="utf-8"))
        self.report = {
            "commit": COMMIT, "profile": "aws", "verified_at": "2026-11-04T13:00:00+00:00",
            "platform": {"system": "Darwin", "release": "26", "machine": "arm64"},
            "claude": "2.1.318", "node": "v26.13.0", "python": "3.12.10",
            "plugins": [{"id": plugin, "scope": "user", "version": "1.0.0"} for plugin in self.manifest["profiles"]["aws"]],
            "pricing": {"package": self.manifest["pricing"]["package"], "protocol": "2025-06-18", "tool_count": 10, "tools_called": False},
        }

    def tearDown(self):
        self.temp.cleanup()

    def validate(self, profile="aws"):
        self.path.write_text(json.dumps(self.report), encoding="utf-8")
        return release.validate_report(self.path, profile, "Darwin", COMMIT, self.manifest)

    def test_valid_report_excludes_unrecognized_fields(self):
        self.report["unrecognized_private_field"] = "not-published"
        self.report["plugins"][0]["installPath"] = "/private/local/path"
        result = self.validate()
        self.assertNotIn("not-published", json.dumps(result))
        self.assertNotIn("/private/local/path", json.dumps(result))

    def test_wrong_commit_profile_platform_or_package(self):
        original = copy.deepcopy(self.report)
        for condition in ("commit", "profile", "platform", "package", "tools_called", "tool_count", "plugin", "scope"):
            with self.subTest(condition=condition):
                self.report = copy.deepcopy(original)
                if condition == "commit": self.report["commit"] = "b" * 40
                elif condition == "profile": self.report["profile"] = "full"
                elif condition == "platform": self.report["platform"]["system"] = "Windows"
                elif condition == "package": self.report["pricing"]["package"] = "different@1.0.0"
                elif condition == "tools_called": self.report["pricing"]["tools_called"] = True
                elif condition == "tool_count": self.report["pricing"]["tool_count"] = 0
                elif condition == "plugin": self.report["plugins"].pop()
                else: self.report["plugins"][0]["scope"] = "project"
                with self.assertRaises(RuntimeError):
                    self.validate()

    def test_collaboration_requires_no_pricing(self):
        self.report["profile"] = "collaboration"
        self.report["plugins"] = [{"id": plugin, "scope": "user", "version": "1.0.0"} for plugin in self.manifest["profiles"]["collaboration"]]
        with self.assertRaises(RuntimeError):
            self.validate("collaboration")
        self.report["pricing"] = None
        self.assertIsNone(self.validate("collaboration")["pricing"])

    def test_missing_or_invalid_report(self):
        with self.assertRaises(RuntimeError):
            release.validate_report(self.path, "aws", "Darwin", COMMIT, self.manifest)
        self.path.write_text("not JSON", encoding="utf-8")
        with self.assertRaises(ValueError):
            release.validate_report(self.path, "aws", "Darwin", COMMIT, self.manifest)


@unittest.skipUnless(shutil.which("git"), "Git is required for archive fixtures")
class ArchiveAndAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="launchpad package fixture ")
        self.root = Path(self.temp.name)
        self.repo = self.root / "source repo"
        self.repo.mkdir()
        self.output = self.root / "assets"
        self.output.mkdir()
        self.download = self.root / "download"
        self.download.mkdir()
        self.environment = patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"})
        self.environment.start()
        self.repo_patch = patch.object(release, "REPO", self.repo)
        self.repo_patch.start()
        self.git("init", "-q")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "core.filemode", "false")
        (self.repo / "hello.txt").write_bytes("Hello, beginners!\n".encode("utf-8"))
        (self.repo / "run.sh").write_bytes(b"#!/bin/sh\nprintf 'fixture\\n'\n")
        (self.repo / "folder with spaces").mkdir()
        (self.repo / "folder with spaces/data.json").write_bytes(b'{"example":true}\n')
        self.git("add", ".")
        self.git("update-index", "--chmod=+x", "run.sh")
        self.git("-c", "user.name=Launchpad test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        self.commit = self.git("rev-parse", "HEAD").strip()
        self.assets = release.build_assets(self.output, "1.0.0", self.commit, {"fixture": True, "commit": self.commit})
        self.metadata = [{"name": path.name, "state": "uploaded", "size": path.stat().st_size,
                          "digest": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()} for path in self.assets]
        for path in self.assets:
            shutil.copyfile(path, self.download / path.name)

    def tearDown(self):
        self.repo_patch.stop()
        self.environment.stop()
        self.temp.cleanup()

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_archives_and_checksums_match_git(self):
        names = {path.name for path in self.assets}
        self.assertEqual(names, {"claude-cloud-launchpad-1.0.0.zip", "claude-cloud-launchpad-1.0.0.tar.gz", "tested-versions.json", "SHA256SUMS"})
        lines = (self.output / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 3)
        for line in lines:
            digest, name = line.split("  ")
            self.assertEqual(digest, hashlib.sha256((self.output / name).read_bytes()).hexdigest())
        release.verify_uploaded_assets(self.metadata, self.assets)
        release.verify_downloaded_assets(self.download, self.assets)

    def test_archive_byte_or_executable_changes_are_rejected(self):
        original = (self.output / "claude-cloud-launchpad-1.0.0.zip").read_bytes()
        zipped = self.output / "claude-cloud-launchpad-1.0.0.zip"
        tarred = self.output / "claude-cloud-launchpad-1.0.0.tar.gz"
        for condition in ("bytes", "executable", "missing"):
            with self.subTest(condition=condition):
                zipped.write_bytes(original)
                with zipfile.ZipFile(zipped) as archive:
                    entries = [(entry, archive.read(entry)) for entry in archive.infolist()]
                with zipfile.ZipFile(zipped, "w") as archive:
                    for entry, content in entries:
                        if entry.filename.endswith("/run.sh"):
                            if condition == "bytes": content += b"changed\n"
                            elif condition == "executable": entry.external_attr = 0
                            else: continue
                        archive.writestr(entry, content)
                with self.assertRaises(RuntimeError):
                    release.verify_archives(zipped, tarred, "claude-cloud-launchpad-1.0.0/", release.tracked_files(self.commit))

    def test_missing_wrong_size_state_or_digest_assets_are_rejected(self):
        for condition in ("missing", "size", "state", "digest"):
            with self.subTest(condition=condition):
                metadata = copy.deepcopy(self.metadata)
                if condition == "missing": metadata.pop()
                elif condition == "size": metadata[0]["size"] += 1
                elif condition == "state": metadata[0]["state"] = "starter"
                else: metadata[0]["digest"] = "sha256:" + "0" * 64
                with self.assertRaises(RuntimeError):
                    release.verify_uploaded_assets(metadata, self.assets)

    def test_missing_or_corrupt_download_is_rejected(self):
        first = self.download / self.assets[0].name
        first.unlink()
        with self.assertRaises(RuntimeError):
            release.verify_downloaded_assets(self.download, self.assets)
        first.write_bytes(b"corrupt")
        with self.assertRaises(RuntimeError):
            release.verify_downloaded_assets(self.download, self.assets)


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Build a release from an exact tested main commit; publish only with --publish.

Uses Git and the authenticated GitHub CLI. Artifacts and output stay outside the
checkout. No installers, model calls, or cloud tools are run by this script.
"""
import argparse
from datetime import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile

REPO = Path(__file__).resolve().parents[1]
RUNNERS = {"macos-latest": "Darwin", "windows-latest": "Windows"}
PROFILES = ("aws", "collaboration", "full")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def command(args, *, binary=False, timeout=180):
    result = subprocess.run(args, cwd=REPO, capture_output=True, timeout=timeout)
    require(result.returncode == 0, f"{args[0]} {args[1]} failed: {result.stderr.decode('utf-8', errors='replace')[-1800:]}")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def api(endpoint):
    return json.loads(command(["gh", "api", endpoint]))


def require_absent(endpoint):
    result = subprocess.run(["gh", "api", endpoint], cwd=REPO, capture_output=True, text=True, timeout=60)
    require(result.returncode != 0, "The release or tag already exists; refusing to replace it")
    require("HTTP 404" in result.stderr, "Could not confirm the release/tag is absent: " + result.stderr[-1000:])


def validate_run(data, repository, commit, workflow_path, expected_jobs, jobs):
    require(data.get("repository", {}).get("full_name") == repository, "Workflow run belongs to another repository")
    require(data.get("head_repository", {}).get("full_name") == repository, "Workflow run used a different source repository")
    require(data.get("head_sha") == commit, "Workflow run did not test this exact commit")
    require(data.get("head_branch") == "main", "Release evidence must come from main")
    require(data.get("path") == workflow_path, "Unexpected workflow used as release evidence")
    require(data.get("status") == "completed" and data.get("conclusion") == "success", "Required workflow has not passed")
    entries = jobs.get("jobs", [])
    require(jobs.get("total_count") == len(expected_jobs) == len(entries), "Required workflow job count does not match")
    require({job.get("name") for job in entries} == expected_jobs, "Required workflow job names do not match")
    require(all(job.get("status") == "completed" and job.get("conclusion") == "success" for job in entries), "A required workflow job did not pass")
    return {"id": data["id"], "attempt": data["run_attempt"], "url": data["html_url"]}


def validate_report(path, profile, system, commit, manifest):
    require(path.is_file() and path.stat().st_size < 512_000, "Missing or oversized version report: " + path.name)
    report = json.loads(path.read_text(encoding="utf-8"))
    require(report.get("commit") == commit, "Version report is for another commit")
    require(report.get("profile") == profile and report.get("platform", {}).get("system") == system, "Version report platform/profile does not match its artifact")
    for field in ("verified_at", "claude", "node", "python"):
        require(isinstance(report.get(field), str) and 0 < len(report[field]) < 1000, "Invalid version report field: " + field)
    require(datetime.fromisoformat(report["verified_at"]).tzinfo is not None, "Version report timestamp must include a timezone")
    plugins = report.get("plugins", [])
    expected = set(manifest["profiles"][profile])
    require(len(plugins) == len(expected) and {p.get("id") for p in plugins} == expected, "Version report plugin membership does not match the profile")
    for plugin in plugins:
        require(plugin.get("scope") == "user" and isinstance(plugin.get("version"), str) and plugin["version"], "Plugin version or scope is missing")
    pricing = report.get("pricing")
    if profile in manifest["pricing"]["profiles"]:
        require(isinstance(pricing, dict) and pricing.get("package") == manifest["pricing"]["package"], "Pricing package does not match the manifest")
        require(pricing.get("tools_called") is False and isinstance(pricing.get("tool_count"), int) and pricing["tool_count"] > 0, "Pricing protocol verification is missing")
        require(isinstance(pricing.get("protocol"), str) and pricing["protocol"], "Pricing protocol version is missing")
        pricing = {key: pricing[key] for key in ("package", "protocol", "tool_count", "tools_called")}
    else:
        require(pricing is None, "Collaboration profile unexpectedly has pricing")
    # Copy only known, sanitized report fields into the public release asset.
    platform = {key: report["platform"][key] for key in ("system", "release", "version", "machine", "macos_version", "windows_version") if key in report["platform"]}
    return {**{key: report[key] for key in ("commit", "profile", "verified_at", "claude", "node", "python")},
            "platform": platform, "plugins": [{key: p[key] for key in ("id", "version", "scope")} for p in plugins], "pricing": pricing}


def collect_reports(repository, run_id, commit, artifact_dir, manifest):
    data = api(f"repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100")
    artifacts = data.get("artifacts", [])
    expected = {f"installation-verification-{runner}-{profile}" for runner in RUNNERS for profile in PROFILES}
    require(data.get("total_count") == len(expected) == len(artifacts), "Expected exactly six installation artifacts")
    require({item.get("name") for item in artifacts} == expected, "Installation artifacts do not match the six native jobs")
    for item in artifacts:
        evidence = item.get("workflow_run", {})
        require(not item.get("expired") and evidence.get("id") == run_id and evidence.get("head_sha") == commit,
                "Installation artifact is expired or belongs to different test evidence")
        destination = artifact_dir / item["name"]
        command(["gh", "run", "download", str(run_id), "--repo", repository, "--name", item["name"], "--dir", str(destination)])
    results = []
    for runner, system in RUNNERS.items():
        for profile in PROFILES:
            folder = artifact_dir / f"installation-verification-{runner}-{profile}"
            results.append({"runner": runner, "profile": profile, **{
                stage: validate_report(folder / f"launchpad-versions-{stage}.json", profile, system, commit, manifest)
                for stage in ("fresh", "repeat")}})
    return results


def tracked_files(commit):
    files = {}
    listing = command(["git", "ls-tree", "-r", "-z", commit], binary=True)
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        metadata, raw_name = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        name = raw_name.decode("utf-8")
        require(kind == "blob" and mode in ("100644", "100755"), "Release contains an unsupported Git entry: " + name)
        require(not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts, "Unsafe archive path")
        files[name] = (int(mode, 8) & 0o777, command(["git", "cat-file", "blob", oid], binary=True))
    return files


def verify_archives(zip_path, tar_path, prefix, expected):
    with zipfile.ZipFile(zip_path) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        require(len(entries) == len(expected) and {entry.filename for entry in entries} == {prefix + name for name in expected}, "ZIP file list differs from Git")
        for entry in entries:
            mode, content = expected[entry.filename[len(prefix):]]
            require(archive.read(entry) == content and (entry.external_attr >> 16) & 0o111 == mode & 0o111, "ZIP content or executable permissions differ from Git")
    with tarfile.open(tar_path, "r:gz") as archive:
        entries = [entry for entry in archive.getmembers() if not entry.isdir()]
        require(len(entries) == len(expected) and {entry.name for entry in entries} == {prefix + name for name in expected}, "Tar file list differs from Git")
        for entry in entries:
            mode, content = expected[entry.name[len(prefix):]]
            require(entry.isfile() and archive.extractfile(entry).read() == content and entry.mode & 0o111 == mode & 0o111, "Tar content or executable permissions differ from Git")


def build_assets(output, version, commit, report):
    stem = "claude-cloud-launchpad-" + version
    prefix = stem + "/"
    zipped, tarred = output / (stem + ".zip"), output / (stem + ".tar.gz")
    command(["git", "archive", "--format=zip", "--prefix=" + prefix, "--output=" + str(zipped), commit])
    tar_bytes = command(["git", "archive", "--format=tar", "--prefix=" + prefix, commit], binary=True)
    tarred.write_bytes(gzip.compress(tar_bytes, mtime=0))
    verify_archives(zipped, tarred, prefix, tracked_files(commit))
    versions = output / "tested-versions.json"
    versions.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    assets = [zipped, tarred, versions]
    sums = output / "SHA256SUMS"
    sums.write_text("".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in assets), encoding="utf-8")
    return assets + [sums]


def release_notes(repository, tag, commit, installation, checks):
    base = f"https://github.com/{repository}/blob/{tag}"
    return f"""Claude Cloud Launchpad {tag} helps beginners set up Claude Code tools on macOS or Windows.

Start with the [illustrated installation guide]({base}/README.md). Choose AWS, Collaboration, or Full setup, then run `bash doctor.sh` with the same profile to check your installation.

This release adds installation choices, prerequisite checks, diagnostics, [worked examples]({base}/docs/examples.md), [selective removal and recovery]({base}/docs/removal.md), and community support files. Read the [changelog]({base}/CHANGELOG.md) for the full change list.

All three profiles passed fresh installation and repeat-installation tests on native Intel macOS and Windows Server 2025 with Git Bash. [Installation results]({installation['url']}) · [Repository checks]({checks['url']}). Tested commit: `{commit}`.

Download either source archive below, extract it, and follow README.md. `tested-versions.json` records the exact tools and plugins observed in all six native jobs. `SHA256SUMS` contains checksums for both archives and the version record.

Windows 11 desktop and WSL/diagram workflows have not been verified end to end. Service account sign-ins, model calls, and cloud operations are outside these installation tests. Plugins and Claude Code can update independently of this release. See [compatibility and tested versions]({base}/docs/tested-versions.md).
"""


def find_release(repository, tag):
    # The releases-by-tag endpoint is for published releases. Listing also finds drafts.
    pages = json.loads(command(["gh", "api", f"repos/{repository}/releases?per_page=100", "--paginate", "--slurp"]))
    matches = [release for page in pages for release in page if release.get("tag_name") == tag]
    require(len(matches) <= 1, "Multiple releases already use this tag")
    return matches[0] if matches else None


def find_created_release(repository, tag):
    """Resolve a just-created draft by pending tag, tolerating API visibility delay."""
    for attempt in range(3):
        try:
            metadata = json.loads(command(["gh", "release", "view", tag, "--repo", repository, "--json", "databaseId"]))
            release_id = metadata.get("databaseId")
            require(isinstance(release_id, int) and release_id > 0, "Invalid created release ID")
            result = api(f"repos/{repository}/releases/{release_id}")
            require(result.get("tag_name") == tag, "Created release tag mismatch")
            return result
        except (RuntimeError, ValueError, KeyError, TypeError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def verify_uploaded_assets(uploaded, assets):
    require(len(uploaded) == len(assets) and {item.get("name") for item in uploaded} == {path.name for path in assets}, "Uploaded release assets do not match")
    local = {path.name: path for path in assets}
    for item in uploaded:
        path = local[item["name"]]
        digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        require(item.get("state") == "uploaded" and item.get("size") == path.stat().st_size, "Release asset size/state mismatch")
        require(item.get("digest") in (None, digest), "GitHub release asset checksum mismatch")


def verify_downloaded_assets(directory, assets):
    local = {path.name: path for path in assets}
    require({path.name for path in directory.iterdir()} == set(local), "Downloaded release assets do not match")
    for name, path in local.items():
        require(hashlib.sha256((directory / name).read_bytes()).digest() == hashlib.sha256(path.read_bytes()).digest(), "Downloaded release asset checksum mismatch")


def publish(repository, tag, commit, assets, notes):
    require(find_release(repository, tag) is None, "The release already exists; refusing to replace it")
    require_absent(f"repos/{repository}/git/ref/tags/{tag}")
    command(["gh", "release", "create", tag, *[str(path) for path in assets], "--repo", repository,
             "--draft", "--target", commit, "--title", "Claude Cloud Launchpad " + tag, "--notes-file", str(notes)], timeout=600)
    release = find_created_release(repository, tag)
    require(release.get("draft") is True and release.get("target_commitish") == commit, "Unexpected draft release target")
    verify_uploaded_assets(release.get("assets", []), assets)
    with tempfile.TemporaryDirectory(prefix="launchpad-release-download-") as temp:
        command(["gh", "release", "download", tag, "--repo", repository, "--dir", temp])
        verify_downloaded_assets(Path(temp), assets)
    # Nothing becomes public until all uploaded bytes have been downloaded and checked.
    command(["gh", "release", "edit", tag, "--repo", repository, "--draft=false", "--latest"])
    published = api(f"repos/{repository}/releases/{release['id']}")
    ref = api(f"repos/{repository}/git/ref/tags/{tag}")
    require(not published.get("draft") and not published.get("prerelease") and ref.get("object", {}).get("sha") == commit, "Published release/tag verification failed")
    require(api(f"repos/{repository}/releases/latest").get("id") == published["id"], "Release was not marked latest")
    print("Published " + published["html_url"])
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write(f"Published [{tag}]({published['html_url']}) from `{commit}` after validating nine jobs, twelve version reports, archive contents, and uploaded asset checksums.\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--installation-run-id", required=True, type=int)
    parser.add_argument("--checks-run-id", required=True, type=int)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--publish", action="store_true", help="Create, verify, then publish a new release; otherwise only prepare files")
    args = parser.parse_args()
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository), "Invalid repository name")
    require(re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", args.tag), "Use a stable version tag such as v1.0.0")
    require(args.installation_run_id > 0 and args.checks_run_id > 0, "Workflow run IDs must be positive")
    version = (REPO / "VERSION").read_text(encoding="utf-8").strip()
    require(args.tag == "v" + version, "Tag does not match VERSION")
    require(not command(["git", "status", "--porcelain", "--untracked-files=all"]), "Release requires a clean checkout")
    commit = command(["git", "rev-parse", "HEAD"])
    if args.publish:
        require(os.environ.get("GITHUB_REF") == "refs/heads/main" and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch", "Publishing is allowed only by manual workflow dispatch on main")
        require(os.environ.get("GITHUB_SHA") == commit, "Checkout does not match the dispatched commit")
    require(api(f"repos/{args.repository}/git/ref/heads/main").get("object", {}).get("sha") == commit, "Checkout is not the current main commit")
    runs = []
    for run_id, path, names in (
        (args.installation_run_id, ".github/workflows/installation-smoke.yml", {f"Native installation ({runner}, {profile})" for runner in RUNNERS for profile in PROFILES}),
        (args.checks_run_id, ".github/workflows/checks.yml", {f"Repository checks ({runner})" for runner in RUNNERS} | {"ShellCheck and Ruff"}),
    ):
        data = api(f"repos/{args.repository}/actions/runs/{run_id}")
        jobs = api(f"repos/{args.repository}/actions/runs/{run_id}/jobs?filter=latest&per_page=100")
        runs.append(validate_run(data, args.repository, commit, path, names, jobs))
    for directory in (args.artifact_dir, args.output_dir):
        require(not directory.resolve().is_relative_to(REPO), "Release files must stay outside the checkout")
        directory.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((REPO / "profiles.json").read_text(encoding="utf-8"))
    results = collect_reports(args.repository, args.installation_run_id, commit, args.artifact_dir, manifest)
    report = {"schema_version": 1, "release": args.tag, "repository": args.repository, "commit": commit,
              "installation_run": runs[0], "checks_run": runs[1], "results": results}
    assets = build_assets(args.output_dir, version, commit, report)
    notes = args.output_dir / "release-notes.md"
    notes.write_text(release_notes(args.repository, args.tag, commit, *runs), encoding="utf-8")
    print("Prepared and verified: " + ", ".join(path.name for path in assets))
    if args.publish:
        publish(args.repository, args.tag, commit, assets, notes)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print("FAIL " + str(exc), file=sys.stderr)
        sys.exit(1)

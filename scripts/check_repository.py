#!/usr/bin/env python3
"""Check release files, manifest consistency, syntax, and local Markdown links."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
ERRORS = []


def check(condition, message):
    if not condition:
        ERRORS.append(message)


def source_files():
    return [
        path for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in {".git", "__pycache__", "node_modules", ".venv"} for part in path.relative_to(ROOT).parts)
    ]


def check_manifest():
    manifest = json.loads((ROOT / "profiles.json").read_text(encoding="utf-8"))
    profiles = manifest["profiles"]
    markets = manifest["marketplaces"]
    check(set(profiles) == {"aws", "collaboration", "full"}, "Expected aws, collaboration, and full profiles")
    for name, plugins in profiles.items():
        check(isinstance(plugins, list) and bool(plugins), f"Empty or invalid profile: {name}")
        check(len(set(plugins)) == len(plugins), f"Duplicate plugin in profile: {name}")
        for plugin in plugins:
            parts = plugin.split("@")
            check(len(parts) == 2 and parts[1] in markets, f"Unknown marketplace for {plugin}")
    check(set(profiles["full"]) == set(profiles["aws"]) | set(profiles["collaboration"]), "Full profile must contain the union of AWS and collaboration plugins")
    check(set(manifest["pricing"]["profiles"]) == {"aws", "full"}, "Pricing belongs only in AWS and full profiles")
    check(bool(re.fullmatch(r"[^\s@]+@\d+\.\d+\.\d+", manifest["pricing"]["package"])), "Pricing package must have an exact version")
    check(not (ROOT / ".claude/settings.json").exists(), "Project Claude settings would override the user's selected profile")
    check(not (ROOT / ".mcp.json").exists(), "Project MCP settings would override the user's selected profile")


def check_links(path):
    text = path.read_text(encoding="utf-8")
    # Commands and illustrative code can contain bracket/parenthesis pairs that
    # are not links. Check normal Markdown prose only, without network requests.
    text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1\s*$", "", text)
    links = re.finditer(r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[\"'][^\"']*[\"'])?\s*\)", text)
    for match in links:
        target = match.group(1) or match.group(2)
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        relative = unquote(parsed.path)
        destination = ROOT / relative.lstrip("/") if relative.startswith("/") else path.parent / relative
        check(destination.exists(), f"Broken local link in {path.relative_to(ROOT)}: {target}")


def main():
    required = [
        "README.md", "LICENSE", "CREDITS.md", "CONTRIBUTING.md", "SECURITY.md",
        "CODE_OF_CONDUCT.md", "CHANGELOG.md", "profiles.json", "install.sh", "doctor.sh",
        "docs/examples.md", "docs/removal.md", "docs/tested-versions.md",
    ]
    for name in required:
        check((ROOT / name).is_file(), f"Missing release file: {name}")
    try:
        check_manifest()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        ERRORS.append(f"Invalid profiles.json: {exc}")
    bash = shutil.which("bash")
    check(bash is not None, "Bash is required for shell syntax checks")
    for path in source_files():
        relative = path.relative_to(ROOT)
        try:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix == ".py":
                compile(path.read_text(encoding="utf-8"), str(relative), "exec")
            elif path.suffix == ".sh":
                check(b"\r\n" not in path.read_bytes(), f"Shell script contains Windows line endings: {relative}")
                if bash:
                    result = subprocess.run([bash, "-n", path.as_posix()], capture_output=True, text=True, timeout=15)
                    check(result.returncode == 0, f"Shell syntax error in {relative}: {result.stderr.strip()}")
            elif path.suffix == ".md":
                check_links(path)
        except (OSError, ValueError, SyntaxError, subprocess.TimeoutExpired) as exc:
            ERRORS.append(f"{relative}: {exc}")
    if ERRORS:
        for message in ERRORS:
            print("FAIL " + message, file=sys.stderr)
        return 1
    print("PASS release files, profile manifest, JSON/Python/Bash syntax, and local documentation links")
    return 0


if __name__ == "__main__":
    sys.exit(main())

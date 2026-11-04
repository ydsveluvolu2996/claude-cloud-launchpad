#!/usr/bin/env python3
"""Verify a real installation in CLAUDE_CONFIG_DIR without calling cloud tools."""

import argparse
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import platform
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time


REPO = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_initialization(result):
    """Probe the common initialize/tools-list subset, including newer date versions."""
    require(isinstance(result, dict), "Malformed MCP initialization result")
    version = result.get("protocolVersion")
    require(isinstance(version, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", version),
            "Missing or malformed MCP protocol version")
    try:
        negotiated = date.fromisoformat(version)
    except ValueError as exc:
        raise RuntimeError("Invalid MCP protocol version date") from exc
    require(negotiated >= date(2024, 11, 5), "MCP protocol predates the supported tools-list probe")
    capabilities = result.get("capabilities")
    require(isinstance(capabilities, dict) and isinstance(capabilities.get("tools"), dict),
            "Pricing server did not advertise tools")
    # Actual tools/list must still succeed below. This is a compatibility probe,
    # not a claim to implement every feature in a future protocol revision.
    return version


class WindowsProcessJob:
    """Own one suspended child and its descendants, including orphaned children."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        self.ctypes = ctypes
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "CreateToolhelp32Snapshot": ([wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE),
            "Thread32First": ([wintypes.HANDLE, ctypes.c_void_p], wintypes.BOOL),
            "Thread32Next": ([wintypes.HANDLE, ctypes.c_void_p], wintypes.BOOL),
            "OpenThread": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "ResumeThread": ([wintypes.HANDLE], wintypes.DWORD),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes = arguments
            function.restype = result

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
                ("max_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
                ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD),
            ]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("basic", BasicLimits), ("io_counters", ctypes.c_ulonglong * 6),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t),
            ]

        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def attach_and_resume(self, process):
        from ctypes import wintypes

        ctypes = self.ctypes
        # The process is still suspended: it cannot spawn children before assignment.
        handle = self.api.OpenProcess(0x0101, False, process.pid)  # SET_QUOTA | TERMINATE
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.api.AssignProcessToJobObject(self.handle, handle):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.api.CloseHandle(handle)

        class ThreadEntry(ctypes.Structure):
            _fields_ = [
                ("size", wintypes.DWORD), ("usage", wintypes.DWORD),
                ("thread_id", wintypes.DWORD), ("process_id", wintypes.DWORD),
                ("base_priority", wintypes.LONG), ("delta_priority", wintypes.LONG),
                ("flags", wintypes.DWORD),
            ]

        snapshot = self.api.CreateToolhelp32Snapshot(0x00000004, 0)  # TH32CS_SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = ThreadEntry()
            entry.size = ctypes.sizeof(entry)
            found = self.api.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.process_id == process.pid:
                    thread = self.api.OpenThread(0x0002, False, entry.thread_id)  # SUSPEND_RESUME
                    if not thread:
                        raise ctypes.WinError(ctypes.get_last_error())
                    try:
                        if self.api.ResumeThread(thread) == 0xFFFFFFFF:
                            raise ctypes.WinError(ctypes.get_last_error())
                    finally:
                        self.api.CloseHandle(thread)
                    return
                entry.size = ctypes.sizeof(entry)
                found = self.api.Thread32Next(snapshot, ctypes.byref(entry))
            raise RuntimeError("Could not find the test process's suspended initial thread")
        finally:
            self.api.CloseHandle(snapshot)

    def close(self):
        if self.handle:
            if not self.api.CloseHandle(self.handle):
                raise self.ctypes.WinError(self.ctypes.get_last_error())
            self.handle = None


def start_process(command, **options):
    job = WindowsProcessJob() if os.name == "nt" else None
    if job is not None:
        # CREATE_SUSPENDED closes the race between spawning a child and owning its tree.
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000004
    else:
        options["start_new_session"] = True
    try:
        process = subprocess.Popen(command, **options)
    except BaseException:
        if job is not None:
            job.close()
        raise
    process.verification_job = job
    process.verification_owns_tree = True
    try:
        if job is not None:
            job.attach_and_resume(process)
    except BaseException:
        try:
            process.kill()  # This handle belongs only to the suspended test child.
        finally:
            finish_process(process)
        raise
    return process


def finish_process(process, grace=0):
    """Bound cleanup to a tree created by start_process, never the caller's group."""
    require(getattr(process, "verification_owns_tree", False), "Refusing to clean up an unowned process tree")
    if grace:
        try:
            process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
    if process.verification_job is not None:
        # Closing the job also kills descendants after their original parent exits.
        # No taskkill subprocess is needed, so cleanup cannot hang waiting for it.
        process.verification_job.close()
    else:
        require(process.pid != os.getpgrp(), "Refusing to signal the caller's process group")
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                break
            if sig == signal.SIGTERM:
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
        # Always signal the group, even when its original parent has already exited.
    process.wait(timeout=5)


def run(command, cwd, timeout=180):
    process = start_process(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        require(process.returncode == 0, f"{command[0]} {command[1]} failed: {stderr[-2000:]}")
        return stdout
    finally:
        finish_process(process)
        process.stdout.close()
        process.stderr.close()


def verify_plugins(claude, neutral, expected):
    expected = set(expected)
    installed = json.loads(run([claude, "plugin", "list", "--json"], neutral))
    require(isinstance(installed, list), "Unexpected plugin list JSON format")
    actual = {entry.get("id") for entry in installed}
    require(actual == expected, f"Wrong plugin selection: missing {sorted(expected - actual)}; unexpected {sorted(actual - expected)}")
    require(len(installed) == len(expected), "Unexpected duplicate plugin installation")
    versions = []
    for plugin_id in sorted(expected):
        matches = [item for item in installed if item.get("id") == plugin_id and item.get("scope") == "user"]
        require(len(matches) == 1, f"Missing or duplicate user-scoped plugin: {plugin_id}")
        entry = matches[0]
        require(entry.get("enabled") is True, f"Plugin is disabled: {plugin_id}")
        require(not entry.get("errors"), f"Plugin has load errors: {plugin_id}")
        install_path = Path(entry["installPath"])
        # Skill-only plugins, such as session-report, need no plugin.json manifest.
        assets = [install_path / ".claude-plugin/plugin.json", install_path / ".mcp.json"]
        assets.extend(install_path.glob("skills/*/SKILL.md"))
        require(any(path.is_file() and path.stat().st_size for path in assets), f"Plugin files missing: {plugin_id}")
        print(f"PASS plugin {plugin_id} ({entry.get('version', 'unknown version')}, user scope)", flush=True)
        versions.append({"id": plugin_id, "version": entry.get("version"), "scope": "user"})
    return versions


def npx_launch_command(package):
    node = shutil.which("node")
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    require(node and npx, "Node.js and npx must be installed")
    # Launch npm's JS entry directly for a portable stdio test. The separate
    # `claude mcp get` check below exercises Claude's registered bare npx command.
    resolved = Path(npx).resolve()
    candidates = [
        resolved if resolved.name == "npx-cli.js" else None,
        Path(npx).parent / "node_modules/npm/bin/npx-cli.js",
        Path(node).parent / "node_modules/npm/bin/npx-cli.js",
        Path(node).parent.parent / "lib/node_modules/npm/bin/npx-cli.js",
    ]
    entry = next((path for path in candidates if path and path.is_file()), None)
    require(entry is not None, "Cannot locate npm's npx-cli.js")
    return [node, str(entry), "-y", package]


def check_pricing_protocol(neutral, package):
    process = start_process(
        npx_launch_command(package), cwd=neutral, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace", bufsize=1,
    )
    replies = queue.Queue()
    errors = []

    def read_stdout():
        for line in process.stdout:
            try:
                replies.put(json.loads(line))
            except json.JSONDecodeError:
                continue
        replies.put(None)

    def read_stderr():
        for line in process.stderr:
            errors.append(line)
            del errors[:-30]

    stdout_reader = threading.Thread(target=read_stdout, daemon=True)
    stderr_reader = threading.Thread(target=read_stderr, daemon=True)
    stdout_reader.start()
    stderr_reader.start()

    def send(message):
        process.stdin.write(json.dumps({"jsonrpc": "2.0", **message}) + "\n")
        process.stdin.flush()

    def receive(request_id):
        deadline = time.monotonic() + 120
        while True:
            remaining = deadline - time.monotonic()
            require(remaining > 0, "Pricing MCP response timed out")
            try:
                message = replies.get(timeout=remaining)
            except queue.Empty as exc:
                raise RuntimeError("Pricing MCP response timed out") from exc
            require(message is not None, "Pricing MCP exited: " + "".join(errors)[-2000:])
            if message.get("id") == request_id:
                require("error" not in message, f"Pricing MCP rejected request {request_id}")
                return message["result"]

    try:
        send({"id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "claude-cloud-launchpad-test", "version": "1.0.0"},
        }})
        initialized = receive(1)
        protocol = check_initialization(initialized)
        send({"method": "notifications/initialized"})
        send({"id": 2, "method": "tools/list", "params": {}})
        tools = receive(2).get("tools", [])
        require(len(tools) > 0 and all(tool.get("name") and tool.get("inputSchema") for tool in tools), "Pricing server returned no valid tools")
        print(f"PASS live pricing MCP initialize + tools/list ({len(tools)} tools; no tools called)", flush=True)
        return {"protocol": protocol, "tool_count": len(tools), "tools_called": False}
    finally:
        if process.stdin and not process.stdin.closed:
            try:
                process.stdin.close()
            except OSError:
                pass
        finish_process(process, grace=5)
        stdout_reader.join(timeout=5)
        stderr_reader.join(timeout=5)
        require(not stdout_reader.is_alive() and not stderr_reader.is_alive(), "Pricing MCP output readers did not stop")
        process.stdout.close()
        process.stderr.close()


def read_config(config):
    path = config / ".claude.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("aws", "collaboration", "full"), default="full")
    parser.add_argument("--report", type=Path, help="Save a sanitized JSON record of tested versions")
    args = parser.parse_args()
    manifest = json.loads((REPO / "profiles.json").read_text(encoding="utf-8"))
    pricing_spec = manifest["pricing"]
    server, package = pricing_spec["name"], pricing_spec["package"]
    needs_pricing = args.profile in pricing_spec["profiles"]
    config_value = os.environ.get("CLAUDE_CONFIG_DIR")
    require(config_value, "Set CLAUDE_CONFIG_DIR to an isolated test profile first")
    config = Path(config_value).resolve()
    require(config != (Path.home() / ".claude").resolve(), "Do not test against your personal Claude profile")
    claude = shutil.which("claude")
    require(claude, "Claude Code CLI is not installed")
    saved = read_config(config)
    pricing = saved.get("mcpServers", {}).get(server)
    if needs_pricing:
        require(pricing and pricing.get("command") == "npx" and pricing.get("args") == ["-y", package], "Missing or unexpected user-scoped pricing MCP configuration")
        print("PASS pricing MCP is saved in the isolated user profile", flush=True)
    else:
        require(pricing is None, "Collaboration-only setup unexpectedly added the pricing MCP")
        print("PASS collaboration-only setup did not add the pricing MCP", flush=True)
    before = pricing
    baseline_path = config / "launchpad-test-pricing-baseline.json"
    if baseline_path.exists():
        require(json.loads(baseline_path.read_text()) == pricing, "Pricing configuration changed since previous verification")
        print("PASS pricing configuration unchanged since previous verification", flush=True)
    else:
        baseline_path.write_text(json.dumps(pricing, sort_keys=True), encoding="utf-8")
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "commit": run([shutil.which("git"), "rev-parse", "HEAD"], REPO).strip(),
        "profile": args.profile,
        "platform": {"system": platform.system(), "release": platform.release(), "version": platform.version(), "machine": platform.machine()},
        "python": platform.python_version(),
    }
    if platform.system() == "Darwin":
        report["platform"]["macos_version"] = platform.mac_ver()[0]
    elif platform.system() == "Windows":
        report["platform"]["windows_version"] = list(platform.win32_ver())
    with tempfile.TemporaryDirectory(prefix="launchpad verify ") as neutral:
        report["claude"] = run([claude, "--version"], neutral).strip()
        report["node"] = run([shutil.which("node"), "--version"], neutral).strip()
        print("Claude Code " + report["claude"], flush=True)
        print("Node.js " + report["node"], flush=True)
        report["plugins"] = verify_plugins(claude, neutral, manifest["profiles"][args.profile])
        if needs_pricing:
            report["pricing"] = {"package": package, **check_pricing_protocol(neutral, package)}
            status = run([claude, "mcp", "get", server], neutral)
            status = re.sub(r"\x1b\[[0-9;]*m", "", status)
            require(re.search(r"Status:\s*(?:[✓✔]\s*)?Connected(?:\s|$)", status), "Claude could not connect using the registered npx command: " + status[-1500:])
            require("User config" in status, "Claude did not resolve the user-scoped MCP configuration")
            print("PASS Claude connects to the user-scoped pricing server from another folder", flush=True)
        else:
            report["pricing"] = None
    after = read_config(config).get("mcpServers", {}).get(server)
    require(before == after, "Verification modified the pricing server configuration")
    print("PASS verification finished without calling cloud tools or changing the MCP entry", flush=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL {exc}", file=sys.stderr, flush=True)
        sys.exit(1)

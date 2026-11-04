#!/usr/bin/env python3
"""Verify a real installation in CLAUDE_CONFIG_DIR without calling cloud tools."""

import json
import os
from pathlib import Path
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
SERVER = "aws-pricing-calculator"
PACKAGE = "sample-aws-pricing-calculator-mcp@1.3.4"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(command, cwd, timeout=180):
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout,
    )
    require(result.returncode == 0, f"{command[0]} {command[1]} failed: {result.stderr[-2000:]}")
    return result.stdout


def verify_plugins(claude, neutral):
    expected = set(json.loads((REPO / ".claude/settings.json").read_text())["enabledPlugins"])
    installed = json.loads(run([claude, "plugin", "list", "--json"], neutral))
    require(isinstance(installed, list), "Unexpected plugin list JSON format")
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


def npx_launch_command():
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
    return [node, str(entry), "-y", PACKAGE]


def check_pricing_protocol(neutral):
    options = {"start_new_session": True} if os.name != "nt" else {}
    process = subprocess.Popen(
        npx_launch_command(), cwd=neutral, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace", bufsize=1, **options,
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

    threading.Thread(target=read_stdout, daemon=True).start()
    threading.Thread(target=read_stderr, daemon=True).start()

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
        require(initialized.get("protocolVersion") in {"2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"}, "Unsupported MCP protocol version")
        require("tools" in initialized.get("capabilities", {}), "Pricing server did not advertise tools")
        send({"method": "notifications/initialized"})
        send({"id": 2, "method": "tools/list", "params": {}})
        tools = receive(2).get("tools", [])
        require(len(tools) > 0 and all(tool.get("name") and tool.get("inputSchema") for tool in tools), "Pricing server returned no valid tools")
        print(f"PASS live pricing MCP initialize + tools/list ({len(tools)} tools; no tools called)", flush=True)
    finally:
        if process.stdin and not process.stdin.closed:
            try:
                process.stdin.close()
            except OSError:
                pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            else:
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                process.wait(timeout=5)


def main():
    config_value = os.environ.get("CLAUDE_CONFIG_DIR")
    require(config_value, "Set CLAUDE_CONFIG_DIR to an isolated test profile first")
    config = Path(config_value).resolve()
    require(config != (Path.home() / ".claude").resolve(), "Do not test against your personal Claude profile")
    claude = shutil.which("claude")
    require(claude, "Claude Code CLI is not installed")
    saved = json.loads((config / ".claude.json").read_text())
    pricing = saved.get("mcpServers", {}).get(SERVER)
    require(pricing and pricing.get("command") == "npx" and pricing.get("args") == ["-y", PACKAGE], "Missing or unexpected user-scoped pricing MCP configuration")
    before = dict(pricing)
    baseline_path = config / "launchpad-test-pricing-baseline.json"
    if baseline_path.exists():
        require(json.loads(baseline_path.read_text()) == pricing, "Repeated installation changed the existing MCP entry")
        print("PASS repeated installation preserved the existing MCP entry", flush=True)
    else:
        baseline_path.write_text(json.dumps(pricing, sort_keys=True), encoding="utf-8")
    print("PASS pricing MCP is saved in the isolated user profile", flush=True)
    with tempfile.TemporaryDirectory(prefix="launchpad-verify-") as neutral:
        print("Claude Code " + run([claude, "--version"], neutral).strip(), flush=True)
        print("Node.js " + run([shutil.which("node"), "--version"], neutral).strip(), flush=True)
        verify_plugins(claude, neutral)
        check_pricing_protocol(neutral)
        status = run([claude, "mcp", "get", SERVER], neutral)
        status = re.sub(r"\x1b\[[0-9;]*m", "", status)
        require(re.search(r"Status:\s*(?:[✓✔]\s*)?Connected(?:\s|$)", status), "Claude could not connect using the registered npx command: " + status[-1500:])
        require("User config" in status, "Claude did not resolve the user-scoped MCP configuration")
        print("PASS Claude connects to the user-scoped pricing server from another folder", flush=True)
    after = json.loads((config / ".claude.json").read_text())["mcpServers"][SERVER]
    require(before == after, "Verification modified the pricing server configuration")
    print("PASS verification finished without calling cloud tools or changing the MCP entry", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL {exc}", file=sys.stderr, flush=True)
        sys.exit(1)

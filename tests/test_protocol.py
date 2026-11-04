#!/usr/bin/env python3
"""Offline tests for forward-compatible, bounded MCP initialization probes."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("verifier", Path(__file__).resolve().parents[1] / "scripts/verify_installation.py")
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class ProtocolTests(unittest.TestCase):
    def test_current_and_future_versions(self):
        for version in ("2024-11-05", "2025-06-18", "2027-01-01"):
            with self.subTest(version=version):
                self.assertEqual(verifier.check_initialization({"protocolVersion": version, "capabilities": {"tools": {}}}), version)

    def test_invalid_or_missing_versions(self):
        for version in (None, 20250618, "latest", "2025-2-1", "2025-02-30", "2023-01-01"):
            with self.subTest(version=version), self.assertRaises(RuntimeError):
                verifier.check_initialization({"protocolVersion": version, "capabilities": {"tools": {}}})

    def test_missing_or_invalid_capabilities(self):
        for capabilities in (None, [], {}, {"tools": True}):
            with self.subTest(capabilities=capabilities), self.assertRaises(RuntimeError):
                verifier.check_initialization({"protocolVersion": "2025-06-18", "capabilities": capabilities})
        with self.assertRaises(RuntimeError):
            verifier.check_initialization([])


if __name__ == "__main__":
    unittest.main()

# Maintenance notes

## Pricing package source verification

On 2026-11-04, the npm registry metadata for `sample-aws-pricing-calculator-mcp@1.3.4` recorded Git commit `31493452d869cde2c586548b8070dd5adcfa53b1`. We downloaded the tarball without executing it, verified its registry SHA-512 integrity value, and compared every packaged file with [that exact AWS Samples commit](https://github.com/aws-samples/sample-aws-pricing-calculator-mcp/tree/31493452d869cde2c586548b8070dd5adcfa53b1). All 27 files matched byte for byte, including the executable bundle, catalog, manifest, README, and license.

The bundle `dist/mcp-server.js` has SHA-256 `039ca1415bb1f468a6b057a1b63586b2d9371deac7c32b240cffe016459e20fd`. The upstream README also recommends this exact npm package name. The registry lists one individual maintainer and no repository field. Matching source bytes establishes correspondence for this version; it does not establish that AWS controls the npm account or protect against future publisher compromise. Recheck the registry integrity, Git commit, and packaged files before changing the pinned version. This was a source comparison, not a reproducible-build or npm provenance-attestation audit.

## Claude CLI diagnostics

Claude Code 2.1.318's `claude mcp get --help` exposes no JSON or other structured-output option. The doctor and native verifier therefore still inspect its connection status text, after removing ANSI colors. They fail with a recovery message when the wording is unrecognized. Plugin listing and the isolated user configuration are checked as JSON; the native verifier also performs a live JSON-RPC initialize/tools-list exchange. Do not silently treat an exit code of zero as proof of a connected MCP server.

The protocol probe accepts valid date-based revisions from 2024-11-05 onward and then requires advertised tools and a successful tools/list response. This tests the common installation subset; it does not claim support for every feature in a future revision. See [MCP version negotiation](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle#version-negotiation).

## Missing v1.0.0 investigation

[Publish run 41853991832](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/actions/runs/41853991832) completed successfully and logged publication at 2026-11-04 15:05:06 UTC. The publishing script checks the public release, latest-release ID, and tag target before logging success.

The authenticated repository activity API subsequently reported deletion of `refs/tags/v1.0.0` at 15:06:03 UTC, with actor `ydsveluvolu2996`, before commit `c1e2b6f5ab816e3847f0316e8dea731bd3259556` and an all-zero after value. Activity ID: `48982444905`. GitHub labels this activity type `branch_deletion` even though the recorded ref is a tag. This proves that the tag existed and was later deleted under that account. It does not distinguish a browser action, API token, or automation using that account. The available repository activity does not identify the separate release-deletion action.

Restore only after both workflows pass on the current main commit. Never delete, replace, or retarget an existing release to make a rerun pass. Keep optional maintenance work on a separate PR so it cannot invalidate release evidence while macOS jobs wait for runner capacity.

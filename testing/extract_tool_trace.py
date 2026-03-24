#!/usr/bin/env python3
"""Extract MCP tool trace + reasoning from a Claude session NDJSON log.

Parses the stream-json output produced by the On-Call watcher and writes a
chronological trace of MCP tool calls and agent reasoning to a JSON file in
testing/manual_results/.

Usage:
    python3 testing/extract_tool_trace.py --test-id OC-001-ospf-passive
    python3 testing/extract_tool_trace.py --test-id OC-001-ospf-passive --file logs/.session-oncall-20260316-140522.tmp
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# MCP tool identification — mirrors dashboard/ws_bridge.py
# ---------------------------------------------------------------------------

_MCP_PREFIX = "mcp__mcp_automation__"


def _strip_tool_prefix(name: str) -> tuple[str, bool]:
    """Return (display_name, is_mcp). Mirrors ws_bridge._strip_tool_prefix."""
    if name.startswith(_MCP_PREFIX):
        return name[len(_MCP_PREFIX):], True
    return name, False


# ---------------------------------------------------------------------------
# NDJSON parser
# ---------------------------------------------------------------------------

def parse_session_log(path: Path) -> list[dict]:
    """Parse a stream-json NDJSON session log and return an ordered trace.

    Returns a list of trace entries, each a dict with one of these shapes:
      {"type": "reasoning", "text": "<coalesced text>"}
      {"type": "tool", "seq": N, "tool": "<name>", "input": {...}, "id": "<tool_use_id>"}
      {"type": "tool_result", "tool_seq": N, "output": "<text>"}
    """
    # --- State ---
    tool_inputs: dict[int, dict] = {}      # keyed by content-block index
    id_to_seq: dict[str, int] = {}         # tool_use_id → seq number
    tool_seq = 0

    trace: list[dict] = []
    pending_reasoning: list[str] = []     # text_delta chunks waiting to be flushed

    def flush_reasoning() -> None:
        text = "".join(pending_reasoning).strip()
        if text:
            trace.append({"type": "reasoning", "text": text})
        pending_reasoning.clear()

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            t = obj.get("type")

            # Final result line — nothing useful for the trace
            if t == "result":
                continue

            if t != "stream_event":
                continue

            ev = obj.get("event", {})
            ev_type = ev.get("type", "")

            # ------------------------------------------------------------------
            # Text reasoning — accumulate chunks
            # ------------------------------------------------------------------
            if ev_type == "content_block_delta":
                delta = ev.get("delta", {})
                if delta.get("type") == "text_delta":
                    pending_reasoning.append(delta.get("text", ""))

                elif delta.get("type") == "input_json_delta":
                    idx = ev.get("index", -1)
                    partial = delta.get("partial_json", "")
                    if idx in tool_inputs:
                        tool_inputs[idx]["json_buf"] += partial

            # ------------------------------------------------------------------
            # Content block start — tool_use or tool_result
            # ------------------------------------------------------------------
            elif ev_type == "content_block_start":
                cb = ev.get("content_block", {})
                cb_type = cb.get("type", "")

                if cb_type == "tool_use":
                    idx = ev.get("index", -1)
                    tool_id = cb.get("id", "")
                    name, is_mcp = _strip_tool_prefix(cb.get("name", ""))
                    tool_inputs[idx] = {
                        "json_buf": "",
                        "id": tool_id,
                        "name": name,
                        "is_mcp": is_mcp,
                    }

                elif cb_type == "tool_result":
                    tool_use_id = cb.get("tool_use_id", "")
                    content = cb.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") for c in content if isinstance(c, dict)
                        )
                    seq = id_to_seq.get(tool_use_id)
                    if seq is not None:
                        # Only emit results for MCP tools
                        flush_reasoning()
                        trace.append({
                            "type": "tool_result",
                            "tool_seq": seq,
                            "output": str(content),
                        })

            # ------------------------------------------------------------------
            # Content block stop — emit completed tool call if MCP
            # ------------------------------------------------------------------
            elif ev_type == "content_block_stop":
                idx = ev.get("index", -1)
                if idx in tool_inputs:
                    entry = tool_inputs.pop(idx)
                    if entry.get("id") and entry.get("is_mcp"):
                        # Flush any pending reasoning before this tool call
                        flush_reasoning()
                        tool_seq += 1
                        try:
                            input_obj = json.loads(entry["json_buf"]) if entry["json_buf"] else {}
                        except json.JSONDecodeError:
                            input_obj = {"raw": entry["json_buf"]}
                        id_to_seq[entry["id"]] = tool_seq
                        trace.append({
                            "type": "tool",
                            "seq": tool_seq,
                            "tool": entry["name"],
                            "input": input_obj,
                            "id": entry["id"],
                        })

    # Flush any trailing reasoning (after last tool call)
    flush_reasoning()
    return trace


# ---------------------------------------------------------------------------
# Auto-detect latest session log
# ---------------------------------------------------------------------------

def find_latest_session_log(logs_dir: Path) -> Path | None:
    """Return the most recently modified .session-*.tmp file in logs_dir."""
    candidates = list(logs_dir.glob(".session-*.tmp"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    repo_root = Path(__file__).parent.parent

    parser = argparse.ArgumentParser(
        description="Extract MCP tool trace + reasoning from a session NDJSON log."
    )
    parser.add_argument(
        "--test-id",
        required=True,
        help="Test identifier used as the output filename prefix (e.g. OC-001-ospf-passive)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Path to the NDJSON session log. Defaults to the latest .session-*.tmp in logs/",
    )
    args = parser.parse_args()

    # Resolve session log
    if args.file:
        session_file = args.file
    else:
        logs_dir = repo_root / "logs"
        session_file = find_latest_session_log(logs_dir)
        if session_file is None:
            print(
                "ERROR: No .session-*.tmp files found in logs/. "
                "Ensure DASHBOARD_RETAIN_LOGS=1 is set in .env and the watcher has run.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Auto-detected session log: {session_file}")

    if not session_file.exists():
        print(f"ERROR: Session log not found: {session_file}", file=sys.stderr)
        sys.exit(1)

    # Parse
    trace = parse_session_log(session_file)
    mcp_tool_count = sum(1 for e in trace if e["type"] == "tool")

    # Write output
    results_dir = repo_root / "testing" / "manual_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_path = results_dir / f"{args.test_id}_{ts}.json"

    output = {
        "test_id": args.test_id,
        "session_file": str(session_file),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "mcp_tool_count": mcp_tool_count,
        "trace": trace,
    }

    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)

    print(f"Trace written to: {out_path}")
    print(f"MCP tool calls captured: {mcp_tool_count}")


if __name__ == "__main__":
    main()

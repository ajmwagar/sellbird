"""Run the Sellbird CLI against a hosted install over HTTPS.

The hosted dashboard exposes an allowlisted `/remote-api/cli` endpoint behind
an API key. This module sends the argv there and prints the child process's
stdout/stderr, so commands keep the exact behaviour they have on the server
without needing the server's SQLite database locally.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

_REMOTE_COMMANDS = {"status", "companies", "outbox", "usage", "warmup", "runs",
                    "inboxes", "sending"}
_CONFIG = Path.home() / ".config" / "sellbird" / "remote.env"


def _load_config() -> None:
    """~/.config/sellbird/remote.env: SELLBIRD_API_URL and SELLBIRD_API_KEY."""
    if _CONFIG.is_file():
        load_dotenv(_CONFIG, override=False)


def configured() -> bool:
    _load_config()
    return bool(os.getenv("SELLBIRD_API_URL", "").strip()
                and os.getenv("SELLBIRD_API_KEY", "").strip())


def should_auto_remote(argv: list[str]) -> bool:
    """Normal commands use the hosted install when remote.env is configured."""
    if os.getenv("SELLBIRD_LOCAL", "").strip() in ("1", "true", "yes"):
        return False
    if not configured():
        return False
    return bool(argv) and argv[0] in _REMOTE_COMMANDS


def run(argv: list[str]) -> int:
    _load_config()
    base = os.getenv("SELLBIRD_API_URL", "").strip().rstrip("/")
    key = os.getenv("SELLBIRD_API_KEY", "").strip()
    args = list(argv)
    as_json = False
    while args and args[0].startswith("--"):
        if args[0] == "--url" and len(args) > 1:
            base = args[1].rstrip("/"); args = args[2:]
        elif args[0] == "--api-key" and len(args) > 1:
            key = args[1]; args = args[2:]
        elif args[0] == "--json":
            as_json = True; args = args[1:]
        else:
            break
    if not base or not key:
        print("  Remote Sellbird is not configured.\n"
              f"  Set SELLBIRD_API_URL and SELLBIRD_API_KEY in {_CONFIG} "
              "or pass --url/--api-key.", file=sys.stderr)
        return 2
    if not args:
        args = ["status"]
    try:
        resp = httpx.post(base + "/remote-api/cli", json={"argv": args},
                          headers={"Authorization": f"Bearer {key}",
                                   "Accept": "application/json"},
                          timeout=200)
        data = resp.json()
    except Exception as e:
        print(f"  Remote request failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(data, indent=2))
    else:
        out = data.get("stdout") or ""
        err = data.get("stderr") or ""
        if out:
            print(out, end="" if out.endswith("\n") else "\n")
        if err:
            print(err, end="" if err.endswith("\n") else "\n", file=sys.stderr)
        if not out and not err:
            print(json.dumps(data, indent=2))
    if resp.status_code >= 400:
        return 1
    return int(data.get("exit_code", 0) or 0)

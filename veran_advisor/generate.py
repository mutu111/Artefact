"""Minimal local prototype; accepts fictional JSON and records each actual run."""
import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from .prompt_loader import LOCAL_RUNS, PROMPT_VERSION, ROOT, SOURCE, assemble

VERSION = "v2.0"


def validate_output(output):
    if not isinstance(output, dict) or set(output) != {"status", "note", "messages"}:
        raise ValueError("Output must contain only status, note and messages")
    status, note, messages = output["status"], output["note"], output["messages"]
    if status not in {"ready", "blocked", "needs_information"} or not isinstance(note, str):
        raise ValueError("Invalid status or note")
    if not isinstance(messages, list) or any(not isinstance(m, str) or not m.strip() for m in messages):
        raise ValueError("Messages must be nonempty strings")
    if len(messages) != (3 if status == "ready" else 0):
        raise ValueError("Incorrect number of messages for status")
    if status != "ready" and not note.strip():
        raise ValueError("A non-ready response must explain the reason")
    if any(not re.search(r"[\u4e00-\u9fff]", m) for m in messages):
        raise ValueError("Each candidate must contain Chinese text")


def resolve_codex(explicit=None):
    if explicit:
        return explicit
    found = shutil.which("codex")
    if found:
        return found
    candidates = sorted((Path.home() / ".vscode/extensions").glob("openai.chatgpt-*/bin/windows-x86_64/codex.exe"))
    if candidates:
        return str(candidates[-1])
    raise FileNotFoundError("Codex CLI not found; use --codex with its executable path")


def main():
    parser = argparse.ArgumentParser(description="Generate Chinese advisor messages using local Codex CLI")
    parser.add_argument("case", type=Path, help="Path to a fictional JSON case")
    parser.add_argument("--case-id", help="Select one case from a JSON array")
    parser.add_argument("--preview", action="store_true", help="Assemble without calling a model")
    parser.add_argument("--model", default="gpt-6.1-terra", help="Defaults to the original pilot's model")
    parser.add_argument("--codex", help="Optional Codex executable path")
    args = parser.parse_args()
    raw_input = args.case.read_bytes()
    case = json.loads(raw_input.decode("utf-8-sig"))
    if args.case_id:
        if not isinstance(case, list):
            raise ValueError("--case-id requires a JSON array")
        matches = [item for item in case if item.get("case_id") == args.case_id]
        if len(matches) != 1:
            raise ValueError("Case ID must match exactly one case")
        case = matches[0]
        raw_input = json.dumps(case, ensure_ascii=False, indent=2).encode("utf-8")
    request = assemble(case)
    if args.preview:
        print(request["prompt"])
        return
    executable = resolve_codex(args.codex)
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = LOCAL_RUNS / run_id
    run_dir.mkdir(parents=True)
    prompt = request["prompt"]
    (run_dir / "input.json").write_bytes(raw_input)
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (run_dir / "source_prompt.md").write_bytes(SOURCE.read_bytes())
    (run_dir / "response_schema.json").write_bytes((ROOT / "config/response_schema.json").read_bytes())
    cmd = [executable, "exec", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only", "--model", args.model, "--output-schema", str(run_dir / "response_schema.json"), "--output-last-message", str(run_dir / "output.json"), "-"]
    metadata = {
        "version": VERSION, "prompt_version": PROMPT_VERSION, "run_id": run_id,
        "case_id": case.get("case_id"), "scenario": request["scenario"],
        "source_sha256": request["source_sha256"], "prompt_sha256": request["prompt_sha256"],
        "input_sha256": hashlib.sha256(raw_input).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "assembler_sha256": hashlib.sha256(Path(__file__).with_name("prompt_loader.py").read_bytes()).hexdigest(),
        "requested_model": args.model, "backend": "local Codex CLI",
        "command": cmd, "run_status": "started",
        "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    started = time.monotonic()
    try:
        result = subprocess.run(cmd, input=prompt, capture_output=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=180, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        (run_dir / "stderr.log").write_text(result.stderr, encoding="utf-8")
        (run_dir / "stdout.log").write_text(result.stdout, encoding="utf-8")
        metadata["return_code"] = result.returncode
        model_match = re.search(r"^model:\s*(.+)$", result.stderr, re.M)
        metadata["reported_model"] = model_match.group(1).strip() if model_match else None
        if result.returncode != 0:
            raise RuntimeError(f"Codex failed (exit {result.returncode}); see {run_dir / 'stderr.log'}")
        output = json.loads((run_dir / "output.json").read_text(encoding="utf-8-sig"))
        validate_output(output)
        metadata["run_status"] = "completed"
        metadata["mechanical_validation"] = "passed; semantic quality not evaluated automatically"
        print(json.dumps(output, ensure_ascii=False, indent=2))
        print(f"Run saved: {run_dir}", file=sys.stderr)
    except Exception as exc:
        metadata["run_status"] = "failed"
        metadata["error"] = str(exc)
        if isinstance(exc, subprocess.TimeoutExpired):
            for name, value in (("stdout.log", exc.stdout), ("stderr.log", exc.stderr)):
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="replace")
                (run_dir / name).write_text(value or "", encoding="utf-8")
        (run_dir / "error.txt").write_text(str(exc), encoding="utf-8")
        raise
    finally:
        metadata["elapsed_seconds"] = round(time.monotonic() - started, 2)
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()

"""Export portable run evidence without commands, machine paths or stderr logs."""
import json
from pathlib import PureWindowsPath

from veran_advisor.prompt_loader import LOCAL_RUNS, ROOT

META_FIELDS = (
    "version", "prompt_version", "run_id", "case_id", "scenario",
    "source_sha256", "prompt_sha256", "input_sha256", "generator_sha256",
    "assembler_sha256", "requested_model", "reported_model", "return_code",
    "run_status", "started_at_utc", "elapsed_seconds", "mechanical_validation",
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def export_evidence():
    target = ROOT / "evidence"
    target.mkdir(exist_ok=True)
    # A cloned repository already contains historical evidence, but not local logs.
    # Preserve that history when exporting new local runs.
    records_path = target / "recorded_runs.json"
    records = read(records_path) if records_path.exists() else {}
    for directory in sorted(LOCAL_RUNS.iterdir()):
        if not directory.is_dir() or not (directory / "output.json").exists():
            continue
        metadata = read(directory / "metadata.json")
        if metadata.get("return_code", 0) != 0:
            continue
        run_id = directory.name
        records[run_id] = {
            "metadata": {key: metadata[key] for key in META_FIELDS if key in metadata},
            "input": read(directory / "input.json"),
            "output": read(directory / "output.json"),
            "prompt": (directory / "prompt.txt").read_text(encoding="utf-8"),
        }
    for name in ("pilot_manifest.json", "final_manifest.json"):
        if not (LOCAL_RUNS / name).exists():
            continue
        original = read(LOCAL_RUNS / name)
        portable = []
        for row in original:
            if "error" in row:
                raise ValueError("Unresolved generation failure: " + row["case_id"])
            run_id = PureWindowsPath(row["run_dir"]).name
            if run_id not in records:
                raise ValueError("Missing raw record: " + run_id)
            portable.append({"case_id": row["case_id"], "run_id": run_id})
        (target / name).write_text(json.dumps(portable, ensure_ascii=False, indent=2), encoding="utf-8")
    (target / "recorded_runs.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(records)} recorded runs with portable metadata.")


if __name__ == "__main__":
    export_evidence()

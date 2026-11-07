"""Generate the fixed fictional cases, reusing exact matching completed requests."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys

from veran_advisor.generate import validate_output
from veran_advisor.prompt_loader import LOCAL_RUNS, ROOT, assemble

PILOT_IDS = ["G01", "PILOT-001", "A01", "X01", "I01", "P01"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", action="store_true", help="Only the six initial cases")
    args = parser.parse_args()
    cases = json.loads((ROOT / "data/test_cases.json").read_text(encoding="utf-8"))
    if args.pilot:
        cases = [case for case in cases if case["case_id"] in PILOT_IDS]

    def matching_run(case):
        request_hash = assemble(case)["prompt_sha256"]
        for meta_path in sorted(LOCAL_RUNS.glob("*/metadata.json"), reverse=True):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue  # Another case may still be writing its local metadata.
            if meta.get("run_status") == "completed" and meta.get("prompt_sha256") == request_hash and meta.get("reported_model") == "gpt-6.1-terra":
                output = json.loads((meta_path.parent / "output.json").read_text(encoding="utf-8-sig"))
                validate_output(output)
                return meta_path.parent
        return None

    def run_case(case):
        reused = matching_run(case)
        if reused:
            return {"case_id": case["case_id"], "run_dir": str(reused.relative_to(ROOT)), "reused": True}
        result = subprocess.run([sys.executable, "-m", "veran_advisor.generate", str(ROOT / "data/test_cases.json"), "--case-id", case["case_id"]], cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace", timeout=210)
        run_dir = matching_run(case)
        if result.returncode or not run_dir:
            return {"case_id": case["case_id"], "error": result.stderr[-2000:]}
        return {"case_id": case["case_id"], "run_dir": str(run_dir.relative_to(ROOT)), "reused": False}

    rows = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(run_case, case): case for case in cases}
        for future in as_completed(futures):
            case = futures[future]
            try:
                row = future.result()
            except Exception as exc:
                row = {"case_id": case["case_id"], "error": str(exc)}
            rows.append(row)
            print(row["case_id"], "FAILED" if "error" in row else "OK", flush=True)
    rows.sort(key=lambda row: next(i for i, case in enumerate(cases) if case["case_id"] == row["case_id"]))
    target = LOCAL_RUNS / ("pilot_manifest.json" if args.pilot else "final_manifest.json")
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(rows)} entries to {target}")
    if any("error" in row for row in rows):
        raise SystemExit(1)
    from scripts.export_evidence import export_evidence
    export_evidence()


if __name__ == "__main__":
    main()

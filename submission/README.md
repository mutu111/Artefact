# VÉRAN — submission materials

Open `report.html` to read the complete case. The report includes the work log, methodology, all 50 cases and 150 actual messages, evaluation, defects and before/after examples, and architecture.

Supporting files:

- `cases.json`: the 50 inputs and 150 original final-model messages.
- `evaluation.json`: lightweight review; 40 groups Pass, 10 Needs edit, 0 Fail. Reviewer: Codex-assisted, not an independent advisor panel.
- `brand.md`, `evaluation_method.md`, `work_log.md`, `prompt.md`: brand, method, process and detailed source prompt.
- `recorded_runs.json`, `final_manifest.json`, `pilot_manifest.json`: portable original requests, outputs and selected metadata. Local commands, executable paths and terminal logs are excluded.
- `run_evidence.html`: a viewer of an actual saved interaction, not an original chat screenshot.

Required screenshots and visual report QA remain pending. The report can be rebuilt from these files using the script in `../code/scripts/`. To generate new messages, double-click the launcher in the project root; Python, an authenticated local Codex CLI and network access are required.

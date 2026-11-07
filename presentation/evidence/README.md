# Recorded evidence

`recorded_runs.json` preserves actual inputs, assembled prompts, original model outputs and selected run metadata. `final_manifest.json` identifies the 50 final runs; `pilot_manifest.json` identifies the six v2.0 development runs used for the before/after comparison. Records are keyed by run ID.

The export omits local executable paths, full commands, terminal logs and local session details. It does not edit candidate messages. Original raw files remain locally under `.local/runs/`, outside Git. Source hashes and prompt hashes are retained where originally recorded.

Rebuild this export from the original local records with `python -m scripts.export_evidence`. The report can be rebuilt directly from the exported evidence, without the local originals or a model call.

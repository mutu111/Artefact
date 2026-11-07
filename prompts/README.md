# Prompt versions

- `veran_source_v1.0.md`: unchanged snapshot of the detailed shared rules and six scenario modules supplied by the user.
- `archive/prompt_v1.txt`: the initial short prompt, retained for provenance.
- `../veran_advisor/prompt_loader.py`: runtime assembly, JSON output contract and the v2.1 language refinement.

The runtime selects shared rules and one scenario, excludes unfilled input templates, and appends only the allowlisted case facts. Full assembled prompts used for actual recorded runs are retained in `../evidence/recorded_runs.json`. The source document's v1.0 label is distinct from runtime prompt versions v2.0 and v2.1.

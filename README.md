# Artefact — VÉRAN Chinese WeChat Advisor Assistant

A local message-drafting tool for a fictional, all-gender designer fashion brand. It covers six client-advisor scenarios and returns three short Chinese candidates for advisor review.

**Start with [the interview presentation folder](presentation/开始这里.html) or [the main report](reports/report.html).** Download or clone the repository and open the HTML file in a browser. GitHub's file viewer displays HTML source rather than the rendered report.

Current results: **50 fictional cases, 150 actual model messages; 40 groups Pass and 10 Needs edit** in a lightweight Codex-assisted review. Final prompt: `veran_scenarios_v2.1`. Required screenshots and visual report QA remain pending, so the report is a draft.

## Project layout

```text
veran_advisor/   Generation and prompt assembly
scripts/        Batch generation, evidence export, report builder
config/         Response JSON schema
prompts/        Supplied prompt snapshot and initial prompt
data/           50 fictional test inputs and a small example
evaluation/     Review labels and issue notes
reports/        Main report and final input/output data
evidence/       Portable original requests, outputs and metadata
docs/           Brand, evaluation method and work log
tests/          Regression checks
presentation/   Collected interview materials and standalone demo runtime
```

Local-only directories are excluded from Git: `private/` contains the confidential source brief, and `.local/` contains original runtime logs and older working drafts. The brief asks for confidentiality; use a private repository for recruitment review and do not publish the original brief.

## Run

For an interview, open `presentation/` and double-click `启动现场演示.vbs`. The local browser workbench lets you select a scenario, enter fresh fictional facts, generate three messages, copy a candidate and download the actual input/output record. `备用启动.cmd` is an alternative launcher. This folder includes the runtime source and all report materials; Python and authenticated Codex are still required for fresh generation.

Start the same workbench from the project root:

```powershell
python -m veran_advisor.demo
```

The default address is `http://127.0.0.1:8765/`. Close it using the workbench's shutdown button. Fresh interview runs stay separate from the original 50-case evaluation.

Use Python 3.10+ from the repository root. The Python code uses only the standard library. Fresh generation additionally requires an installed, authenticated Codex CLI; no credentials are stored in the repository.

Preview a request without calling the model:

```powershell
python -m veran_advisor.generate data/examples/case_001.json --preview
```

Generate three messages for one case:

```powershell
python -m veran_advisor.generate data/test_cases.json --case-id P01
```

The default model is `gpt-6.1-terra`. Use `--model` to change it or `--codex` to specify the executable path. Generated messages are not sent to clients.

Rebuild the report from committed evidence, without a model call:

```powershell
python -m scripts.build_report
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

For a fresh batch of all 50 cases, run `python -m scripts.batch_generate`. This uses the local CLI, reuses exact matching completed local requests and exports portable evidence. Newly generated outputs need a new review before existing evaluation labels can be reused. `python -m scripts.export_evidence` exports existing original local records separately.

After changing source or report materials, refresh the collected presentation folder with `python -m scripts.package_presentation`.

## Results and method

- [Main report: work log, methodology, 50 cases, evaluation and defects](reports/report.html)
- [50 cases and 150 original messages](reports/cases.json)
- [Review results](reports/evaluation.json)
- [Brand assumptions](docs/brand.md)
- [Lightweight evaluation method](docs/evaluation.md)
- [Work log](docs/work_log.md)
- [Original-run evidence](evidence/README.md)

The six scenarios are greetings, recommendations, aftercare, reactivation, invitations and price objections. `ready` returns three candidates; `blocked` and `needs_information` return an advisor note. Mechanical checks validate format and count. Factual accuracy, contact boundaries and natural Chinese still need review. The evaluation is assisted review of simulated cases, not independent advisor validation or evidence of customer conversion.

"""Build one local, self-contained submission report from recorded results."""
from collections import Counter
import html
import json
from pathlib import Path

from veran_advisor.prompt_loader import ROOT, SCENARIOS, SUBMISSION


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def esc(value):
    return html.escape(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))


def main():
    cases = read(ROOT / "data/test_cases.json")
    manifest = read(SUBMISSION / "final_manifest.json")
    evidence = read(SUBMISSION / "recorded_runs.json")
    reviews = read(SUBMISSION / "evaluation.json")
    records = {row["case_id"]: row for row in manifest}
    scores = {row["case_id"]: row for row in reviews["cases"]}
    assert len(cases) == len(records) == len(scores) == 50
    outputs = []
    for case in cases:
        record = records[case["case_id"]]
        if "error" in record:
            raise ValueError("Unresolved generation failure: " + case["case_id"])
        recorded = evidence[record["run_id"]]
        output, meta = recorded["output"], recorded["metadata"]
        assert output["status"] == "ready" and len(output["messages"]) == 3
        outputs.append({"input": case, "output": output, "prompt_version": meta["prompt_version"], "run_id": record["run_id"]})
    labels = Counter(row["label"] for row in reviews["cases"])
    counts = Counter(evidence[row["run_id"]]["metadata"]["scenario"] for row in manifest)
    out_dir = SUBMISSION
    out_dir.mkdir(exist_ok=True)
    (out_dir / "cases.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "evaluation.json").write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
    parts = ["""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>VÉRAN — Applied AI Written Challenge</title>
<style>body{font:16px/1.65 system-ui,'Microsoft YaHei',sans-serif;color:#20242a;background:#f5f4f0;margin:0}main{max-width:1150px;margin:auto;padding:42px 24px}h1{font-size:36px;line-height:1.2}h2{margin-top:48px;border-bottom:2px solid #ddd;padding-bottom:10px}h3{margin-top:28px}a{color:#295568}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #d8d8d2;text-align:left;padding:10px;vertical-align:top}th{background:#eaece8}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#fff;padding:16px;border:1px solid #ddd;font:14px/1.6 ui-monospace,monospace}.scroll{overflow-x:auto}#case-table{min-width:2100px}#case-table td{min-width:190px}#case-table td:nth-child(1){min-width:85px}.small{font-size:14px;color:#5a6065}.box{background:white;border:1px solid #ddd;padding:20px;margin:18px 0}.metrics{display:flex;gap:20px;flex-wrap:wrap}.metric{background:#fff;border:1px solid #ddd;padding:14px 22px}.metric b{display:block;font-size:28px}blockquote{margin:10px 0;padding:12px 16px;background:#fff;border-left:3px solid #44616a}.flow{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.flow span{border:1px solid #a5b4b6;background:#fff;padding:12px}figure{margin:24px 0}figure img{max-width:100%;border:1px solid #ccc}button{padding:8px 14px;border:1px solid #888;background:#fff;cursor:pointer}@media print{body{background:#fff}main{max-width:none}h2{break-before:page}.scroll{overflow:visible}#case-table{min-width:0;font-size:8px}#case-table td{min-width:0}button{display:none}}</style><main>
<p class="small">Confidential recruitment submission · Fictional brand and data · 7 November 2026</p><h1>VÉRAN<br>Chinese WeChat Message Assistant</h1><p>A working local prototype for client advisors at an experimental contemporary designer fashion house.</p>
<nav><a href="#work-log">A. Work log</a> · <a href="#method">B. Methodology</a> · <a href="#cases">C. 50 test cases</a> · <a href="#evaluation">D. Evaluation</a> · <a href="#defects">E. Defects and next steps</a> · <a href="#architecture">Architecture</a></nav>"""]
    parts.append(f'<div class="metrics"><div class="metric"><b>50</b>fictional cases</div><div class="metric"><b>150</b>actual model messages</div><div class="metric"><b>6</b>scenarios</div><div class="metric"><b>{labels["Pass"]}</b>groups passed assisted review</div></div>')
    parts.append('<p>Final outputs use <b>veran_scenarios_v2.1</b>, with model <b>gpt-6.1-terra</b> through the locally authenticated Codex CLI. Counts below describe this simulated dataset and assisted review, not a real-customer study.</p>')
    parts.append('<h2 id="work-log">A. Work log</h2><p>The actual sequence includes an early pilot before the detailed prompt and final evaluation rules. Steps are recorded as they occurred, rather than rewritten as a perfect process.</p><div class="scroll"><table><tr><th>Step</th><th>What you did</th><th>Input</th><th>Output</th><th>Tool or agent used</th><th>Screenshots</th></tr>')
    steps = [
        ("Read the brief", "Two-page supplied PDF", "Required deliverables, six scenarios and ground rules", "Codex; Python PDF extraction/rendering", "Earlier chat not captured"),
        ("Agree the fictional brand", "User choices and corrections", "All-gender designer fashion; experimental design; RMB 3,000–8,000 positioning", "User and Codex chat", "Earlier chat not captured"),
        ("Define the first tool and language rules", "Brand assumptions and brief", "Input/output design; warm, concise Chinese", "Codex", "Earlier chat not captured"),
        ("Build and run the first prototype", "Old v1 prompt and PILOT-001", "Three actual messages and retained logs", "Python; Codex CLI", "Original terminal/chat screenshot not captured"),
        ("Review initial defects", "Original three messages", "Long sentences, repetition and ambiguous form of address", "Codex-assisted review", "Earlier chat not captured"),
        ("Integrate the user-supplied detailed prompt", "Shared rules plus six scenario modules", "Versioned snapshot, routing and JSON output contract", "User-provided prompt; Codex implementation", "Source file and prompt snapshots retained; earlier chat not captured"),
        ("Check integration and re-run the same facts", "Regression fixtures and original pilot facts", "Six program checks passed; actual v2.0 comparison", "Python unittest; Codex CLI", "Raw records retained"),
        ("Prepare a lightweight test set and rubric", "Brief requirements and user request for simplicity", "50 fictional inputs; four pass/issue checks", "Codex", "Planning chat not captured"),
        ("Run six initial cases", "One case per scenario, v2.0", "18 messages and a short pilot defect review", "Python; Codex CLI; Codex-assisted review", "Raw run records retained; screenshot not captured"),
        ("Revise language guidance once", "Pilot defects", "v2.1 short-sentence and everyday-language guidance", "Codex", "Before/after raw records linked below"),
        ("Generate the final 50 cases", "Fixed fictional inputs and v2.1", "150 original messages with per-run evidence", "Python; Codex CLI", "See screenshot below" if (out_dir / "generation.png").exists() else "Pending capture; raw output retained"),
        ("Review outputs and assemble submission", "Final outputs and four checks", "Evaluation, representative defects and this report", "Codex-assisted review; Python", "See screenshot below" if (out_dir / "evaluation.png").exists() else "Pending capture; review data retained"),
        ("Organize repository for review", "Existing source files, reports and raw runs", "Clear folders and portable evidence; confidential source brief and local logs excluded from Git", "Codex; Python; Git", "Not captured"),
        ("Add a local workbench and collect submission materials", "Existing generator and request for a simple way to test new inputs", "Local form and launcher; a fresh case generated three actual messages", "Python local server; Codex CLI", "Browser preview unavailable; HTTP flow verified, screenshot pending"),
        ("Simplify the submission structure", "Request for clearer opening instructions and fewer folders", "Two folders: submission and code; direct report and tool entry points", "Codex; Python; Git", "Not captured"),
    ]
    for i, step in enumerate(steps, 1):
        parts.append('<tr><td>' + str(i) + '</td>' + ''.join('<td>' + esc(v) + '</td>' for v in step) + '</tr>')
    parts.append('</table></div><p class="small">Evidence limitation: screenshots of the earlier planning AI chats were not captured. The retained logs and snapshots are supporting records, not substitutes for those screenshots. Attach available original chat screenshots before final submission. Later recorded-run screenshots are explicitly labeled as a viewer captured after execution.</p>')
    parts.append('''<h2 id="method">B. Methodology</h2><h3>Brand assumptions</h3><p>VÉRAN is a fictional, all-gender contemporary designer fashion house offering ready-to-wear, footwear, bags and accessories. Its experimental design language includes unexpected proportions and asymmetry. Typical featured prices are RMB 3,000–8,000; case-specific product facts are authoritative. The advisor should sound warm, concise and natural in Chinese, without formal luxury clichés or sales pressure.</p>
<h3>Tool design</h3><p>Each request combines the shared brand and factual rules, exactly one scenario module, and supplied case facts. The model returns structured JSON: three messages and a separate advisor note for eligible cases. Missing facts stay unknown. Explicit opt-outs use a no-send branch. Evaluation expectations are excluded from the generation input. A small validator checks status, count and Chinese text; it does not establish truthfulness or naturalness. Advisors review drafts before use; the tool sends nothing.</p>
<h3>Test design and iteration</h3><p>The 50 concise fictional cases cover greetings (8), recommendations (9), aftercare (8), reactivation (8), invitations (8) and price objections (9). They vary stated preferences, relationship, known facts and common concerns: unknown discounts, complaints, incomplete event details, latest preferences and declined purchases. Six cases were used for the initial review. One consolidated language revision produced v2.1, which was then run on all 50 cases, including those six. The 50-case results therefore are not an untouched independent test set.</p>
<h3>What good and unacceptable mean</h3><p>Good messages are grounded in supplied facts, respond to the latest need, read like short friendly WeChat messages, and provide three useful choices. Unacceptable outputs invent consequential facts or promises, violate explicit contact limits, give unsupported care instructions, miss the actual question, or fail to provide the required candidates. Small style or variation problems are marked “Needs edit”.</p>
<p>Review uses four pass/issue checks per group: facts and boundaries; scenario and context; Chinese expression; three useful choices. A group passes only if all four pass. Serious factual, boundary or task failures are labeled “Fail”. Technical execution failures are recorded separately and never counted as passes. The reviewer is Codex-assisted; no independent advisor panel or customer outcome study was conducted.</p>''')
    parts.append('<h2 id="cases">C. 50 test cases and actual outputs</h2><p>Each row contains the original case facts and three unedited final model messages. The extra scenario-context column preserves occasions, events, purchases, policies and other relevant inputs. Scroll horizontally to view all required columns. <a href="cases.json">Structured input/output data</a>.</p><div class="scroll"><table id="case-table"><tr><th>Case ID</th><th>Scenario</th><th>Client information</th><th>Conversation history</th><th>Product information</th><th>Scenario context</th><th>Output 1</th><th>Output 2</th><th>Output 3</th><th>Advisor note / version</th></tr>')
    for record in outputs:
        case, output = record["input"], record["output"]
        client = {k: case[k] for k in ("client_information", "relationship", "contact_preferences") if k in case}
        context = {k: v for k, v in case.items() if k not in {"case_id", "scenario", "client_information", "relationship", "contact_preferences", "conversation_history", "product_information"}}
        values = [case["case_id"], case["scenario"], client, case.get("conversation_history", []), case.get("product_information", "Not provided / not applicable"), context, *output["messages"], {"note": output["note"], "version": record["prompt_version"]}]
        parts.append('<tr>' + ''.join('<td>' + esc(v) + '</td>' for v in values) + '</tr>')
    parts.append('</table></div><h2 id="evaluation">D. Evaluation report</h2>')
    parts.append(f'<p>All 50 final requests completed and produced three Chinese candidates each (150 messages). Case-group assisted-review labels: <b>{labels["Pass"]} Pass</b>, <b>{labels["Needs edit"]} Needs edit</b>, <b>{labels["Fail"]} Fail</b>. These are group-level results; no separate message-level pass rate is claimed.</p>')
    parts.append('<table><tr><th>Scenario</th><th>Cases</th></tr>' + ''.join(f'<tr><td>{esc(SCENARIOS[k])}</td><td>{v}</td></tr>' for k,v in counts.items()) + '</table>')
    parts.append('<h3>Review table</h3><p>Pass/issue refers to the three-message group. Short notes identify the affected output when an issue was found. <a href="evaluation.json">Structured review data</a>.</p><div class="scroll"><table><tr><th>Case</th><th>Facts / boundaries</th><th>Scenario / context</th><th>Chinese expression</th><th>Useful choices</th><th>Label</th><th>Issue note</th></tr>')
    for row in reviews["cases"]:
        parts.append('<tr>' + ''.join('<td>' + esc(row[k]) + '</td>' for k in ("case_id", "facts", "context", "expression", "choices", "label", "note")) + '</tr>')
    parts.append('</table></div><p class="small">Reviewer: ' + esc(reviews["reviewer"]) + '</p>')
    if not (out_dir / "generation.png").exists() or not (out_dir / "evaluation.png").exists():
        parts.append('<div class="box"><b>Submission evidence still pending:</b> generation/evaluation screenshots and available earlier AI-chat screenshots must be added before final submission. Automated UI capture was attempted but the browser connection and native input could not be used reliably. Raw runs and the <a href="run_evidence.html">recorded-run viewer</a> are retained; they are not represented as screenshots.</div>')
    for image_name, caption in (("generation.png", "Actual recorded-run viewer, captured after model execution; not a screenshot of an original planning chat."), ("evaluation.png", "Evaluation summary and review table captured from this report.")):
        if (out_dir / image_name).exists():
            parts.append(f'<figure><img src="{image_name}" alt="{esc(caption)}"><figcaption>{esc(caption)}</figcaption></figure>')
    parts.append('<h2 id="defects">E. Defects, changes and next steps</h2><p>The initial v2.0 review found long sentences, formal check-ins, repeated hedging and similar alternatives. v2.1 added short-sentence guidance, everyday-language examples, and a rule against inventing advisor actions such as “recently compiled”. Only genuine raw before/after outputs are shown below; this does not establish general improvement.</p>')
    initial = {row["case_id"]: row for row in read(SUBMISSION / "pilot_manifest.json")}
    for case_id in ("A01", "PILOT-001", "I01"):
        old_record = evidence[initial[case_id]["run_id"]]
        old = old_record["output"]["messages"][0]
        old_version = old_record["metadata"]["prompt_version"]
        new = next(row for row in outputs if row["input"]["case_id"] == case_id)["output"]["messages"][0]
        parts.append(f'<h3>{esc(case_id)}</h3><p class="small">Before: {esc(old_version)}, Output 1</p><blockquote>{esc(old)}</blockquote><p class="small">After: veran_scenarios_v2.1, Output 1</p><blockquote>{esc(new)}</blockquote>')
    parts.append('<p>Remaining issues are those recorded in the review table. Next improvements should focus on the recurring expression and variation defects, explicit no-contact and embedded-instruction boundary tests, and confirmation by real advisors. Product knowledge must be expanded with verified fictional case facts rather than generic assumptions. The local CLI dependency means a reviewer needs the authenticated runtime to generate new inputs; a public model endpoint has not been deployed.</p>')
    parts.append('''<h2 id="architecture">Bonus: architecture</h2><div class="flow"><span>Advisor input / local form</span>→<span>Shared rules + one scenario + known facts</span>→<span>Codex CLI / model</span>→<span>JSON validation</span>→<span>3 Chinese drafts + separate note</span>→<span>Advisor review</span></div><p class="small">Exact input, assembled prompt, versions, hashes, output and execution metadata are retained per run. The no-send and insufficient-information statuses return an advisor note rather than customer messages.</p><h2>Using the tool</h2><p>Double-click the tool launcher in the project root. The local form accepts new inputs, displays three Chinese candidates and a separate advisor note, and lets the advisor copy or download results. The submission folder contains the report and supporting material; the code folder contains the implementation. New generation requires Python, an authenticated Codex CLI and network access.</p><p>Alternatively, run these commands from the code folder:</p><pre>python -m veran_advisor.demo
python -m veran_advisor.generate data/examples/case_001.json
python -m veran_advisor.generate data/test_cases.json --case-id P01
python -m scripts.batch_generate</pre><p>The code and portable run evidence remain in the project directory. This report opens locally without an account; generating fresh results requires Python and the authenticated Codex CLI. No messages are sent and nothing has been published.</p></main></html>''')
    (out_dir / "report.html").write_text('\n'.join(parts), encoding="utf-8")
    # Faithful record viewer for evidence capture; clearly not an original chat UI.
    sample = next(row for row in outputs if row["input"]["case_id"] == "A02")
    trace = '<!doctype html><meta charset="utf-8"><title>Recorded model run</title><style>body{font:18px/1.6 system-ui,"Microsoft YaHei";max-width:1050px;margin:30px auto;color:#222}pre{white-space:pre-wrap;background:#f5f5f0;padding:20px}h1{font-size:28px}</style><h1>VÉRAN — actual recorded model interaction</h1><p>Case A02 · veran_scenarios_v2.1 · gpt-6.1-terra<br>Record viewer captured after execution, not an original chat screenshot.</p><h2>Input facts</h2><pre>' + esc(json.dumps(sample["input"], ensure_ascii=False, indent=2)) + '</pre><h2>Actual original output</h2><pre>' + esc(json.dumps(sample["output"], ensure_ascii=False, indent=2)) + '</pre><p>Run ID in recorded_runs.json: ' + esc(sample["run_id"]) + '</p>'
    (out_dir / "run_evidence.html").write_text(trace, encoding="utf-8")
    print(json.dumps({"cases": len(outputs), "messages": sum(len(row["output"]["messages"]) for row in outputs), "labels": dict(labels), "report": str(out_dir / "report.html")}))


if __name__ == "__main__":
    main()

"""Render the recorded case as a readable GitHub README and one standalone HTML."""
from collections import Counter
import base64
import html
import json
from pathlib import Path

from veran_advisor.prompt_loader import PROJECT_ROOT, ROOT, SCENARIOS, SUBMISSION

LABELS = {"Pass": "通过", "Needs edit": "需修改", "Fail": "不通过"}
FIELDS = {
    "client_id": "虚构编号", "preferred_address": "称呼", "preferences": "偏好",
    "name": "名称", "details": "设计", "price_rmb": "价格", "date": "日期",
    "time": "时间", "place": "地点", "content": "内容", "participation": "参加条件",
    "client_information": "客户信息", "relationship": "关系", "contact_preferences": "联系偏好",
    "occasion": "场合", "purchase_information": "购买记录", "care_information": "护理信息",
    "event_information": "活动信息", "policy_information": "政策", "reference_date": "参考日期",
    "scenario_details": "本次任务",
}
ISSUES = {
    "G02": "候选 2 的“值此中秋”偏正式，与刚建立联系的微信语气不够贴合。",
    "G08": "候选 3 的“向您送上一句问候”生硬，可以更直接。",
    "R04": "三条都重复方头、侧拉链和了解更多，选择差异较小。",
    "R09": "三条主要重复针法拼接和价格，实质差异较小。",
    "A01": "候选 3 的“想关心一下您上周买的折线衬衫”仍不够自然。",
    "I01": "候选 2、3 的活动信息仍集中在长句中；候选 2 的结尾偏生硬。",
    "I03": "候选 1、3 的活动句偏长；候选 2 的结尾有模板感。",
    "I05": "三条都把“虚构的”直接写进客户消息，而且内容高度相似。",
    "I08": "三条都沿用主题、时间地点、邀请的相同结构，选择价值有限。",
    "P06": "三条重复“具体定价依据”，表达偏技术化、不够口语。",
}
STEPS = [
    ("阅读题目，确认交付范围", "两页笔试说明", "明确 A–E、六场景及虚构数据要求", "Codex＋PDF 阅读", "未截取"),
    ("确定品牌定位与语气", "用户选择及修正", "VÉRAN：男女全品类、先锋设计；中文亲切短句", "用户＋Codex", "未截取"),
    ("定义输入与三候选输出", "品牌和业务要求", "输入字段、事实边界、顾问审核流程", "Codex", "未截取"),
    ("搭建最小工具并运行初版", "v1 提示词＋西装推荐案例", "首次真实生成三条话术，保留原始记录", "Python＋Codex CLI", "未截取"),
    ("检查初版问题", "首次三条输出", "发现长句、重复和称呼不明确", "Codex 辅助审阅", "未截取"),
    ("接入详细六场景提示词", "用户提供的规则文档", "统一规则＋单场景路由；同案例复跑和程序检查", "Python＋Codex CLI", "未截取"),
    ("准备测试输入和简明评估标准", "六场景及常见边界", "50 个虚构案例；四项通过／问题检查", "Codex＋Python", "未截取"),
    ("先运行六例开发案例", "每场景一例，v2.0", "18 条原始话术及初步问题清单", "Codex CLI＋辅助审阅", "未截取"),
    ("集中调整表达要求", "六例中的长句和模板感", "v2.1：短句、日常表达、减少无依据动作", "Codex", "未截取"),
    ("以最终版本生成全部 50 例", "固定输入＋v2.1", "150 条原始话术，记录版本和运行信息", "Python＋Codex CLI", "待补"),
    ("评估并记录缺陷", "150 条输出及对应输入", "40 组通过、10 组需修改；保留具体问题", "Codex 辅助审阅", "待补"),
    ("建立新案例输入页面", "同一生成流程＋新虚构输入", "新案例实际返回三条话术；10 项程序检查通过", "Python＋Codex CLI", "待补"),
    ("整理提交文件与报告", "输入、输出、评估及版本记录", "README 直接展示 A–E；完整 HTML；两个文件夹", "Python＋Git", "未截取"),
]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def human(value, key=""):
    if value is None or value == "" or value == [] or value == {}:
        return "未提供"
    if isinstance(value, dict):
        if "speaker" in value and "message" in value:
            return f'{value["speaker"]}：{value["message"]}'
        return "；".join(f'{FIELDS.get(k, k)}：{human(v, k)}' for k, v in value.items())
    if isinstance(value, list):
        return "\n".join(human(item) for item in value) or "无"
    if key == "price_rmb" and isinstance(value, (int, float)):
        return f"人民币 {value:,.0f} 元"
    return str(value)


def inputs(case):
    client = human(case.get("client_information"))
    for key in ("relationship", "contact_preferences"):
        if key in case:
            client += f"；{FIELDS[key]}：{human(case[key])}"
    extras = [f'{FIELDS[key]}：{human(case[key])}' for key in (
        "occasion", "purchase_information", "care_information", "event_information",
        "policy_information", "reference_date", "scenario_details",
    ) if key in case]
    return [
        ("客户信息", client),
        ("最近聊天", human(case.get("conversation_history")) if case.get("conversation_history") else "无"),
        ("产品信息", human(case.get("product_information")) if case.get("product_information") else "不适用／未提供"),
        ("场景补充", "\n".join(extras) or "无"),
    ]


def esc(text):
    return html.escape(str(text))


def md(text):
    return esc(text).replace("|", "\\|").replace("\n", "<br>")


def md_table(headers, rows):
    return "\n".join([
        "| " + " | ".join(md(v) for v in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(md(v) for v in row) + " |" for row in rows),
    ])


def htable(headers, rows, cls=""):
    return f'<div class="table-wrap"><table class="{cls}"><thead><tr>' + ''.join(f'<th>{esc(v)}</th>' for v in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + esc(v).replace('\n','<br>') + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def load_results():
    source = read(ROOT / "data/test_cases.json")
    manifest = read(SUBMISSION / "final_manifest.json")
    evidence = read(SUBMISSION / "recorded_runs.json")
    review = read(SUBMISSION / "evaluation.json")
    by_id = {row["case_id"]: row for row in manifest}
    scores = {row["case_id"]: row for row in review["cases"]}
    assert len(source) == len(manifest) == len(scores) == 50
    results = []
    for case in source:
        run_id = by_id[case["case_id"]]["run_id"]
        record = evidence[run_id]
        assert record["output"]["status"] == "ready" and len(record["output"]["messages"]) == 3
        results.append({"input": case, "output": record["output"], "prompt_version": record["metadata"]["prompt_version"], "run_id": run_id, "scenario": record["metadata"]["scenario"], "review": scores[case["case_id"]]})
    return results, evidence, review


def case_markdown(result):
    case = result["input"]
    lines = [f'**{case["case_id"]}｜{SCENARIOS[result["scenario"]]}**', '', md_table(["输入项", "本例内容"], inputs(case)), '']
    for i, message in enumerate(result["output"]["messages"], 1):
        lines.extend([f'**Output {i}｜候选 {i}**', '', '> ' + esc(message).replace('\n','\n> '), ''])
    if result["output"]["note"]:
        lines.extend(['顾问备注：' + esc(result["output"]["note"]), ''])
    score = result["review"]
    lines.extend([f'评估：**{LABELS[score["label"]]}**。' + (' ' + ISSUES[case["case_id"]] if case["case_id"] in ISSUES else '') + ' 提示词版本：v2.1。', '', '---', ''])
    return '\n'.join(lines)


def case_html(result):
    case = result["input"]
    label = result["review"]["label"]
    rows = inputs(case)
    history = case.get("conversation_history")
    if isinstance(history, list) and history:
        title = history[-1].get("message", "")
    elif isinstance(history, str) and history:
        title = history
    else:
        title = human(case.get("occasion") or case.get("scenario_details") or SCENARIOS[result["scenario"]])
    title = title[:58] + ("…" if len(title)>58 else "")
    search = human(case) + ' ' + ' '.join(result["output"]["messages"])
    parts = [f'<details class="case" data-scenario="{result["scenario"]}" data-search="{esc(search.lower())}"><summary><span class="case-id">{case["case_id"]}</span><span class="case-topic">{esc(title)}</span><span class="badge {"edit" if label!="Pass" else "pass"}">{LABELS[label]}</span></summary><div class="case-body">']
    parts.append('<dl class="inputs">' + ''.join(f'<dt>{esc(k)}</dt><dd>{esc(v).replace(chr(10),"<br>")}</dd>' for k,v in rows) + '</dl>')
    for i,message in enumerate(result["output"]["messages"],1):
        parts.append(f'<div class="message"><span class="message-label">候选 {i}</span><p>{esc(message)}</p></div>')
    if result["output"]["note"]:
        parts.append('<p class="advisor-note"><b>顾问备注：</b>' + esc(result["output"]["note"]) + '</p>')
    if case["case_id"] in ISSUES:
        parts.append('<p class="issue"><b>需修改：</b>' + esc(ISSUES[case["case_id"]]) + '</p>')
    parts.append('<p class="meta">原始模型输出 · 提示词 v2.1</p></div></details>')
    return ''.join(parts)


def build_sections(results, evidence):
    counts = Counter(row["review"]["label"] for row in results)
    scenario_rows = []
    for key,name in SCENARIOS.items():
        group = [r for r in results if r["scenario"]==key]
        labels = Counter(r["review"]["label"] for r in group)
        scenario_rows.append((name,len(group),len(group)*3,labels["Pass"],labels["Needs edit"],labels["Fail"]))
    quality_rows = []
    for key,name in (("facts","事实与边界"),("context","场景与上下文"),("expression","中文表达"),("choices","候选差异")):
        issue = sum(r["review"][key]!="Pass" for r in results)
        quality_rows.append((name,50-issue,issue))
    issue_rows = [(r["input"]["case_id"],SCENARIOS[r["scenario"]],ISSUES[r["input"]["case_id"]]) for r in results if r["review"]["label"]!="Pass"]
    initial = {r["case_id"]:r["run_id"] for r in read(SUBMISSION / "pilot_manifest.json")}
    comparisons = []
    for case_id,index,change in (
        ("X01",1,"去掉没有输入依据的“最近整理到”，改为回应客户明确表达的兴趣。"),
        ("A01",2,"减少公文式问候，但最终候选仍不够自然，因此继续标为需修改。"),
        ("P01",0,"保留“先核实折扣”的事实边界，压缩泛泛的铺垫。"),
    ):
        before=evidence[initial[case_id]]["output"]["messages"][index]
        after=next(r for r in results if r["input"]["case_id"]==case_id)["output"]["messages"][index]
        comparisons.append((case_id,index+1,before,after,change))
    return counts,scenario_rows,quality_rows,issue_rows,comparisons


def build_markdown(results, evidence):
    counts,scenario_rows,quality_rows,issue_rows,comparisons=build_sections(results,evidence)
    parts=['# VÉRAN｜客户顾问微信话术生成工具', '',
        '## 项目背景 · Project background', '',
        'VÉRAN 是一个虚构的先锋设计师时装品牌，面向男女客户，覆盖成衣、鞋履、包袋和配饰，主要价格定位为人民币 3,000–8,000 元。客户顾问需要在微信上自然地维护关系，同时准确回应客户的问题。', '',
        '本工具接收**客户信息、沟通场景、最近聊天和相关产品／活动信息**，生成 **3 条可独立发送的中文候选话术**，由顾问审核后选择。表达要求是亲切、简洁、易读，不编造信息，也不强迫购买。', '',
        '**本页直接包含 A–E 的结果，以及全部 50 个案例；不需要打开 JSON 文件。**', '',
        '## 仓库结构 · Repository', '',
        '```text\nREADME.md          当前页面：直接阅读 A–E 全部结果\n打开报告.html      同一份内容的完整离线阅读版\n启动工具.cmd       打开表单，输入新案例并生成话术\nsubmission/        报告依据、原始结果、提示词与工作记录\ncode/              生成工具、测试与报告构建代码\n```', '',
        '## 结果概览', '',
        md_table(['覆盖场景','测试案例','实际话术','辅助评估通过','需修改'],[['6 类','50 例','150 条',f'{counts["Pass"]} 组',f'{counts["Needs edit"]} 组']]), '',
        '最终提示词：**v2.1**；生成模型：**gpt-6.1-terra**。评估是 Codex 辅助审阅，单位为“每例的三条候选”，不代表独立顾问验证或真实客户转化效果。', '',
        '[A 工作日志](#a-work-log) · [B 方法说明](#b-methodology) · [C 50 个案例](#c-50-test-cases) · [D 评估结果](#d-evaluation) · [E 缺陷与改进](#e-defects-and-next-steps)', '',
        '## A. Work log', '',
        '以下按实际开展顺序记录。原始输入、提示词、输出和版本已保存；历史 AI 对话截图，以及生成／评估截图尚未补齐，日志不作为截图替代品。', '',
        md_table(['Step','做了什么','Input','Output','工具','截图'],[(i,*row) for i,row in enumerate(STEPS,1)]), '',
        '## B. Methodology', '',
        '**品牌与沟通假设。** VÉRAN 的设计可以前卫，但顾问的表达应自然、有分寸。只使用本次提供的事实；客户最新表态优先。未知信息可以省略或核实，明确拒绝联系时停止营销草稿。', '',
        '**生成流程。** 客户输入 → 统一品牌规则＋对应场景规则 → 模型生成 → 格式检查 → 三条中文候选＋独立顾问备注。工具不自动发送消息。', '',
        '**测试设计。** 六个场景共 50 例，覆盖普通沟通、偏好变化、信息缺失、售后不满、活动安排和价格问题。先用六例发现问题，集中调整到 v2.1，再用该版本运行全部 50 例。这 50 例不是完全独立的留出测试集。', '',
        md_table(['场景','例数','重点'],[
            ('生日与节日问候',8,'真诚祝福；不借问候推销，不猜生日或家庭情况'),
            ('产品推荐',9,'关联已知需求；不编材质、库存、优惠或合身效果'),
            ('售后关怀',8,'回应使用反馈和问题；不编护理方法或服务承诺'),
            ('沉睡客户唤醒',8,'轻量重建联系；不追问缺席原因、不制造愧疚'),
            ('活动邀请',8,'讲清已知安排；不编名额、礼品或预留权益'),
            ('价格异议',9,'回应折扣、比价或预算问题；政策未知时先核实'),
        ]), '',
        '**什么是好结果？** 事实准确、回应当前问题、中文自然简短，三条候选有选择价值。', '',
        '**什么不可接受？** 编造重要事实或商业承诺、违反明确联系限制、错误护理建议、答非所问，或没有按要求给出三条候选。', '',
        '**评估方式。** 每组三条话术只检查四项：事实与边界、场景与上下文、中文表达、候选差异。四项均通过记为“通过”；表达或重复问题记为“需修改”；事实、边界或任务错误记为“不通过”。有问题时只记录一句具体原因。', '',
        '## C. 50 test cases', '',
        '下面先展示一个完整案例，再按六个场景展开全部 50 例。所有候选均为模型原始输出，未做人工润色；客户、产品和活动均为虚构。', '',
    ]
    example=next(r for r in results if r['input']['case_id']=='PILOT-001')
    parts.extend([case_markdown(example), '### 全部案例（按场景展开）', ''])
    for key,name in SCENARIOS.items():
        group=[r for r in results if r['scenario']==key]
        parts.extend([f'<details>\n<summary><b>{name}｜{len(group)} 例</b></summary>', '', *(case_markdown(r) for r in group), '</details>', ''])
    parts.extend(['完整 HTML 还提供按编号／产品搜索、按场景筛选，以及题目规定列的 50 行表格视图。', '',
        '## D. Evaluation', '',
        f'**50 例均完成生成，共 150 条中文话术。辅助评估结果：{counts["Pass"]} 组通过，{counts["Needs edit"]} 组需修改，{counts["Fail"]} 组不通过。**', '',
        '通过表示本次辅助审阅未发现需要标出的问题，不等于工具不会出错。以下按案例组统计，不把组级结果当成单条消息通过率。', '',
        md_table(['场景','案例','话术','通过','需修改','不通过'],scenario_rows), '',
        '**四项检查结果**（同一例可能在多项上有问题）：', '',
        md_table(['检查项','通过组数','有问题组数'],quality_rows), '',
        '**需要修改的 10 例：**', '',
        md_table(['Case ID','场景','具体问题'],issue_rows), '',
        '主要问题集中在活动邀请的长句和模板感，以及部分候选重复。I05 还把数据标签“虚构的”写进了客户消息，应优先修正。未标出问题的案例及原始话术均可在 C 部分直接查看。评估截图待补。', '',
        '## E. Defects and next steps', '',
        '**已经做过的调整。** v2.0 的六例开发运行暴露了长句、正式问候和重复表达。v2.1 加入短句要求、日常表达指导，并禁止编造“最近整理”“专门挑选”等顾问动作。以下是真实运行记录中的同案例、同候选编号对比；这类对比不证明整体因果改进。', '',
    ])
    for case_id,index,before,after,change in comparisons:
        parts.extend([f'**{case_id} · 候选 {index}**', '', '**修改前 · v2.0**', '', '> '+esc(before), '', '**修改后 · v2.1**', '', '> '+esc(after), '', change, ''])
    parts.extend(['**仍需改进。** 优先处理 I05 的数据标签外露、活动邀请中的长句，以及重复候选。修订后应对相同输入复跑并保留新版本；当前 150 条结果保持原样，未用人工修改覆盖。后续还需补做明确拒绝联系和聊天内嵌指令的边界测试，并邀请实际顾问审阅。', '',
        '**提交证据。** AI 对话与生成／评估截图仍需补齐；本页不把原始日志或重新排版的记录冒充截图。', '',
        '### 工具架构 · Architecture', '',
        '输入表单 → 品牌与场景规则 → Codex CLI／模型 → 输出格式检查 → 三条候选＋顾问备注 → 顾问审核', '',
        '### 如何运行', '',
        '- **阅读完整离线版：** 下载仓库 ZIP 并解压，双击最外层的 **打开报告.html**。',
        '- **测试新案例：** 双击 **启动工具.cmd**，在浏览器填写案例并点击生成。',
        '- 新生成需要 Python 3.10+、已登录的 Codex CLI 和可用网络；现有结果可直接离线阅读。', '',
        '<details>\n<summary>代码运行与复现命令</summary>', '',
        '在 `code` 文件夹中执行：', '',
        '```powershell\npython -m veran_advisor.demo\npython -m unittest discover -s tests -v\npython -m scripts.build_report\n```', '',
        '报告构建只使用已保存的结果，不调用模型。批量新生成使用 `python -m scripts.batch_generate`，新输出需要重新评估。原始本机日志和题目 PDF 未上传。', '', '</details>', '',
    ])
    return '\n'.join(parts)


CSS = '''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:28px}body{margin:0;background:#f5f5f0;color:#202a25;font:16px/1.8 system-ui,-apple-system,'Microsoft YaHei',sans-serif}a{color:#315b45;text-underline-offset:4px}header{padding:27px 5vw;border-bottom:1px solid #d9dfd5;display:flex;justify-content:space-between;align-items:center}.brand{font-size:27px;font-weight:650;letter-spacing:5px}.kicker,.meta{font-size:12px;color:#69746a}.layout{max-width:1360px;margin:0 auto;display:grid;grid-template-columns:184px minmax(0,1fr);gap:44px;padding:36px 4vw 70px}aside{position:sticky;top:28px;align-self:start}aside a{display:block;padding:10px 0;border-bottom:1px solid #dce1d7;font-size:14px;text-decoration:none}main{min-width:0}h1{font-size:35px;line-height:1.35;letter-spacing:-1px;margin:4px 0 15px}h2{font-size:27px;line-height:1.5;margin:0 0 18px}h3{font-size:19px;margin:25px 0 12px}p{margin:10px 0 17px}.lead{font-size:18px;color:#566057}.section{padding:35px 0;border-top:1px solid #d4dbd0;scroll-margin-top:25px}.section:first-child{border-top:0;padding-top:0}.section-no{font-size:12px;letter-spacing:2px;color:#68755f;margin-bottom:4px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}.stat{padding:18px;background:#fff;border:1px solid #d9e0d4}.stat b{display:block;font-size:31px;line-height:1.4}.stat span{font-size:13px;color:#63705f}.notice{border-left:3px solid #7c905a;background:#edf1e6;padding:14px 18px;font-size:14px;margin:20px 0}.table-wrap{overflow:auto;background:#fff;border:1px solid #d8dfd3;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;border-bottom:1px solid #e1e6dc;padding:11px 13px;vertical-align:top}th{background:#eef1e9;font-weight:600}tr:last-child td{border-bottom:0}.log-table{min-width:810px}.flow{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:20px 0}.flow span{padding:10px 13px;background:#fff;border:1px solid #cbd6c3}.badge{font-size:12px;white-space:nowrap;padding:3px 9px;border-radius:12px}.pass{color:#315b39;background:#e5efde}.edit{color:#805a1e;background:#f5ead4}.case{background:#fff;border:1px solid #d4ddce;margin:10px 0}.case summary{cursor:pointer;display:flex;align-items:center;gap:13px;padding:16px 18px;list-style:none}.case summary:before{content:'+';color:#657d50;font-size:20px}.case[open] summary:before{content:'−'}.case-id{font-size:13px;font-weight:700;min-width:72px}.case-topic{flex:1;font-size:14px}.case-body{padding:4px 22px 20px;border-top:1px solid #e5e9df}.inputs{display:grid;grid-template-columns:88px minmax(0,1fr);gap:9px 12px;font-size:14px;padding:16px 0;color:#4e594e}.inputs dt{font-weight:600}.inputs dd{margin:0;overflow-wrap:anywhere}.message{background:#f5f7f1;border-left:3px solid #bacba9;padding:11px 16px;margin:12px 0}.message-label{font-size:12px;color:#5f7152}.message p{margin:4px 0;font-size:17px;white-space:pre-wrap;overflow-wrap:anywhere}.advisor-note{font-size:13px;color:#5c6956}.issue{background:#faf1dd;padding:10px 14px;font-size:13px}.filters{background:#edf1e7;padding:17px;display:flex;flex-wrap:wrap;gap:10px;position:sticky;top:0;z-index:2;margin:20px 0}input,select,button{font:inherit;font-size:14px;border:1px solid #bfcdb5;background:#fff;padding:8px 11px;color:#283426}input{flex:1;min-width:180px}button{cursor:pointer}button:hover{background:#e7efd9}.example{margin:22px 0}.bar{height:12px;display:flex;margin:18px 0;background:#eee}.bar .ok{background:#7e9f65}.bar .warn{background:#d7b96f}.comparison{background:#fff;border:1px solid #d4ddce;padding:20px;margin:16px 0}.compare-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.compare-col{padding:14px;background:#f4f5f0}.compare-col.after{background:#edf3e5}.compare-col p{font-size:16px;margin:8px 0}.compare-label{font-size:12px;color:#5f6d58}.matrix{min-width:1800px}.matrix td{min-width:150px}.matrix td:first-child{min-width:80px}.raw-table summary{cursor:pointer;font-size:14px;color:#586c48;margin-top:22px}.empty{padding:20px;display:none}.evidence-img{max-width:100%;border:1px solid #d5decf}.figure-note{font-size:12px;color:#6b7565}.repo{font:14px/1.8 ui-monospace,monospace;background:#fff;border:1px solid #d8dfd3;padding:16px;white-space:pre-wrap}.muted{color:#687260;font-size:13px}[hidden]{display:none!important}@media(max-width:900px){.layout{grid-template-columns:1fr;gap:22px}aside{position:static;display:flex;gap:13px;flex-wrap:wrap}aside a{border:0;padding:0}.stats{grid-template-columns:1fr 1fr}h1{font-size:28px}.compare-grid{grid-template-columns:1fr}}@media(max-width:520px){header{padding:18px}.layout{padding:24px 18px}.case summary{padding:13px 10px;gap:8px}.case-topic{font-size:12px}.case-id{min-width:58px}.case-body{padding:4px 13px 15px}.inputs{grid-template-columns:70px 1fr}.stats{gap:8px}.stat{padding:13px}}@media print{body{background:#fff}aside,.filters,header,button{display:none}.layout{display:block;padding:0}.section{break-before:page}details.case{break-inside:avoid}.case-body{display:block}.stats{grid-template-columns:repeat(4,1fr)}}'''


def build_html(results,evidence):
    counts,scenario_rows,quality_rows,issue_rows,comparisons=build_sections(results,evidence)
    parts=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VÉRAN｜项目报告 A–E</title><style>'+CSS+'</style></head><body>',
        '<header><div class="brand">VÉRAN</div><span class="kicker">CLIENT ADVISOR TOOL · CASE REPORT</span></header><div class="layout"><aside><a href="#overview">项目背景与结果</a><a href="#work-log">A · 工作日志</a><a href="#method">B · 方法说明</a><a href="#cases">C · 50 个案例</a><a href="#evaluation">D · 评估结果</a><a href="#defects">E · 缺陷与改进</a><a href="#architecture">架构与运行</a></aside><main>',
        '<section class="section" id="overview"><p class="section-no">PROJECT BACKGROUND</p><h1>中文微信话术生成工具</h1><p class="lead">输入客户与场景信息，生成三条可供顾问选择的消息。</p><p>VÉRAN 是虚构的先锋设计师时装品牌，面向男女客户，覆盖成衣、鞋履、包袋和配饰，主要价格定位为人民币 3,000–8,000 元。工具支持六种客户沟通场景，强调亲切、简洁和事实边界。</p>',
        f'<div class="stats"><div class="stat"><b>50</b><span>虚构测试案例</span></div><div class="stat"><b>150</b><span>模型实际生成话术</span></div><div class="stat"><b>{counts["Pass"]}</b><span>组通过辅助评估</span></div><div class="stat"><b>{counts["Needs edit"]}</b><span>组仍需修改</span></div></div>',
        '<p class="muted">提示词 v2.1 · gpt-6.1-terra · Codex 辅助审阅，非独立顾问验证。本文直接包含全部结果；案例卡片可展开，无需阅读 JSON。</p><h3>文件结构 · Repository</h3><div class="repo">README.md　GitHub 直接阅读的 A–E 结果<br>打开报告.html　当前完整离线报告<br>启动工具.cmd　输入新案例并生成话术<br>submission/　提交依据与原始记录<br>code/　生成工具、测试与构建代码</div></section>',
        '<section class="section" id="work-log"><p class="section-no">A · WORK LOG</p><h2>工作日志</h2><p>按实际顺序记录：先跑最小版本，再引入详细场景规则，通过开发案例调整表达，最后生成和审阅 50 例。</p>',
        htable(['Step','做了什么','Input','Output','工具','截图'],[(i,*row) for i,row in enumerate(STEPS,1)],'log-table'),
        '<div class="notice">证据说明：原始输入、提示词、输出及版本已保存。历史 AI 对话截图、生成与评估截图尚未补齐，原始日志不作为截图替代品。</div></section>',
        '<section class="section" id="method"><p class="section-no">B · METHODOLOGY</p><h2>方法说明</h2><h3>品牌与沟通原则</h3><p>品牌设计可以前卫，顾问表达应自然、有分寸。只用本次已知事实；客户最新表态优先。未知信息可省略或核实，不编造产品、库存、优惠或服务。明确拒绝联系时停止营销草稿。</p><h3>生成流程</h3><div class="flow"><span>客户与场景输入</span>→<span>统一规则＋对应场景</span>→<span>模型生成</span>→<span>格式检查</span>→<span>三条候选＋顾问备注</span></div><p>工具只起草，不自动发送。格式检查只能确认结构与数量，不能替代事实和语言审阅。</p><h3>测试设计</h3><p>六个场景共 50 例，覆盖普通需求、信息缺失、偏好变化、售后不满、活动安排及价格问题。先用六例发现问题，集中修订为 v2.1，再用该版本运行全部 50 例。因此，最终数据不属于完全独立的留出测试集。</p>',
        htable(['场景','例数','话术数'],[(r[0],r[1],r[2]) for r in scenario_rows]),
        '<h3>好结果与不可接受结果</h3><p><b>好结果：</b>事实准确、回应当前问题、中文亲切简短，三条候选有选择价值。<b>不可接受：</b>编造重要事实或承诺、违反明确联系限制、给出错误护理建议、答非所问，或缺少要求的候选。</p><p>每例只做四项通过／问题检查。四项均通过记“通过”；表达或重复问题记“需修改”；事实、边界或任务错误记“不通过”。问题用一句话记录。</p></section>',
        '<section class="section" id="cases"><p class="section-no">C · 50 TEST CASES</p><h2>50 个案例与原始话术</h2><p>先看一个完整例子，再按场景、编号或产品查找全部结果。点击案例可展开输入和三条候选；所有候选保持模型原文。</p><h3>代表案例 · 产品推荐</h3><div class="example">',
    ]
    example=next(r for r in results if r['input']['case_id']=='PILOT-001')
    parts.append(case_html(example).replace('class="case"','class="case example-case" open',1))
    parts.append('</div><h3>全部案例</h3><div class="filters"><select id="scenario-filter" aria-label="按场景筛选"><option value="">全部场景 · 50 例</option>' + ''.join(f'<option value="{k}">{esc(v)}</option>' for k,v in SCENARIOS.items()) + '</select><input id="case-search" aria-label="搜索案例" placeholder="搜索编号、客户原话或产品"><button id="expand">全部展开</button><button id="collapse">全部收起</button></div><p id="case-count" class="muted">显示 50 / 50 例</p><div id="case-list">')
    parts.extend(case_html(r) for r in results)
    parts.append('</div><p id="empty" class="empty">没有符合条件的案例。</p>')
    table_rows=[]
    for r in results:
        case=r['input']; values=dict(inputs(case))
        table_rows.append((case['case_id'],SCENARIOS[r['scenario']],values['客户信息'],values['最近聊天'],values['产品信息'],values['场景补充'],*r['output']['messages']))
    parts.append('<details class="raw-table"><summary>按题目规定列查看完整 50 行表格</summary>'+htable(['Case ID','Scenario','Client information','Conversation history','Product information','Additional context','Output 1','Output 2','Output 3'],table_rows,'matrix')+'</details></section>')
    parts.extend(['<section class="section" id="evaluation"><p class="section-no">D · EVALUATION</p><h2>评估结果</h2>',
        f'<p><b>{counts["Pass"]} 组通过，{counts["Needs edit"]} 组需修改，{counts["Fail"]} 组不通过。</b>所有 50 次最终请求都生成了三条中文候选。下列结果按“每例的三条候选”统计，不是单条消息通过率。</p><div class="bar" aria-label="40组通过，10组需修改"><span class="ok" style="width:80%"></span><span class="warn" style="width:20%"></span></div>',
        htable(['场景','案例','话术','通过','需修改','不通过'],scenario_rows),
        '<h3>四项检查</h3>'+htable(['检查项','通过组数','有问题组数'],quality_rows),
        '<p class="muted">同一例可有多项问题。审阅者为 Codex 辅助审阅，未开展独立顾问验证或真实客户效果实验。</p><h3>需要修改的 10 例</h3>',
        htable(['Case ID','场景','具体问题'],issue_rows),
        '<p>主要问题是活动邀请偏长、模板感和候选重复。I05 将“虚构的”数据标签写入了客户消息，应优先修正。</p>',
    ])
    for image_name,caption in (('generation.png','生成结果截图'),('evaluation.png','评估结果截图')):
        file=SUBMISSION/image_name
        if file.exists():
            data=base64.b64encode(file.read_bytes()).decode('ascii')
            parts.append(f'<figure><img class="evidence-img" src="data:image/png;base64,{data}" alt="{caption}"><figcaption class="figure-note">{caption}</figcaption></figure>')
    parts.append('<p class="muted">生成与评估截图待补；当前保留逐例原始结果和辅助评估记录。</p></section><section class="section" id="defects"><p class="section-no">E · DEFECTS AND NEXT STEPS</p><h2>缺陷与改进</h2><p>v2.0 的开发运行暴露了长句、正式问候和重复表达。v2.1 增加短句与日常表达要求，并禁止编造顾问“最近整理”“专门挑选”等动作。以下对比来自同案例、同候选编号的真实记录，不证明整体因果改进。</p>')
    for case_id,index,before,after,change in comparisons:
        parts.append(f'<div class="comparison"><h3>{case_id} · 候选 {index}</h3><div class="compare-grid"><div class="compare-col"><span class="compare-label">修改前 · v2.0</span><p>{esc(before)}</p></div><div class="compare-col after"><span class="compare-label">修改后 · v2.1</span><p>{esc(after)}</p></div></div><p class="muted">{esc(change)}</p></div>')
    parts.append('<h3>仍需改进</h3><p>优先处理 I05 的数据标签外露、活动邀请长句和重复候选。修订后对同一输入复跑并保留版本；当前 150 条输出保持原样。后续补做明确拒绝联系及聊天内嵌指令的边界测试，并邀请实际顾问审阅。AI 对话与生成／评估截图也需补齐。</p></section><section class="section" id="architecture"><p class="section-no">ARCHITECTURE & USAGE</p><h2>架构与运行</h2><div class="flow"><span>输入表单</span>→<span>品牌与场景规则</span>→<span>Codex CLI／模型</span>→<span>格式检查</span>→<span>三条候选＋备注</span>→<span>顾问审核</span></div><p>阅读报告：直接打开本文件。测试新案例：双击项目最外层的<b>启动工具.cmd</b>，在浏览器填写案例后生成。新生成需要本机 Python 3.10+、已登录的 Codex CLI 和网络；现有结果可离线查看。消息不会自动发送。</p><p class="muted">原始本机日志和题目 PDF 未上传。报告可从保存的结果重建，不需要再次调用模型。</p></section></main></div>')
    parts.append('''<script>
const cards=[...document.querySelectorAll('#case-list > .case')];
const filter=document.getElementById('scenario-filter'),search=document.getElementById('case-search');
function update(){const scenario=filter.value,query=search.value.trim().toLowerCase();let count=0;for(const card of cards){const show=(!scenario||card.dataset.scenario===scenario)&&(!query||card.dataset.search.includes(query));card.hidden=!show;if(show)count++;}document.getElementById('case-count').textContent=`显示 ${count} / ${cards.length} 例`;document.getElementById('empty').style.display=count?'none':'block';}
filter.addEventListener('change',update);search.addEventListener('input',update);
document.getElementById('expand').onclick=()=>cards.filter(card=>!card.hidden).forEach(card=>card.open=true);
document.getElementById('collapse').onclick=()=>cards.forEach(card=>card.open=false);
window.addEventListener('beforeprint',()=>cards.forEach(card=>card.open=true));
</script></body></html>''')
    return '\n'.join(parts)


def main():
    results,evidence,review=load_results()
    # The original machine-readable record stays available for audit, not as the reading interface.
    public=[{key:row[key] for key in ('input','output','prompt_version','run_id')} for row in results]
    (SUBMISSION/'cases.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
    (PROJECT_ROOT/'README.md').write_text(build_markdown(results,evidence),encoding='utf-8')
    report_path=PROJECT_ROOT/'打开报告.html'
    report_path.write_text(build_html(results,evidence),encoding='utf-8')
    print(json.dumps({'cases':len(results),'messages':sum(len(r['output']['messages']) for r in results),'labels':dict(Counter(r['review']['label'] for r in results)),'readme':'README.md','html':report_path.name},ensure_ascii=True))


if __name__=='__main__':
    main()

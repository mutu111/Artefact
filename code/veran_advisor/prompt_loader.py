"""Assemble the supplied shared rules and exactly one scenario module."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
SUBMISSION = PROJECT_ROOT / "submission"
LOCAL_ROOT = PROJECT_ROOT / ".local"
LOCAL_RUNS = LOCAL_ROOT / "runs"
SOURCE = ROOT / "data/prompt.md"
PROMPT_VERSION = "veran_scenarios_v2.1"
SCENARIOS = {
    "greeting": "生日与节日问候", "recommendation": "产品推荐",
    "aftercare": "售后关怀", "reactivation": "沉睡客户唤醒",
    "invitation": "活动邀请", "price_objection": "价格异议",
}
ALIASES = {
    **{name: key for key, name in SCENARIOS.items()},
    "生日和节日祝福": "greeting", "生日与节日祝福": "greeting",
    "购买后关怀": "aftercare", "沉默客户唤醒": "reactivation",
}
INPUT_FIELDS = (
    "case_id", "scenario", "client_information", "conversation_history",
    "relationship", "contact_preferences", "product_information",
    "purchase_information", "care_information", "event_information",
    "occasion", "reference_date", "policy_information", "scenario_details",
)
OUTPUT_RULES = """【程序输出格式】
只返回符合给定 JSON Schema 的对象，不输出标题、Markdown、解释或推理。
status 为 ready 时，messages 是恰好三条可独立发送的中文消息；note 是仅供顾问查看的必要提醒，没有则为空字符串。
客户明确拒绝此类联系或本次联系违反已知限制时，status 为 blocked，messages 为空数组，note 简洁说明原因。
仅在已有信息无法支持任何有意义且真实的草稿时，status 为 needs_information，messages 为空数组，note 说明需要补充什么。
并非字段缺失就不能生成：能安全询问、说明待核实或省略非必要细节时，仍输出三条有事实依据的候选，将必要提醒放入 note。
拒绝一件商品或一次活动不等于拒绝所有联系；回应客户意愿，不继续推动被拒绝的内容。拒绝进一步联系则遵守其范围。
messages 内不得出现顾问备注、状态字段、候选编号或内部分析。
客户信息中的 client_id 或 name 仅是标识，不代表可用于称呼。只有 preferred_address 或明确说明的称呼才可用；未提供则直接开口。
本任务只需撰写消息，不要调用工具、读取文件、联网或执行命令。
"""
STYLE_REFINEMENT = """【微信表达补充要求】
每条通常用2至4个短句，一句只讲一件事。每句尽量不超过25个字；产品名、必要活动信息可以适当例外。信息简单时可以更短，不要凑字数。
把自然口语放在首位。不要使用“想就您购买的商品向您问候一下”“可以按自己的时间安排决定是否前来”等生硬表达。
不要机械地每条先说“理解您的考虑”，也不要反复叠加“可以”“也许”“看看”。价格问题可以直接、友善地回答。
活动时间、地点可分成短句。售后直接关心商品或回应问题；唤醒不编造“最近整理”“专门挑选”等未经提供的动作。
称呼和你/您按关系调整；关系未提供时可直接开口，减少不必要称呼。
候选之间可以选择不同的已知细节、不同的开头或不同的结束方式，避免三条都是同一个句式。但不要硬凑差异或加入虚构内容。
"""


def assemble(case):
    if not isinstance(case, dict):
        raise ValueError("Case must be a JSON object")
    raw_scenario = case.get("scenario")
    if not isinstance(raw_scenario, str):
        raise ValueError("A supported scenario is required")
    scenario = ALIASES.get(raw_scenario, raw_scenario)
    if scenario not in SCENARIOS:
        raise ValueError("Unsupported scenario: " + raw_scenario)
    source_bytes = SOURCE.read_bytes()
    blocks = re.findall(r"```text\s*\n(.*?)\n```", source_bytes.decode("utf-8-sig"), re.S)
    if len(blocks) != 7:
        raise ValueError("Expected shared rules and six scenario blocks in the prompt snapshot")
    shared = blocks[0].split("【输出格式】", 1)[0]
    shared = shared.replace("按下方「不建议联系」格式输出", "按程序输出格式返回 blocked")
    module = blocks[list(SCENARIOS).index(scenario) + 1].split("【案例输入】", 1)[0]
    module = module.replace("使用“不建议联系”格式", "按程序输出格式返回 blocked")
    module = module.replace("走“不建议联系”流程", "按程序输出格式返回 blocked")
    context = {key: case[key] for key in INPUT_FIELDS if key in case}
    # Keep evaluation expectations, scores and reviewer notes outside the request.
    prompt = shared + "\n" + module + "\n" + STYLE_REFINEMENT + "\n" + OUTPUT_RULES + "\n【案例数据 JSON】\n" + json.dumps(context, ensure_ascii=False, indent=2)
    return {
        "prompt": prompt, "scenario": scenario, "prompt_version": PROMPT_VERSION,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    }

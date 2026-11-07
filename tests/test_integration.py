"""Regression checks for prompt routing, evaluation leakage and output validation."""
import unittest
from veran_advisor.generate import validate_output
from veran_advisor.prompt_loader import SCENARIOS, assemble


class PromptIntegrationTests(unittest.TestCase):
    def test_selects_only_requested_scenario_and_no_templates(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                prompt = assemble({"scenario": scenario})["prompt"]
                self.assertEqual(prompt.count("【本次场景】"), 1)
                self.assertNotIn("【案例输入】", prompt)
                self.assertNotIn("候选 1：<", prompt)
                self.assertIn("【程序输出格式】", prompt)

    def test_evaluator_metadata_does_not_reach_generator(self):
        prompt = assemble({"scenario": "产品推荐", "expected_behavior": "SECRET_EXPECTATION", "score": "SECRET_SCORE", "reviewer_notes": "SECRET_REVIEW"})["prompt"]
        for secret in ("SECRET_EXPECTATION", "SECRET_SCORE", "SECRET_REVIEW"):
            self.assertNotIn(secret, prompt)

    def test_new_case_facts_and_preferences_are_preserved(self):
        case = {"scenario": "invitation", "contact_preferences": "仅微信联系", "event_information": {"place": "虚构展厅"}, "client_information": {"client_id": "TEST", "preferred_address": "林女士"}}
        prompt = assemble(case)["prompt"]
        for fact in ("仅微信联系", "虚构展厅", "林女士"):
            self.assertIn(fact, prompt)

    def test_unknown_scenario_rejected(self):
        with self.assertRaises(ValueError):
            assemble({"scenario": "unsupported"})

    def test_ready_requires_three_chinese_messages(self):
        validate_output({"status": "ready", "note": "", "messages": ["你好。", "欢迎。", "谢谢。"]})
        for messages in (["你好。"], ["hello", "hi", "hey"], ["你好。", "欢迎。", ""]):
            with self.assertRaises(ValueError):
                validate_output({"status": "ready", "note": "", "messages": messages})

    def test_no_send_response_requires_reason_and_no_messages(self):
        validate_output({"status": "blocked", "note": "客户拒绝联系", "messages": []})
        for output in ({"status": "blocked", "note": "", "messages": []}, {"status": "blocked", "note": "客户拒绝联系", "messages": ["你好。"]}):
            with self.assertRaises(ValueError):
                validate_output(output)


if __name__ == "__main__":
    unittest.main()

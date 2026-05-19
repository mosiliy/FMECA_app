import unittest

from model import FMEAModel


class TestExplainRisk(unittest.TestCase):
    def test_explain_risk_contains_key_sections(self):
        failure = {
            "component": "CPU",
            "failure_mode": "Overheat",
            "severity": 8,
            "occurrence": 4,
            "detection": 3,
            "mil_criticality": 0.004,
            "local_effect": "Thermal throttling",
            "next_higher_effect": "Subsystem slowdown",
            "end_effect": "Mission degradation",
            "recommended_actions": "Replace fan",
            "action_owner": "Reliability engineer",
            "due_date": "2026-06-01",
        }
        text = FMEAModel.explain_risk(failure)
        self.assertIn("RPN:", text)
        self.assertIn("Критичность Cm:", text)
        self.assertIn("Влияние на систему:", text)
        self.assertIn("Рекомендации:", text)


if __name__ == "__main__":
    unittest.main()

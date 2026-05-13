import unittest

from model import FMEAModel


class TestIteration3QualityAndReporting(unittest.TestCase):
    def test_calculate_analysis_completeness_full_set_is_100(self):
        failure = {
            "function_text": "Power conversion",
            "failure_mode": "Voltage drift",
            "failure_cause": "Aging capacitors",
            "local_effect": "Ripple increase",
            "next_higher_effect": "Subsystem instability",
            "end_effect": "Mission degradation",
            "recommended_actions": "Replace capacitors",
            "severity": 8,
            "occurrence": 4,
            "detection": 3,
            "mil_criticality": 0.004,
        }
        self.assertEqual(FMEAModel.calculate_analysis_completeness(failure), 100.0)

    def test_calculate_analysis_completeness_partial_set_percentage(self):
        failure = {
            "function_text": "Power conversion",
            "failure_mode": "Voltage drift",
            "failure_cause": "",
            "local_effect": "",
            "next_higher_effect": "Subsystem instability",
            "end_effect": "Mission degradation",
            "recommended_actions": "",
            "severity": 8,
            "occurrence": 4,
            "detection": 3,
        }
        # Из 10 обязательных полей заполнено 7 -> 70%
        self.assertEqual(FMEAModel.calculate_analysis_completeness(failure), 70.0)

    def test_get_missing_fields_returns_expected_list(self):
        failure = {
            "function_text": "Power conversion",
            "failure_mode": "Voltage drift",
            "failure_cause": "",
            "local_effect": None,
            "next_higher_effect": "Subsystem instability",
            "end_effect": "Mission degradation",
            "recommended_actions": "Replace capacitors",
            "severity": 8,
            "occurrence": 4,
            "detection": 3,
            "mil_criticality": None,
        }
        missing = FMEAModel.get_missing_fields(failure)
        self.assertIn("failure_cause", missing)
        self.assertIn("local_effect", missing)
        self.assertIn("mil_criticality", missing)

    def test_calculate_analysis_completeness_without_mil_field(self):
        failure = {
            "function_text": "Power conversion",
            "failure_mode": "Voltage drift",
            "failure_cause": "Aging capacitors",
            "local_effect": "Ripple increase",
            "next_higher_effect": "Subsystem instability",
            "end_effect": "Mission degradation",
            "recommended_actions": "Replace capacitors",
            "severity": 8,
            "occurrence": 4,
            "detection": 3,
        }
        self.assertEqual(FMEAModel.calculate_analysis_completeness(failure), 100.0)

    def test_calculate_analysis_completeness_with_mil_field(self):
        failure = {
            "function_text": "Power conversion",
            "failure_mode": "Voltage drift",
            "failure_cause": "Aging capacitors",
            "local_effect": "Ripple increase",
            "next_higher_effect": "Subsystem instability",
            "end_effect": "Mission degradation",
            "recommended_actions": "Replace capacitors",
            "severity": 8,
            "occurrence": 4,
            "detection": 3,
            "mil_criticality": None,
        }
        # 10 из 11 полей заполнены
        self.assertAlmostEqual(FMEAModel.calculate_analysis_completeness(failure), 90.91, places=2)

    def test_calculate_residual_risk_from_stored_values(self):
        failure = {
            "rpn": 120,
            "residual_rpn": 60,
        }
        risk = FMEAModel.calculate_residual_risk(failure)
        self.assertEqual(risk["initial_rpn"], 120)
        self.assertEqual(risk["residual_rpn"], 60)
        self.assertEqual(risk["risk_reduction"], 60)

    def test_calculate_residual_risk_with_fallback_calculation(self):
        failure = {
            "severity": 8,
            "occurrence": 5,
            "detection": 3,
            "residual_severity": 6,
            "residual_occurrence": 3,
            "residual_detection": 3,
        }
        risk = FMEAModel.calculate_residual_risk(failure)
        self.assertEqual(risk["initial_rpn"], 120)
        self.assertEqual(risk["residual_rpn"], 54)
        self.assertEqual(risk["risk_reduction"], 66)
    
    def test_calculate_residual_risk_uses_explicit_residual_rpn_when_present(self):
        failure = {
            "severity": 8,
            "occurrence": 5,
            "detection": 3,
            "residual_rpn": 40,
            "residual_severity": 6,
            "residual_occurrence": 3,
            "residual_detection": 3,
        }
        risk = FMEAModel.calculate_residual_risk(failure)
        self.assertEqual(risk["initial_rpn"], 120)
        self.assertEqual(risk["residual_rpn"], 40)
        self.assertEqual(risk["risk_reduction"], 80)


if __name__ == "__main__":
    unittest.main()

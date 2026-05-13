import os
import tempfile
import unittest

from database import Database
from model import FMEAModel


class TestQualityDashboardBackend(unittest.TestCase):
    def test_build_quality_dashboard_summary_and_problematic_records(self):
        failures = [
            {
                "id": 1,
                "component": "CPU",
                "function_text": "Compute",
                "failure_mode": "Overheat",
                "failure_cause": "Fan fail",
                "local_effect": "Throttle",
                "next_higher_effect": "Subsystem slowdown",
                "end_effect": "Mission impact",
                "recommended_actions": "Replace fan",
                "severity": 8,
                "occurrence": 4,
                "detection": 3,
                "mil_criticality": 0.004,
            },
            {
                "id": 2,
                "component": "RAM",
                "function_text": "Store",
                "failure_mode": "Bit flip",
                "failure_cause": "",
                "local_effect": "",
                "next_higher_effect": "Data errors",
                "end_effect": "System instability",
                "recommended_actions": "",
                "severity": 7,
                "occurrence": 3,
                "detection": 4,
                "mil_criticality": None,
            },
        ]

        dashboard = FMEAModel.build_quality_dashboard(
            failures,
            top_n=5,
            low_completeness_threshold=80.0,
        )

        summary = dashboard["summary"]
        self.assertEqual(summary["total_records"], 2)
        self.assertAlmostEqual(summary["average_analysis_completeness_score"], 81.82, places=2)
        self.assertEqual(summary["fully_completed_count"], 1)
        self.assertEqual(summary["fully_completed_percent"], 50.0)

        problematic = dashboard["problematic_records"]
        self.assertEqual(len(problematic), 1)
        self.assertEqual(problematic[0]["id"], 2)
        self.assertLess(problematic[0]["analysis_completeness_score"], 80.0)
        self.assertIn("failure_cause", problematic[0]["missing_fields"])

    def test_database_quality_dashboard_data_source(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db = Database(os.path.join(tmp_dir, "quality.db"))
            component_id = db.add_component("SYS", "SUB", "CPU")

            db.add_failure(
                component_id=component_id,
                failure_mode="Overheat",
                failure_cause="Fan fail",
                failure_effect="Shutdown",
                severity=8,
                occurrence=4,
                detection=3,
                function_text="Compute",
                local_effect="Throttle",
                next_higher_effect="Subsystem slowdown",
                end_effect="Mission impact",
                recommended_actions="Replace fan",
                failure_rate_lambda=1e-5,
                mode_ratio_alpha=0.5,
                conditional_prob_beta=0.8,
                mission_time_t=1000,
            )

            records = db.get_failures_for_quality_dashboard()
            db.close()

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["component"], "CPU")
            self.assertEqual(records[0]["failure_mode"], "Overheat")
            self.assertIn("mil_criticality", records[0])


if __name__ == "__main__":
    unittest.main()

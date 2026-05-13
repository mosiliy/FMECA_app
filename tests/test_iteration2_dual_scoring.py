import os
import tempfile
import unittest

from database import Database
from model import FMEAModel


class TestIteration2DualScoring(unittest.TestCase):
    def test_dual_scoring_keeps_rpn_and_calculates_mil_when_data_present(self):
        result = FMEAModel.calculate_dual_scores(
            severity=8,
            occurrence=4,
            detection=3,
            lambda_p=1e-5,
            alpha=0.5,
            beta=0.8,
            mission_time_t=1000,
        )
        self.assertEqual(result["rpn"], 96)  # как раньше
        self.assertAlmostEqual(result["mil_criticality"], 0.004)

    def test_dual_scoring_returns_none_mil_when_data_missing(self):
        result = FMEAModel.calculate_dual_scores(
            severity=8,
            occurrence=4,
            detection=3,
            lambda_p=None,
            alpha=0.5,
            beta=0.8,
            mission_time_t=1000,
        )
        self.assertEqual(result["rpn"], 96)
        self.assertIsNone(result["mil_criticality"])

    def test_validate_action_requirements(self):
        ok, error = FMEAModel.validate_action_requirements(
            recommended_actions="Replace capacitor",
            action_owner="Reliability engineer",
            due_date="2026-06-01",
        )
        self.assertTrue(ok)
        self.assertIsNone(error)

        ok, error = FMEAModel.validate_action_requirements(
            recommended_actions="Replace capacitor",
            action_owner="",
            due_date="2026-06-01",
        )
        self.assertFalse(ok)
        self.assertIsNotNone(error)
        
        ok, error = FMEAModel.validate_action_requirements(
            recommended_actions="Replace capacitor",
            action_owner="Reliability engineer",
            due_date="",
        )
        self.assertFalse(ok)
        self.assertIsNotNone(error)

    def test_end_effect_recommendation(self):
        msg = FMEAModel.get_effect_completion_recommendation(
            end_effect="Mission loss",
            local_effect="",
        )
        self.assertIsNotNone(msg)

    def test_add_failure_calculates_mil_criticality(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "iteration2.db")
            db = Database(db_path)
            component_id = db.add_component("SYS", "SUB", "CPU")

            failure_id = db.add_failure(
                component_id=component_id,
                failure_mode="Overheat",
                failure_cause="Fan failure",
                failure_effect="Shutdown",
                severity=8,
                occurrence=4,
                detection=3,
                failure_rate_lambda=1e-5,
                mode_ratio_alpha=0.5,
                conditional_prob_beta=0.8,
                mission_time_t=1000,
            )
            self.assertIsInstance(failure_id, int)

            db.cursor.execute("SELECT rpn, mil_criticality FROM failures WHERE id = ?", (failure_id,))
            rpn, mil_criticality = db.cursor.fetchone()
            db.close()

            self.assertEqual(rpn, 96)  # старый RPN не изменён
            self.assertAlmostEqual(mil_criticality, 0.004)
    
    def test_integration_add_failure_saves_mil_inputs_and_result(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "iteration2_integration.db")
            db = Database(db_path)
            component_id = db.add_component("SYS", "SUB", "PSU")

            failure_id = db.add_failure(
                component_id=component_id,
                failure_mode="Voltage spikes",
                failure_cause="Capacitor aging",
                failure_effect="Unstable output",
                severity=9,
                occurrence=3,
                detection=4,
                failure_rate_lambda=2e-5,
                mode_ratio_alpha=0.25,
                conditional_prob_beta=0.5,
                mission_time_t=2000,
            )

            db.cursor.execute(
                """
                SELECT rpn, failure_rate_lambda, mode_ratio_alpha,
                       conditional_prob_beta, mission_time_t, mil_criticality
                FROM failures
                WHERE id = ?
                """,
                (failure_id,),
            )
            row = db.cursor.fetchone()
            db.close()

            self.assertEqual(row[0], 108)  # 9*3*4
            self.assertAlmostEqual(row[1], 2e-5)
            self.assertAlmostEqual(row[2], 0.25)
            self.assertAlmostEqual(row[3], 0.5)
            self.assertAlmostEqual(row[4], 2000.0)
            self.assertAlmostEqual(row[5], 0.005)

    def test_add_failure_stores_none_mil_for_legacy_like_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "iteration2_legacy.db")
            db = Database(db_path)
            component_id = db.add_component("SYS", "SUB", "SSD")

            failure_id = db.add_failure(
                component_id=component_id,
                failure_mode="Read error",
                failure_cause="Cell wear",
                failure_effect="Data corruption",
                severity=7,
                occurrence=5,
                detection=4,
            )
            db.cursor.execute("SELECT mil_criticality FROM failures WHERE id = ?", (failure_id,))
            (mil_criticality,) = db.cursor.fetchone()
            db.close()

            self.assertIsNone(mil_criticality)

    def test_component_mil_criticality_aggregation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "iteration2_aggregation.db")
            db = Database(db_path)
            comp_a = db.add_component("SYS", "SUB", "CPU")
            comp_b = db.add_component("SYS", "SUB", "RAM")

            db.add_failure(comp_a, "Overheat", "Fan", "Stop", 8, 4, 3,
                           failure_rate_lambda=1e-5, mode_ratio_alpha=0.5,
                           conditional_prob_beta=0.8, mission_time_t=1000)
            db.add_failure(comp_a, "Thermal throttling", "Dust", "Degradation", 6, 4, 3,
                           failure_rate_lambda=2e-5, mode_ratio_alpha=0.4,
                           conditional_prob_beta=0.5, mission_time_t=1000)
            db.add_failure(comp_b, "Bit flip", "Noise", "Error", 5, 3, 4)

            summary = db.get_component_mil_criticality_summary()
            db.close()

            self.assertGreaterEqual(len(summary), 2)
            summary_map = {row[0]: row[1] for row in summary}
            self.assertAlmostEqual(summary_map["CPU"], 0.008, places=7)
            self.assertAlmostEqual(summary_map["RAM"], 0.0, places=7)


if __name__ == "__main__":
    unittest.main()

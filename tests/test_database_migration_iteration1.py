import os
import sqlite3
import tempfile
import unittest

from database import Database


class TestDatabaseMigrationIteration1(unittest.TestCase):
    def _create_legacy_database(self, db_path: str) -> None:
        """Создаёт старую схему failures без новых полей."""
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id INTEGER NOT NULL,
                failure_type_id INTEGER,
                cause_id INTEGER,
                effect_id INTEGER,
                failure_mode TEXT NOT NULL,
                failure_cause TEXT NOT NULL,
                failure_effect TEXT NOT NULL,
                severity INTEGER,
                occurrence INTEGER,
                detection INTEGER,
                rpn INTEGER
            )
            """
        )
        conn.commit()
        conn.close()

    def test_legacy_database_opens_and_new_columns_are_added(self):
        expected_new_columns = {
            "function_text",
            "local_effect",
            "next_higher_effect",
            "end_effect",
            "current_controls",
            "recommended_actions",
            "action_owner",
            "due_date",
            "action_status",
            "failure_rate_lambda",
            "mode_ratio_alpha",
            "conditional_prob_beta",
            "mission_time_t",
            "mission_phase",
            "operating_mode",
            "is_single_point",
            "is_latent",
            "is_common_cause",
            "mil_criticality",
            "residual_severity",
            "residual_occurrence",
            "residual_detection",
            "residual_rpn",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "legacy_fmea.db")
            self._create_legacy_database(db_path)

            # Должно открыться без ошибок, миграция выполняется автоматически.
            db = Database(db_path)
            db.close()

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(failures)")
            columns = {row[1] for row in cur.fetchall()}
            conn.close()

            self.assertTrue(
                expected_new_columns.issubset(columns),
                f"Не все новые колонки добавлены. Отсутствуют: {expected_new_columns - columns}",
            )


if __name__ == "__main__":
    unittest.main()

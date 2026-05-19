import unittest

from model import FMEAModel


class TestComprehensiveReporting(unittest.TestCase):
    def _full_row(self):
        return (
            1, "SYS", "SUB", "CPU", "Processor", "Compute",
            "Overheat", "Fan fail", "Throttling", "Subsystem slowdown", "Mission degradation", "Legacy effect",
            8, 4, 3, 96, 0.004,
            1e-6, 0.2, 0.5, 1000.0,
            "Monitoring", "Replace fan", "Engineer", "2026-06-01", "Open",
            "Integration", "Nominal",
            1, 0, 0,
            6, 3, 2, 36,
        )

    def test_comprehensive_dataframe_has_gost_mil_columns(self):
        df = FMEAModel.build_comprehensive_fmeca_dataframe([self._full_row()])
        for col in ["Класс тяжести", "Уровень вероятности", "λ (1/ч)", "ОПФ", "Полнота анализа, %"]:
            self.assertIn(col, df.columns)
        self.assertEqual(df.iloc[0]["Класс тяжести"], "II")
        self.assertEqual(df.iloc[0]["RPN до мер"], 96)
        self.assertEqual(df.iloc[0]["RPN после мер"], 36)

    def test_gost_compliance_summary(self):
        df = FMEAModel.build_comprehensive_fmeca_dataframe([self._full_row()])
        summary = FMEAModel.build_gost_compliance_summary(df)
        self.assertEqual(summary.iloc[0]["Значение"], 1)


if __name__ == "__main__":
    unittest.main()

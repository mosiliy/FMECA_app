import unittest

from model import FMEAModel


class TestStandardizedReporting(unittest.TestCase):
    def test_build_standardized_fmeca_dataframe_contains_before_after_columns(self):
        data = [
            (
                1, "SYS", "SUB", "CPU", "Processor", "Compute",
                "Overheat", "Fan fail", "Throttling", "Subsystem slowdown", "Mission degradation",
                8, 4, 3, 96, 0.004,
                "Replace fan", "Engineer", "2026-06-01", 54
            )
        ]
        df = FMEAModel.build_standardized_fmeca_dataframe(data)
        self.assertIn("Before Actions (RPN)", df.columns)
        self.assertIn("After Actions (Residual RPN)", df.columns)
        self.assertIn("Risk Reduction", df.columns)
        self.assertEqual(df.iloc[0]["Risk Reduction"], 42)

    def test_sort_standardized_fmeca_by_mil(self):
        data = [
            (
                1, "SYS", "SUB", "CPU", "Processor", "Compute",
                "Overheat", "Fan fail", "Throttling", "Subsystem slowdown", "Mission degradation",
                8, 4, 3, 96, 0.004,
                "Replace fan", "Engineer", "2026-06-01", 54
            ),
            (
                2, "SYS", "SUB", "RAM", "Memory", "Store",
                "Bit flip", "Noise", "Data error", "Module instability", "System error",
                7, 3, 4, 84, 0.01,
                "ECC tuning", "Analyst", "2026-07-01", 40
            ),
        ]
        df = FMEAModel.build_standardized_fmeca_dataframe(data)
        sorted_df = FMEAModel.sort_standardized_fmeca(df, sort_by="mil_criticality")
        self.assertEqual(sorted_df.iloc[0]["Component"], "RAM")


if __name__ == "__main__":
    unittest.main()

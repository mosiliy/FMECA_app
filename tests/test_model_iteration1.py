import unittest

from model import FMEAModel


class TestModelIteration1(unittest.TestCase):
    # Regression: старый RPN не меняется
    def test_calculate_rpn_regression(self):
        self.assertEqual(FMEAModel.calculate_rpn(8, 4, 3), 96)
        self.assertEqual(FMEAModel.calculate_rpn(1, 1, 1), 1)
        self.assertEqual(FMEAModel.calculate_rpn(10, 10, 10), 1000)

    # Unit: calc_mil_criticality
    def test_calc_mil_criticality_normal_values(self):
        result = FMEAModel.calc_mil_criticality(1.2e-5, 0.5, 0.8, 1000)
        self.assertAlmostEqual(result, 0.0048)

    def test_calc_mil_criticality_boundary_zeroes(self):
        self.assertEqual(FMEAModel.calc_mil_criticality(0.0, 0.5, 0.8, 1000), 0.0)
        self.assertEqual(FMEAModel.calc_mil_criticality(1.2e-5, 0.0, 0.8, 1000), 0.0)
        self.assertEqual(FMEAModel.calc_mil_criticality(1.2e-5, 0.5, 0.0, 1000), 0.0)
        self.assertEqual(FMEAModel.calc_mil_criticality(1.2e-5, 0.5, 0.8, 0.0), 0.0)

    def test_calc_mil_criticality_returns_none_for_missing_or_invalid(self):
        self.assertIsNone(FMEAModel.calc_mil_criticality(None, 0.5, 0.8, 1000))
        self.assertIsNone(FMEAModel.calc_mil_criticality(1.0, None, 0.8, 1000))
        self.assertIsNone(FMEAModel.calc_mil_criticality(1.0, 0.5, None, 1000))
        self.assertIsNone(FMEAModel.calc_mil_criticality(1.0, 0.5, 0.8, None))
        self.assertIsNone(FMEAModel.calc_mil_criticality("bad", 0.5, 0.8, 1000))

    # Unit: calc_residual_rpn
    def test_calc_residual_rpn_normal_values(self):
        self.assertEqual(FMEAModel.calc_residual_rpn(6, 3, 4), 72)
        self.assertEqual(FMEAModel.calc_residual_rpn(10, 10, 10), 1000)

    def test_calc_residual_rpn_returns_none_for_missing_values(self):
        self.assertIsNone(FMEAModel.calc_residual_rpn(None, 3, 4))
        self.assertIsNone(FMEAModel.calc_residual_rpn(6, None, 4))
        self.assertIsNone(FMEAModel.calc_residual_rpn(6, 3, None))

    def test_calc_residual_rpn_returns_none_for_invalid_values(self):
        # Выход за границы S/O/D: 1..10
        self.assertIsNone(FMEAModel.calc_residual_rpn(0, 3, 4))
        self.assertIsNone(FMEAModel.calc_residual_rpn(11, 3, 4))
        self.assertIsNone(FMEAModel.calc_residual_rpn(6, -1, 4))
        # Невалидные типы
        self.assertIsNone(FMEAModel.calc_residual_rpn("x", 3, 4))

    def test_map_severity_to_mil_std_1629a_category(self):
        self.assertEqual(FMEAModel.map_severity_to_mil_std_1629a_category(10), "I")
        self.assertEqual(FMEAModel.map_severity_to_mil_std_1629a_category(9), "I")
        self.assertEqual(FMEAModel.map_severity_to_mil_std_1629a_category(8), "II")
        self.assertEqual(FMEAModel.map_severity_to_mil_std_1629a_category(6), "III")
        self.assertEqual(FMEAModel.map_severity_to_mil_std_1629a_category(4), "IV")
        self.assertEqual(FMEAModel.map_severity_to_mil_std_1629a_category("bad"), "IV")

    def test_map_occurrence_to_mil_std_1629a_level(self):
        self.assertEqual(FMEAModel.map_occurrence_to_mil_std_1629a_level(10), "A")
        self.assertEqual(FMEAModel.map_occurrence_to_mil_std_1629a_level(8), "B")
        self.assertEqual(FMEAModel.map_occurrence_to_mil_std_1629a_level(5), "C")
        self.assertEqual(FMEAModel.map_occurrence_to_mil_std_1629a_level(3), "D")
        self.assertEqual(FMEAModel.map_occurrence_to_mil_std_1629a_level(1), "E")


if __name__ == "__main__":
    unittest.main()

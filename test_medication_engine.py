import unittest
from app.services.medication_intelligence.engine import MedicationInteractionEngine


class TestMedicationEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = MedicationInteractionEngine()

    def test_known_moderate_interaction(self):
        result = self.engine.check_interactions(["Abacavir", "Cobicistat"])
        self.assertEqual(result["interactions"][0]["severity"], "Moderate")

    def test_known_major_interaction(self):
        result = self.engine.check_interactions(["Iron", "Dolutegravir"])
        self.assertEqual(result["interactions"][0]["severity"], "Major")

    def test_pair_order_independent(self):
        a = self.engine.check_interactions(["Iron", "Dolutegravir"])
        b = self.engine.check_interactions(["Dolutegravir", "Iron"])
        self.assertEqual(a["interactions"][0]["severity"],
                         b["interactions"][0]["severity"])

    def test_all_unique_pairs_checked(self):
        result = self.engine.check_interactions(
            ["Abacavir", "Cobicistat", "Iron", "Dolutegravir"]
        )
        self.assertEqual(result["total_pairs_checked"], 6)

    def test_unmatched_medication(self):
        result = self.engine.check_interactions(
            ["Abacavir", "UnknownTestMedicine"]
        )
        self.assertIn("UnknownTestMedicine", result["unmatched_medications"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

import unittest
from app.services.medication_intelligence.engine import MedicationInteractionEngine
from app.services.medication_intelligence.patient_risk import PatientRiskAssessment


class TestPatientRisk(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine = MedicationInteractionEngine()
        cls.assessor = PatientRiskAssessment(engine)

    def test_interaction_detection(self):
        patient = {
            "date_of_birth": "2000-01-01",
            "allergies": [],
            "medical_history": []
        }
        result = self.assessor.assess(
            ["Iron", "Dolutegravir"], patient
        )
        self.assertEqual(result["interaction_count"], 1)

    def test_allergy_review_flag(self):
        patient = {
            "date_of_birth": "2000-01-01",
            "allergies": ["Penicillin"],
            "medical_history": []
        }
        result = self.assessor.assess(["Abacavir"], patient)
        self.assertTrue(any(
            flag["type"] == "allergy_review_required"
            for flag in result["risk_flags"]
        ))

    def test_missing_information(self):
        result = self.assessor.assess(["Abacavir"], {})
        self.assertIn("date_of_birth", result["missing_information"])
        self.assertIn("allergies", result["missing_information"])
        self.assertIn("medical_history", result["missing_information"])

    def test_unmatched_medication(self):
        result = self.assessor.assess(
            ["UnknownTestMedicine"],
            {"allergies": [], "medical_history": []}
        )
        self.assertIn(
            "UnknownTestMedicine", result["unmatched_medications"]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

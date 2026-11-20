
import unittest

import run


class TestPatientRiskAPI(unittest.TestCase):

    def setUp(self):
        self.client = run.app.test_client()

    def get_csrf_token(self):
        response = self.client.get("/api/auth/csrf")
        return response.get_json()["csrf_token"]

    def test_unauthenticated_access(self):
        token = self.get_csrf_token()

        response = self.client.post(
            "/api/patient/assessments",
            headers={"X-CSRFToken": token}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json()["error"],
            "Authentication required"
        )

    def test_doctor_cannot_access_patient_assessment(self):
        token = self.get_csrf_token()

        with self.client.session_transaction() as session:
            session["user_id"] = 999
            session["role"] = "doctor"

        response = self.client.post(
            "/api/patient/assessments",
            headers={"X-CSRFToken": token}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.get_json()["error"],
            "Patient access only"
        )


if __name__ == "__main__":
    unittest.main()

from datetime import date


class PatientRiskAssessment:

    def __init__(self, interaction_engine):
        self.interaction_engine = interaction_engine

    def assess(self, medications, patient):
        interaction_result = (
            self.interaction_engine.check_interactions(medications)
        )

        flags = []
        missing_information = []

        dob = patient.get("date_of_birth")

        if dob:
            if isinstance(dob, str):
                dob = date.fromisoformat(dob)

            age = (
                date.today().year - dob.year
                - ((date.today().month, date.today().day)
                   < (dob.month, dob.day))
            )
        else:
            age = None
            missing_information.append("date_of_birth")

        allergies = patient.get("allergies")

        if allergies is None:
            missing_information.append("allergies")
        elif allergies:
            flags.append({
                "type": "allergy_review_required",
                "details": allergies
            })

        medical_history = patient.get("medical_history")

        if medical_history is None:
            missing_information.append("medical_history")

        for interaction in interaction_result["interactions"]:
            if interaction["status"] == "interaction_found":
                flags.append({
                    "type": "drug_interaction",
                    "drug_a": interaction["drug_a"],
                    "drug_b": interaction["drug_b"],
                    "severity": interaction["severity"],
                    "evidence": interaction["evidence_source"]
                })

        return {
            "patient_age": age,
            "interaction_count": sum(
                item["type"] == "drug_interaction" for item in flags
            ),
            "risk_flags": flags,
            "missing_information": missing_information,
            "unmatched_medications": (
                interaction_result["unmatched_medications"]
            ),
            "clinical_review_required": bool(flags or missing_information),
            "disclaimer": (
                "This assessment supports clinical review and does not "
                "establish medication safety or replace a clinician."
            )
        }
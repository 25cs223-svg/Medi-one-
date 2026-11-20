
import json

from flask import Blueprint, jsonify, session, current_app

from app.database import get_db_connection
from app.services.medication_intelligence.engine import (
    MedicationInteractionEngine
)
from app.services.medication_intelligence.patient_risk import (
    PatientRiskAssessment
)


patient_risk_bp = Blueprint(
    "patient_risk",
    __name__,
    url_prefix="/api/patient"
)


@patient_risk_bp.route("/assessments", methods=["POST"])
def create_assessment():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    if session.get("role") != "patient":
        return jsonify({"error": "Patient access only"}), 403

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT id, date_of_birth, allergies, medical_history
                    FROM patient_profiles
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )

                profile = cursor.fetchone()

                if not profile:
                    return jsonify({
                        "error": "Patient profile not found"
                    }), 404

                patient_id = profile[0]

                cursor.execute(
                    """
                    SELECT DISTINCT m.generic_name
                    FROM prescriptions p
                    JOIN prescription_items pi
                        ON pi.prescription_id = p.id
                    JOIN medications m
                        ON m.id = pi.medication_id
                    WHERE p.patient_id = %s
                      AND p.status = 'active'
                    ORDER BY m.generic_name
                    """,
                    (patient_id,)
                )

                medications = [
                    row[0] for row in cursor.fetchall()
                ]

                patient = {
                    "date_of_birth": profile[1],
                    "allergies": profile[2],
                    "medical_history": profile[3]
                }

                engine = MedicationInteractionEngine()
                assessor = PatientRiskAssessment(engine)

                result = assessor.assess(medications, patient)

                cursor.execute(
                    """
                    INSERT INTO safety_assessments
                    (patient_id, risk_level, assessment_result, explanation)
                    VALUES (%s, %s, %s::jsonb, %s)
                    RETURNING id
                    """,
                    (
                        patient_id,
                        None,
                        json.dumps(result),
                        "Evidence-based medication interaction review"
                    )
                )

                assessment_id = cursor.fetchone()[0]

        return jsonify({
            "assessment_id": assessment_id,
            "assessment": result
        }), 201

    except Exception:
        current_app.logger.exception(
            "Patient medication assessment failed"
        )
        return jsonify({
            "error": "Assessment could not be completed"
        }), 500

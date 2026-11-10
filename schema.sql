CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL
        CHECK (role IN ('patient', 'doctor')),
    created_at TIMESTAMPTZ DEFAULT NOW()
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_token_hash TEXT,
    email_verification_expires_at TIMESTAMPTZ,
);

CREATE TABLE IF NOT EXISTS patient_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    date_of_birth DATE,
    blood_group VARCHAR(5),
    allergies JSONB DEFAULT '[]'::jsonb,
    medical_history JSONB DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS doctor_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    specialization VARCHAR(150),
    license_number VARCHAR(100) UNIQUE
    verification_status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (verification_status IN ('pending', 'approved', 'rejected')),
);

CREATE TABLE IF NOT EXISTS medications (
    id BIGSERIAL PRIMARY KEY,
    generic_name VARCHAR(255) NOT NULL,
    brand_name VARCHAR(255),
    strength VARCHAR(100),
    interaction_evidence TEXT,
    source_reference TEXT
);

CREATE TABLE IF NOT EXISTS prescriptions (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT REFERENCES patient_profiles(id),
    doctor_id BIGINT REFERENCES doctor_profiles(id),
    prescription_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'cancelled')),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS prescription_items (
    id BIGSERIAL PRIMARY KEY,
    prescription_id BIGINT REFERENCES prescriptions(id)
        ON DELETE CASCADE,
    medication_id BIGINT REFERENCES medications(id),
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    duration_days INTEGER CHECK (duration_days > 0)
);

CREATE TABLE IF NOT EXISTS dosage_schedules (
    id BIGSERIAL PRIMARY KEY,
    prescription_item_id BIGINT REFERENCES prescription_items(id)
        ON DELETE CASCADE,
    dosage_time TIME NOT NULL,
    instructions TEXT
);

CREATE TABLE IF NOT EXISTS safety_assessments (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT REFERENCES patient_profiles(id),
    risk_level VARCHAR(20),
    assessment_result JSONB NOT NULL,
    explanation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

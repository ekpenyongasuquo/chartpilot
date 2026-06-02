"""
seed_db.py — Seeds ChartPilot demo database with realistic Nigerian FMC patient records

Run this once before starting the backend:
    cd demo_data
    python seed_db.py

Generates: chartpilot_demo.db with ~30 patients, 150+ records across all tables.
All names, IDs, and records are fictional — created for demo purposes only.
"""
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "./chartpilot_demo.db"

# ── Realistic Nigerian names ─────────────────────────────────────────────────
FIRST_NAMES_M = [
    "Emeka", "Chukwuemeka", "Biodun", "Tunde", "Femi", "Kayode",
    "Benson", "Sunday", "Monday", "Emmanuel", "Chidera", "Obinna",
    "Ikechukwu", "Uche", "Taiwo", "Kehinde", "Gbenga", "Segun",
]
FIRST_NAMES_F = [
    "Ngozi", "Adaeze", "Chioma", "Amaka", "Funmi", "Yetunde",
    "Blessing", "Grace", "Patience", "Comfort", "Faith", "Joy",
    "Ebunoluwa", "Folake", "Kemi", "Sade", "Nneka", "Ifeoma",
]
LAST_NAMES = [
    "Okonkwo", "Adeyemi", "Nwachukwu", "Eze", "Okafor", "Balogun",
    "Adesanya", "Chukwu", "Okeke", "Adeleke", "Ibrahim", "Musa",
    "Aliyu", "Obi", "Onyekachi", "Abubakar", "Fashola", "Ogundipe",
]

DEPARTMENTS = ["General OPD", "ANC", "Paediatrics", "Surgery", "Medicine", "Cardiology"]
DOCTORS = ["DR001", "DR002", "DR003", "DR004"]

LAB_TESTS = [
    ("Malaria RDT", ["Negative", "Positive", "Negative", "Negative", "Positive"], "", "Negative"),
    ("FBC - Haemoglobin", None, "g/dL", "11.5 - 17.5"),
    ("FBC - PCV", None, "%", "36 - 52"),
    ("Blood Glucose (RBS)", None, "mmol/L", "3.9 - 11.0"),
    ("HbA1c", None, "%", "< 6.5"),
    ("Serum Creatinine", None, "µmol/L", "53 - 115"),
    ("Serum Potassium", None, "mmol/L", "3.5 - 5.5"),
    ("Malaria Parasite Count", ["Negative", "+", "++", "+++", "Negative"], "", "Negative"),
    ("Urine Protein", ["Negative", "Trace", "+", "Negative", "Negative"], "", "Negative"),
    ("HIV Screening", ["Non-reactive", "Non-reactive", "Reactive", "Non-reactive"], "", "Non-reactive"),
    ("Widal Test", ["Negative", "Positive (1:160)", "Negative", "Negative"], "", "Negative"),
    ("Urinalysis", ["Normal", "WBC++, Bacteria+", "Normal", "RBC+"], "", "Normal"),
]

COMPLAINTS = [
    "Fever and body ache for 3 days",
    "Persistent cough for 2 weeks",
    "Lower abdominal pain",
    "Headache and dizziness",
    "Swollen legs and difficulty breathing",
    "Loss of appetite and weight loss",
    "Frequent urination and thirst",
    "Chest pain and palpitations",
    "Antenatal visit — 28 weeks",
    "Antenatal visit — 36 weeks",
    "Child brought in with high fever",
    "Routine checkup",
]

DIAGNOSES = [
    "Malaria (P. falciparum)",
    "Upper respiratory tract infection",
    "Urinary tract infection",
    "Hypertension — poorly controlled",
    "Type 2 Diabetes Mellitus",
    "Peptic ulcer disease",
    "Anaemia — iron deficiency",
    "Congestive cardiac failure",
    "Normal ANC — no complications",
    "Malaria in pregnancy",
    "Acute gastroenteritis",
    "Hypertensive heart disease",
]


def random_date(days_back: int = 365) -> str:
    d = datetime.now() - timedelta(days=random.randint(0, days_back))
    return d.strftime("%Y-%m-%d")


def make_patient_id(n: int) -> str:
    return f"FMC-{n:05d}"


def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Create tables ────────────────────────────────────────────────────────
    c.executescript("""
        DROP TABLE IF EXISTS patients;
        DROP TABLE IF EXISTS visits;
        DROP TABLE IF EXISTS lab_results;
        DROP TABLE IF EXISTS vitals;
        DROP TABLE IF EXISTS medications;
        DROP TABLE IF EXISTS audit_log;

        CREATE TABLE patients (
            patient_id TEXT PRIMARY KEY,
            first_name TEXT, last_name TEXT,
            date_of_birth TEXT, gender TEXT,
            phone TEXT, address TEXT, blood_group TEXT
        );

        CREATE TABLE visits (
            visit_id TEXT PRIMARY KEY,
            patient_id TEXT, visit_date TEXT,
            doctor_id TEXT, department TEXT,
            complaint TEXT, diagnosis TEXT, notes TEXT
        );

        CREATE TABLE lab_results (
            result_id TEXT PRIMARY KEY,
            patient_id TEXT, visit_id TEXT,
            test_name TEXT, result_value TEXT,
            result_unit TEXT, reference_range TEXT,
            status TEXT, collected_date TEXT, reported_date TEXT
        );

        CREATE TABLE vitals (
            vital_id TEXT PRIMARY KEY,
            patient_id TEXT, visit_id TEXT,
            recorded_date TEXT,
            bp_systolic INTEGER, bp_diastolic INTEGER,
            pulse INTEGER, temperature REAL,
            weight_kg REAL, height_cm REAL, spo2 INTEGER
        );

        CREATE TABLE medications (
            med_id TEXT PRIMARY KEY,
            patient_id TEXT, visit_id TEXT,
            drug_name TEXT, dosage TEXT,
            frequency TEXT, start_date TEXT,
            end_date TEXT, prescribed_by TEXT
        );

        CREATE TABLE audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, doctor_id TEXT,
            query_hash TEXT, patients_accessed TEXT,
            record_count INTEGER, sql_hash TEXT,
            critical_flagged INTEGER, access_purpose TEXT
        );
    """)

    # ── Seed patients ────────────────────────────────────────────────────────
    patients = []
    for i in range(1, 31):
        gender = random.choice(["M", "F"])
        first = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
        last = random.choice(LAST_NAMES)
        dob = random_date(365 * 50)
        pid = make_patient_id(i + 400)
        blood = random.choice(["A+", "B+", "O+", "AB+", "A-", "O-"])
        lga = random.choice(["Calabar Municipal", "Calabar South", "Odukpani", "Akamkpa"])
        patients.append((pid, first, last, dob, gender,
                         f"080{random.randint(10000000,99999999)}",
                         f"{random.randint(1,50)} {random.choice(['Murtala', 'Ndidem', 'Eta Agbor', 'IBB'])} Road, {lga}",
                         blood))

    c.executemany(
        "INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)", patients
    )

    # ── Seed visits, vitals, labs, meds ─────────────────────────────────────
    visit_count = 0
    result_count = 0
    vital_count = 0
    med_count = 0

    for patient in patients:
        pid = patient[0]
        gender = patient[4]
        num_visits = random.randint(2, 7)

        for v in range(num_visits):
            visit_count += 1
            vid = f"V{visit_count:05d}"
            vdate = random_date(400)
            dept = "ANC" if gender == "F" and random.random() < 0.3 else random.choice(DEPARTMENTS)
            complaint = random.choice(COMPLAINTS)
            diagnosis = random.choice(DIAGNOSES)
            doc = random.choice(DOCTORS)

            c.execute("INSERT INTO visits VALUES (?,?,?,?,?,?,?,?)",
                      (vid, pid, vdate, doc, dept, complaint, diagnosis,
                       f"Patient reviewed. {random.choice(['Follow up in 2 weeks.', 'Refer to specialist.', 'Continue medications.', 'Review labs.'])}"))

            # Vitals
            vital_count += 1
            bp_sys = random.randint(95, 195)
            bp_dia = random.randint(60, 125)
            c.execute("INSERT INTO vitals VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (f"VT{vital_count:05d}", pid, vid, vdate,
                       bp_sys, bp_dia,
                       random.randint(55, 105),
                       round(random.uniform(36.0, 39.5), 1),
                       round(random.uniform(45, 95), 1),
                       round(random.uniform(150, 185), 1),
                       random.randint(88, 100)))

            # Lab results (2-4 per visit)
            for _ in range(random.randint(2, 4)):
                result_count += 1
                test = random.choice(LAB_TESTS)
                test_name, options, unit, ref = test[0], test[1], test[2], test[3]

                if options:
                    value = random.choice(options)
                    status = "CRITICAL" if value in ["Positive", "Reactive", "+++"] else "COMPLETED"
                else:
                    # Generate numeric value — occasionally outside range for realism
                    ranges = {
                        "FBC - Haemoglobin": (5.5, 18.0),
                        "FBC - PCV": (17.0, 55.0),
                        "Blood Glucose (RBS)": (2.0, 24.0),
                        "HbA1c": (4.5, 12.0),
                        "Serum Creatinine": (40.0, 600.0),
                        "Serum Potassium": (2.2, 7.0),
                    }
                    lo, hi = ranges.get(test_name, (1.0, 10.0))
                    value = str(round(random.uniform(lo, hi), 1))
                    status = "COMPLETED"

                collect_date = vdate
                report_date = (datetime.strptime(vdate, "%Y-%m-%d") + timedelta(days=random.randint(0, 2))).strftime("%Y-%m-%d")

                c.execute("INSERT INTO lab_results VALUES (?,?,?,?,?,?,?,?,?,?)",
                          (f"LR{result_count:05d}", pid, vid,
                           test_name, value, unit, ref, status,
                           collect_date, report_date))

            # Medications (1-2 per visit)
            drugs = [
                ("Artemether-Lumefantrine", "80/480mg", "BD x3 days"),
                ("Amoxicillin", "500mg", "TDS x5 days"),
                ("Amlodipine", "5mg", "OD"),
                ("Metformin", "500mg", "BD"),
                ("Omeprazole", "20mg", "OD"),
                ("Folic Acid", "5mg", "OD"),
                ("Ferrous Sulphate", "200mg", "BD"),
                ("Lisinopril", "10mg", "OD"),
                ("Cotrimoxazole", "960mg", "BD x7 days"),
            ]
            for _ in range(random.randint(1, 2)):
                med_count += 1
                drug, dose, freq = random.choice(drugs)
                start = vdate
                end_d = (datetime.strptime(vdate, "%Y-%m-%d") + timedelta(days=random.randint(5, 90))).strftime("%Y-%m-%d")
                c.execute("INSERT INTO medications VALUES (?,?,?,?,?,?,?,?,?)",
                          (f"MED{med_count:05d}", pid, vid, drug, dose, freq, start, end_d, doc))

    conn.commit()
    conn.close()

    print(f"✅ Demo database seeded: {DB_PATH}")
    print(f"   Patients:    {len(patients)}")
    print(f"   Visits:      {visit_count}")
    print(f"   Lab results: {result_count}")
    print(f"   Vitals:      {vital_count}")
    print(f"   Medications: {med_count}")
    print()
    print("Sample patient IDs for demo queries:")
    for p in patients[:5]:
        print(f"  {p[0]} — {p[1]} {p[2]}")


if __name__ == "__main__":
    seed()
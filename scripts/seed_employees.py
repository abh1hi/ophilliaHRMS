#!/usr/bin/env python3
"""
Seed 8 dummy employees into auth_db + employee_db.

Requirements:
    pip install psycopg2-binary passlib[argon2]

Run:
    python scripts/seed_employees.py
"""

import uuid
import psycopg2
from passlib.context import CryptContext

# ── Config ────────────────────────────────────────────────────────────────────
DB_HOST     = "localhost"
DB_PORT     = 5432
DB_USER     = "postgres"
DB_PASSWORD = "changeme"

AUTH_DB     = "auth_db"
EMPLOYEE_DB = "employee_db"

EMPLOYEE_PASSWORD = "Employee@123"
COMPANY_NAME      = "Ophillia"

# ── Dummy data ────────────────────────────────────────────────────────────────
EMPLOYEES = [
    dict(
        first_name="Priya",        last_name="Sharma",
        email="priya.sharma@ophillia.com",
        personal_email="priya.sharma@gmail.com",
        phone="9876543201",        gender="female",
        date_of_birth="1995-06-14",
        door_no="12A",             street="MG Road",
        village_town="Bengaluru",  pin_code="560001",
        designation="Software Engineer",
        department_name="Engineering",
        role="employee",           date_joined="2023-03-01",
        joining_salary=65000,      project="Phoenix",
        bank_name="HDFC Bank",     bank_branch="Bengaluru Main",
        bank_account_number="50100123456789", ifsc_code="HDFC0001234",
        aadhaar_number="234567890123", pan_number="ABCDE1234F",
        uan_number="100234567890",
        emergency_contact_name="Rajesh Sharma",
        emergency_contact_number="9876543200",
        emergency_contact_relation="Father",
        highest_qualification="B.Tech Computer Science",
        year_of_passing="2017",    institute_name="VTU Bengaluru",
    ),
    dict(
        first_name="Arjun",        last_name="Nair",
        email="arjun.nair@ophillia.com",
        personal_email="arjun.nair@gmail.com",
        phone="9876543202",        gender="male",
        date_of_birth="1992-11-23",
        door_no="45",              street="Koramangala 5th Block",
        village_town="Bengaluru",  pin_code="560034",
        designation="Senior Software Engineer",
        department_name="Engineering",
        role="employee",           date_joined="2021-07-15",
        joining_salary=95000,      project="Phoenix",
        bank_name="ICICI Bank",    bank_branch="Koramangala",
        bank_account_number="012345678901", ifsc_code="ICIC0000123",
        aadhaar_number="345678901234", pan_number="FGHIJ5678K",
        uan_number="100345678901",
        emergency_contact_name="Meena Nair",
        emergency_contact_number="9876543210",
        emergency_contact_relation="Mother",
        highest_qualification="M.Tech Software Engineering",
        year_of_passing="2015",    institute_name="NIT Calicut",
    ),
    dict(
        first_name="Sneha",        last_name="Patel",
        email="sneha.patel@ophillia.com",
        personal_email="sneha.patel@gmail.com",
        phone="9876543203",        gender="female",
        date_of_birth="1997-03-08",
        door_no="7",               street="Indiranagar 100ft Road",
        village_town="Bengaluru",  pin_code="560038",
        designation="HR Executive",
        department_name="Human Resources",
        role="hr",                 date_joined="2022-01-10",
        joining_salary=45000,      project=None,
        bank_name="SBI",           bank_branch="Indiranagar",
        bank_account_number="30987654321", ifsc_code="SBIN0005678",
        aadhaar_number="456789012345", pan_number="KLMNO9012P",
        uan_number="100456789012",
        emergency_contact_name="Vikram Patel",
        emergency_contact_number="9876543211",
        emergency_contact_relation="Husband",
        highest_qualification="MBA Human Resources",
        year_of_passing="2019",    institute_name="Symbiosis Pune",
    ),
    dict(
        first_name="Rahul",        last_name="Verma",
        email="rahul.verma@ophillia.com",
        personal_email="rahul.verma@gmail.com",
        phone="9876543204",        gender="male",
        date_of_birth="1990-08-17",
        door_no="22B",             street="HSR Layout Sector 4",
        village_town="Bengaluru",  pin_code="560102",
        designation="Engineering Manager",
        department_name="Engineering",
        role="manager",            date_joined="2020-05-01",
        joining_salary=130000,     project="Titan",
        bank_name="Axis Bank",     bank_branch="HSR Layout",
        bank_account_number="919876543210", ifsc_code="UTIB0002345",
        aadhaar_number="567890123456", pan_number="PQRST3456Q",
        uan_number="100567890123",
        emergency_contact_name="Sunita Verma",
        emergency_contact_number="9876543212",
        emergency_contact_relation="Wife",
        highest_qualification="B.Tech Electronics",
        year_of_passing="2012",    institute_name="IIT Delhi",
    ),
    dict(
        first_name="Divya",        last_name="Menon",
        email="divya.menon@ophillia.com",
        personal_email="divya.menon@gmail.com",
        phone="9876543205",        gender="female",
        date_of_birth="1994-12-30",
        door_no="3",               street="Whitefield Main Road",
        village_town="Bengaluru",  pin_code="560066",
        designation="UI/UX Designer",
        department_name="Design",
        role="employee",           date_joined="2023-08-14",
        joining_salary=70000,      project="Phoenix",
        bank_name="HDFC Bank",     bank_branch="Whitefield",
        bank_account_number="50100987654321", ifsc_code="HDFC0005678",
        aadhaar_number="678901234567", pan_number="UVWXY7890R",
        uan_number="100678901234",
        emergency_contact_name="Anand Menon",
        emergency_contact_number="9876543213",
        emergency_contact_relation="Father",
        highest_qualification="B.Des Visual Communication",
        year_of_passing="2016",    institute_name="NID Ahmedabad",
    ),
    dict(
        first_name="Karan",        last_name="Singh",
        email="karan.singh@ophillia.com",
        personal_email="karan.singh@gmail.com",
        phone="9876543206",        gender="male",
        date_of_birth="1993-05-25",
        door_no="8",               street="Jayanagar 4th Block",
        village_town="Bengaluru",  pin_code="560011",
        designation="DevOps Engineer",
        department_name="Engineering",
        role="employee",           date_joined="2022-09-05",
        joining_salary=85000,      project="Titan",
        bank_name="Kotak Mahindra",bank_branch="Jayanagar",
        bank_account_number="7812345678", ifsc_code="KKBK0001234",
        aadhaar_number="789012345678", pan_number="ZABCD2345S",
        uan_number="100789012345",
        emergency_contact_name="Gurpreet Singh",
        emergency_contact_number="9876543214",
        emergency_contact_relation="Father",
        highest_qualification="B.Tech Information Technology",
        year_of_passing="2015",    institute_name="PEC Chandigarh",
    ),
    dict(
        first_name="Ananya",       last_name="Reddy",
        email="ananya.reddy@ophillia.com",
        personal_email="ananya.reddy@gmail.com",
        phone="9876543207",        gender="female",
        date_of_birth="1998-02-14",
        door_no="15",              street="Electronic City Phase 1",
        village_town="Bengaluru",  pin_code="560100",
        designation="QA Engineer",
        department_name="Engineering",
        role="employee",           date_joined="2024-01-08",
        joining_salary=55000,      project="Phoenix",
        bank_name="SBI",           bank_branch="Electronic City",
        bank_account_number="40123456789", ifsc_code="SBIN0009012",
        aadhaar_number="890123456789", pan_number="EFGHI6789T",
        uan_number="100890123456",
        emergency_contact_name="Suresh Reddy",
        emergency_contact_number="9876543215",
        emergency_contact_relation="Father",
        highest_qualification="B.Tech Computer Science",
        year_of_passing="2020",    institute_name="JNTU Hyderabad",
    ),
    dict(
        first_name="Mohammed",     last_name="Khan",
        email="mohammed.khan@ophillia.com",
        personal_email="mohammed.khan@gmail.com",
        phone="9876543208",        gender="male",
        date_of_birth="1991-09-07",
        door_no="33",              street="Old Madras Road",
        village_town="Bengaluru",  pin_code="560016",
        designation="Backend Developer",
        department_name="Engineering",
        role="employee",           date_joined="2021-11-20",
        joining_salary=90000,      project="Titan",
        bank_name="ICICI Bank",    bank_branch="Old Madras Road",
        bank_account_number="012987654321", ifsc_code="ICIC0001234",
        aadhaar_number="901234567890", pan_number="JKLMN0123U",
        uan_number="100901234567",
        emergency_contact_name="Fatima Khan",
        emergency_contact_number="9876543216",
        emergency_contact_relation="Mother",
        highest_qualification="B.Tech Computer Science",
        year_of_passing="2013",    institute_name="Osmania University",
    ),
]


def main():
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    hashed_pw   = pwd_context.hash(EMPLOYEE_PASSWORD)
    print(f"Password hash generated for '{EMPLOYEE_PASSWORD}'")

    # ── Connect to auth_db ────────────────────────────────────────────────────
    auth_conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, dbname=AUTH_DB,
    )
    auth_cur = auth_conn.cursor()

    # Get company_id
    auth_cur.execute("SELECT id FROM companies WHERE name = %s", (COMPANY_NAME,))
    row = auth_cur.fetchone()
    if not row:
        print(f"ERROR: Company '{COMPANY_NAME}' not found in auth_db. Run create_superadmin.sql first.")
        return
    company_id = row[0]
    print(f"Company ID: {company_id}")

    # ── Connect to employee_db ────────────────────────────────────────────────
    emp_conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, dbname=EMPLOYEE_DB,
    )
    emp_cur  = emp_conn.cursor()

    created = 0
    skipped = 0

    for emp in EMPLOYEES:
        # Check if user already exists in auth_db
        auth_cur.execute("SELECT id FROM users WHERE email = %s", (emp["email"],))
        existing = auth_cur.fetchone()
        if existing:
            print(f"  SKIP  {emp['email']} (already exists)")
            skipped += 1
            continue

        user_id = uuid.uuid4()

        # Insert into auth_db.users
        auth_cur.execute(
            """
            INSERT INTO users (id, company_id, email, hashed_password, role, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, TRUE, NOW(), NOW())
            """,
            (str(user_id), str(company_id), emp["email"], hashed_pw, emp["role"]),
        )

        # Resolve department_id from employee_db.departments (if table exists)
        dept_id = None
        try:
            emp_cur.execute(
                "SELECT id FROM departments WHERE name = %s LIMIT 1",
                (emp["department_name"],),
            )
            dept_row = emp_cur.fetchone()
            if not dept_row:
                # Create the department
                dept_id = uuid.uuid4()
                emp_cur.execute(
                    "INSERT INTO departments (id, name, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())",
                    (str(dept_id), emp["department_name"]),
                )
            else:
                dept_id = dept_row[0]
        except psycopg2.errors.UndefinedTable:
            emp_conn.rollback()
            dept_id = None

        # Insert into employee_db.employees
        emp_cur.execute(
            """
            INSERT INTO employees (
                id, user_id,
                first_name, last_name, gender, date_of_birth,
                door_no, street, village_town, pin_code,
                phone, personal_email, email,
                bank_account_number, bank_name, bank_branch, ifsc_code,
                aadhaar_number, pan_number, uan_number,
                emergency_contact_name, emergency_contact_number, emergency_contact_relation,
                highest_qualification, year_of_passing, institute_name,
                date_joined, department_id, designation, employment_status,
                project, joining_salary, role,
                created_at, updated_at
            ) VALUES (
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, 'active',
                %s, %s, %s,
                NOW(), NOW()
            )
            """,
            (
                str(uuid.uuid4()), str(user_id),
                emp["first_name"], emp["last_name"], emp.get("gender"), emp.get("date_of_birth"),
                emp.get("door_no"), emp.get("street"), emp.get("village_town"), emp.get("pin_code"),
                emp.get("phone"), emp.get("personal_email"), emp["email"],
                emp.get("bank_account_number"), emp.get("bank_name"), emp.get("bank_branch"), emp.get("ifsc_code"),
                emp.get("aadhaar_number"), emp.get("pan_number"), emp.get("uan_number"),
                emp.get("emergency_contact_name"), emp.get("emergency_contact_number"), emp.get("emergency_contact_relation"),
                emp.get("highest_qualification"), emp.get("year_of_passing"), emp.get("institute_name"),
                emp["date_joined"], str(dept_id) if dept_id else None, emp.get("designation"),
                emp.get("project"), emp.get("joining_salary"), emp.get("role"),
            ),
        )

        auth_conn.commit()
        emp_conn.commit()
        print(f"  OK    {emp['email']}  ({emp['designation']})")
        created += 1

    auth_cur.close(); auth_conn.close()
    emp_cur.close();  emp_conn.close()

    print(f"\nDone — {created} created, {skipped} skipped.")
    print(f"All employees can log in with password: {EMPLOYEE_PASSWORD}")


if __name__ == "__main__":
    main()

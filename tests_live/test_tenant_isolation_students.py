"""
Tenant Isolation Tests — Students Service
===========================================
Verifies that students, classes, and guardians are scoped per company_id.

Pre-requisites:
  - Docker services running (auth, students at minimum)

Test strategy:
  1. Register two companies with admin users
  2. Create classes under each company
  3. Enroll students under each company
  4. Verify Company A cannot see Company B's students/classes
  5. Verify same student_number can exist across tenants
"""

import json
import sys
import uuid
import urllib.error
import urllib.request
from datetime import datetime

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

AUTH_URL = "http://localhost:8000/api/v1/auth"
STUDENTS_URL = "http://localhost:8003/api/v1/students"
CLASSES_URL = "http://localhost:8003/api/v1/classes"

PASSED = 0
FAILED = 0
ERRORS = []


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def make_request(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            try:
                return resp.getcode(), json.loads(raw)
            except json.JSONDecodeError:
                return resp.getcode(), raw.decode()
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw.decode()
    except Exception as e:
        return 0, str(e)


def assert_eq(test_name, actual, expected):
    global PASSED, FAILED
    if actual == expected:
        PASSED += 1
        log(f"PASS: {test_name}")
    else:
        FAILED += 1
        msg = f"FAIL: {test_name} — expected {expected!r}, got {actual!r}"
        ERRORS.append(msg)
        log(msg, "FAIL")


def assert_true(test_name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        log(f"PASS: {test_name}")
    else:
        FAILED += 1
        msg = f"FAIL: {test_name}" + (f" — {detail}" if detail else "")
        ERRORS.append(msg)
        log(msg, "FAIL")


# ──────────────────────────────────────────────
# Setup helpers
# ──────────────────────────────────────────────

def register_company(suffix):
    data = {
        "name": f"StuTenant{suffix}_{uuid.uuid4().hex[:6]}",
        "domain": f"stutenant{suffix}-{uuid.uuid4().hex[:6]}.com",
    }
    status_code, resp = make_request(f"{AUTH_URL}/companies", "POST", data)
    if status_code not in (200, 201):
        log(f"Company registration failed ({status_code}): {resp}", "ERROR")
        return None
    if isinstance(resp, dict):
        company = resp.get("data", resp)
        return company.get("id") or company.get("company_id")
    return None


def register_user(email, password, role, company_id):
    data = {
        "email": email,
        "password": password,
        "role": role,
        "company_id": company_id,
        "first_name": "Test",
        "last_name": role.capitalize(),
    }
    status_code, resp = make_request(f"{AUTH_URL}/register", "POST", data)
    return status_code, resp


def login(email, password):
    data = {"email": email, "password": password}
    status_code, resp = make_request(f"{AUTH_URL}/login", "POST", data)
    if status_code != 200:
        log(f"Login failed ({status_code}): {resp}", "ERROR")
        return None
    if isinstance(resp, dict):
        return resp.get("access_token") or resp.get("data", {}).get("access_token")
    return None


# ──────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────

def main():
    global PASSED, FAILED

    log("=" * 60)
    log("TENANT ISOLATION TESTS — STUDENTS SERVICE")
    log("=" * 60)

    # ── Setup two tenants ──
    log("\n--- Setting up Company A ---")
    suffix_a = uuid.uuid4().hex[:4]
    company_a_id = register_company("A")
    if not company_a_id:
        log("Cannot proceed without Company A", "FATAL")
        sys.exit(1)
    log(f"Company A ID: {company_a_id}")

    email_a = f"stu-admin-a-{suffix_a}@test.com"
    register_user(email_a, "TestPass123!", "super_admin", company_a_id)
    token_a = login(email_a, "TestPass123!")
    if not token_a:
        log("Cannot proceed without Token A", "FATAL")
        sys.exit(1)

    log("\n--- Setting up Company B ---")
    suffix_b = uuid.uuid4().hex[:4]
    company_b_id = register_company("B")
    if not company_b_id:
        log("Cannot proceed without Company B", "FATAL")
        sys.exit(1)
    log(f"Company B ID: {company_b_id}")

    email_b = f"stu-admin-b-{suffix_b}@test.com"
    register_user(email_b, "TestPass123!", "super_admin", company_b_id)
    token_b = login(email_b, "TestPass123!")
    if not token_b:
        log("Cannot proceed without Token B", "FATAL")
        sys.exit(1)

    # ── Test 1: Class isolation ──
    log("\n--- Test: Class isolation ---")

    class_name_a = f"Grade-1A-{uuid.uuid4().hex[:4]}"
    status_ca, resp_ca = make_request(
        f"{CLASSES_URL}/",
        "POST",
        {"name": class_name_a, "section": "A", "academic_year": "2026-2027"},
        token_a,
    )
    assert_true("Company A can create class", status_ca in (200, 201),
                f"status={status_ca}, resp={resp_ca}")

    class_a_id = None
    if isinstance(resp_ca, dict):
        class_a_id = resp_ca.get("id")

    class_name_b = f"Grade-1B-{uuid.uuid4().hex[:4]}"
    status_cb, resp_cb = make_request(
        f"{CLASSES_URL}/",
        "POST",
        {"name": class_name_b, "section": "B", "academic_year": "2026-2027"},
        token_b,
    )
    assert_true("Company B can create class", status_cb in (200, 201),
                f"status={status_cb}, resp={resp_cb}")

    class_b_id = None
    if isinstance(resp_cb, dict):
        class_b_id = resp_cb.get("id")

    # List classes — each tenant sees only their own
    _, class_list_a = make_request(f"{CLASSES_URL}/", "GET", token=token_a)
    _, class_list_b = make_request(f"{CLASSES_URL}/", "GET", token=token_b)

    if isinstance(class_list_a, dict):
        items_a = class_list_a.get("items", class_list_a.get("data", []))
        if isinstance(items_a, list):
            cnames_a = [c.get("name") for c in items_a]
            assert_true("Company A sees own class", class_name_a in cnames_a,
                         f"Expected {class_name_a} in {cnames_a}")
            assert_true("Company A does NOT see Company B class", class_name_b not in cnames_a,
                         f"Found {class_name_b} in {cnames_a}")

    if isinstance(class_list_b, dict):
        items_b = class_list_b.get("items", class_list_b.get("data", []))
        if isinstance(items_b, list):
            cnames_b = [c.get("name") for c in items_b]
            assert_true("Company B sees own class", class_name_b in cnames_b,
                         f"Expected {class_name_b} in {cnames_b}")
            assert_true("Company B does NOT see Company A class", class_name_a not in cnames_b,
                         f"Found {class_name_a} in {cnames_b}")

    # ── Test 2: Student isolation ──
    log("\n--- Test: Student isolation ---")

    stu_num_a = f"STU-A-{uuid.uuid4().hex[:6]}"
    status_sa, resp_sa = make_request(
        f"{STUDENTS_URL}/",
        "POST",
        {
            "first_name": "Alice",
            "last_name": "TenantA",
            "student_number": stu_num_a,
            "date_of_birth": "2015-01-15",
            "gender": "female",
            "class_id": class_a_id,
        },
        token_a,
    )
    assert_true("Company A can enroll student", status_sa in (200, 201),
                f"status={status_sa}, resp={resp_sa}")

    student_a_id = None
    if isinstance(resp_sa, dict):
        student_a_id = resp_sa.get("id")

    stu_num_b = f"STU-B-{uuid.uuid4().hex[:6]}"
    status_sb, resp_sb = make_request(
        f"{STUDENTS_URL}/",
        "POST",
        {
            "first_name": "Bob",
            "last_name": "TenantB",
            "student_number": stu_num_b,
            "date_of_birth": "2015-06-20",
            "gender": "male",
            "class_id": class_b_id,
        },
        token_b,
    )
    assert_true("Company B can enroll student", status_sb in (200, 201),
                f"status={status_sb}, resp={resp_sb}")

    student_b_id = None
    if isinstance(resp_sb, dict):
        student_b_id = resp_sb.get("id")

    # List students — each sees only their own
    _, stu_list_a = make_request(f"{STUDENTS_URL}/", "GET", token=token_a)
    _, stu_list_b = make_request(f"{STUDENTS_URL}/", "GET", token=token_b)

    if isinstance(stu_list_a, dict):
        stu_items_a = stu_list_a.get("items", stu_list_a.get("data", []))
        if isinstance(stu_items_a, list):
            stu_nums_a = [s.get("student_number") for s in stu_items_a]
            assert_true("Company A sees own student", stu_num_a in stu_nums_a,
                         f"Expected {stu_num_a} in {stu_nums_a}")
            assert_true("Company A does NOT see Company B student", stu_num_b not in stu_nums_a,
                         f"Found {stu_num_b} in {stu_nums_a}")

    if isinstance(stu_list_b, dict):
        stu_items_b = stu_list_b.get("items", stu_list_b.get("data", []))
        if isinstance(stu_items_b, list):
            stu_nums_b = [s.get("student_number") for s in stu_items_b]
            assert_true("Company B sees own student", stu_num_b in stu_nums_b,
                         f"Expected {stu_num_b} in {stu_nums_b}")
            assert_true("Company B does NOT see Company A student", stu_num_a not in stu_nums_b,
                         f"Found {stu_num_a} in {stu_nums_b}")

    # ── Test 3: Cross-tenant student access ──
    log("\n--- Test: Cross-tenant student access ---")

    if student_a_id:
        status_cross, _ = make_request(f"{STUDENTS_URL}/{student_a_id}", "GET", token=token_b)
        assert_true(
            "Company B cannot access Company A's student by ID",
            status_cross in (403, 404),
            f"Got status {status_cross}",
        )

    if student_b_id:
        status_cross2, _ = make_request(f"{STUDENTS_URL}/{student_b_id}", "GET", token=token_a)
        assert_true(
            "Company A cannot access Company B's student by ID",
            status_cross2 in (403, 404),
            f"Got status {status_cross2}",
        )

    # ── Test 4: Same student_number across tenants ──
    log("\n--- Test: Same student number across tenants ---")

    shared_num = f"STU-SHARED-{uuid.uuid4().hex[:6]}"
    s1, _ = make_request(
        f"{STUDENTS_URL}/", "POST",
        {
            "first_name": "Shared",
            "last_name": "NumA",
            "student_number": shared_num,
            "date_of_birth": "2015-03-10",
            "gender": "male",
        },
        token_a,
    )
    s2, _ = make_request(
        f"{STUDENTS_URL}/", "POST",
        {
            "first_name": "Shared",
            "last_name": "NumB",
            "student_number": shared_num,
            "date_of_birth": "2015-07-22",
            "gender": "female",
        },
        token_b,
    )
    assert_true(
        "Same student number can exist in both companies",
        s1 in (200, 201) and s2 in (200, 201),
        f"Company A status={s1}, Company B status={s2}",
    )

    # ── Test 5: Cross-tenant class access ──
    log("\n--- Test: Cross-tenant class access ---")

    if class_a_id:
        status_cc, _ = make_request(f"{CLASSES_URL}/{class_a_id}", "GET", token=token_b)
        assert_true(
            "Company B cannot access Company A's class by ID",
            status_cc in (403, 404),
            f"Got status {status_cc}",
        )

    if class_b_id:
        status_cc2, _ = make_request(f"{CLASSES_URL}/{class_b_id}", "GET", token=token_a)
        assert_true(
            "Company A cannot access Company B's class by ID",
            status_cc2 in (403, 404),
            f"Got status {status_cc2}",
        )

    # ── Summary ──
    log("\n" + "=" * 60)
    log(f"RESULTS: {PASSED} passed, {FAILED} failed")
    if ERRORS:
        log("Failures:")
        for err in ERRORS:
            log(f"  - {err}", "FAIL")
    log("=" * 60)

    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()

"""
Tenant Isolation Tests — Payroll Service
==========================================
Verifies that salary structures, payroll runs, and payslips
are scoped per company_id.

Pre-requisites:
  - Docker services running (auth, employee, payroll at minimum)

Test strategy:
  1. Register two companies with super-admin users
  2. Create salary structures under each company
  3. Verify Company A cannot see Company B's salary structures
  4. Attempt payroll runs and verify cross-tenant invisibility
  5. Verify my-payslips endpoint is tenant-scoped
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
PAYROLL_URL = "http://localhost:8006/api/v1/payroll"
SALARY_URL = "http://localhost:8006/api/v1/salary"

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
        "name": f"PayTenant{suffix}_{uuid.uuid4().hex[:6]}",
        "domain": f"paytenant{suffix}-{uuid.uuid4().hex[:6]}.com",
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
    log("TENANT ISOLATION TESTS — PAYROLL SERVICE")
    log("=" * 60)

    # ── Setup two tenants ──
    log("\n--- Setting up Company A ---")
    suffix_a = uuid.uuid4().hex[:4]
    company_a_id = register_company("A")
    if not company_a_id:
        log("Cannot proceed without Company A", "FATAL")
        sys.exit(1)
    log(f"Company A ID: {company_a_id}")

    email_a = f"pay-admin-a-{suffix_a}@test.com"
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

    email_b = f"pay-admin-b-{suffix_b}@test.com"
    register_user(email_b, "TestPass123!", "super_admin", company_b_id)
    token_b = login(email_b, "TestPass123!")
    if not token_b:
        log("Cannot proceed without Token B", "FATAL")
        sys.exit(1)

    # ── Test 1: Salary structure isolation ──
    log("\n--- Test: Salary structure isolation ---")

    struct_name_a = f"Grade-A-{uuid.uuid4().hex[:4]}"
    status_sa, resp_sa = make_request(
        f"{SALARY_URL}/structures",
        "POST",
        {
            "name": struct_name_a,
            "base_salary": 50000.00,
            "hra_percent": 40.0,
            "da_percent": 10.0,
            "ta_amount": 1500.0,
            "pf_percent": 12.0,
            "esi_percent": 0.75,
            "professional_tax": 200.0,
        },
        token_a,
    )
    assert_true("Company A can create salary structure", status_sa in (200, 201),
                f"status={status_sa}, resp={resp_sa}")

    struct_name_b = f"Grade-B-{uuid.uuid4().hex[:4]}"
    status_sb, resp_sb = make_request(
        f"{SALARY_URL}/structures",
        "POST",
        {
            "name": struct_name_b,
            "base_salary": 60000.00,
            "hra_percent": 35.0,
            "da_percent": 12.0,
            "ta_amount": 2000.0,
            "pf_percent": 12.0,
            "esi_percent": 0.75,
            "professional_tax": 200.0,
        },
        token_b,
    )
    assert_true("Company B can create salary structure", status_sb in (200, 201),
                f"status={status_sb}, resp={resp_sb}")

    # List salary structures — each tenant should only see their own
    _, struct_list_a = make_request(f"{SALARY_URL}/structures", "GET", token=token_a)
    _, struct_list_b = make_request(f"{SALARY_URL}/structures", "GET", token=token_b)

    if isinstance(struct_list_a, list):
        names_a = [s.get("name") for s in struct_list_a]
        assert_true("Company A sees own salary structure", struct_name_a in names_a,
                     f"Expected {struct_name_a} in {names_a}")
        assert_true("Company A does NOT see Company B's structure", struct_name_b not in names_a,
                     f"Found {struct_name_b} in {names_a}")

    if isinstance(struct_list_b, list):
        names_b = [s.get("name") for s in struct_list_b]
        assert_true("Company B sees own salary structure", struct_name_b in names_b,
                     f"Expected {struct_name_b} in {names_b}")
        assert_true("Company B does NOT see Company A's structure", struct_name_a not in names_b,
                     f"Found {struct_name_a} in {names_b}")

    # ── Test 2: Same structure name across tenants ──
    log("\n--- Test: Same name across tenants ---")

    shared_name = f"Manager-Grade-{uuid.uuid4().hex[:4]}"
    s1, _ = make_request(
        f"{SALARY_URL}/structures", "POST",
        {"name": shared_name, "base_salary": 70000.00, "hra_percent": 40.0, "da_percent": 10.0,
         "ta_amount": 2000.0, "pf_percent": 12.0, "esi_percent": 0.75, "professional_tax": 200.0},
        token_a,
    )
    s2, _ = make_request(
        f"{SALARY_URL}/structures", "POST",
        {"name": shared_name, "base_salary": 75000.00, "hra_percent": 38.0, "da_percent": 11.0,
         "ta_amount": 2500.0, "pf_percent": 12.0, "esi_percent": 0.75, "professional_tax": 200.0},
        token_b,
    )
    assert_true(
        "Same structure name can exist in both companies",
        s1 in (200, 201) and s2 in (200, 201),
        f"Company A status={s1}, Company B status={s2}",
    )

    # ── Test 3: Payroll runs isolation ──
    log("\n--- Test: Payroll runs isolation ---")

    _, runs_a = make_request(f"{PAYROLL_URL}/runs", "GET", token=token_a)
    _, runs_b = make_request(f"{PAYROLL_URL}/runs", "GET", token=token_b)

    assert_true("Company A can list payroll runs", isinstance(runs_a, list),
                f"got {type(runs_a)}: {runs_a}")
    assert_true("Company B can list payroll runs", isinstance(runs_b, list),
                f"got {type(runs_b)}: {runs_b}")

    # Cross-check: no overlap in run IDs
    if isinstance(runs_a, list) and isinstance(runs_b, list):
        ids_a = {r.get("id") for r in runs_a}
        ids_b = {r.get("id") for r in runs_b}
        overlap = ids_a & ids_b
        assert_eq("No overlapping payroll run IDs between tenants", len(overlap), 0)

    # ── Test 4: My payslips isolation ──
    log("\n--- Test: My payslips isolation ---")

    status_ps_a, ps_a = make_request(f"{PAYROLL_URL}/my-payslips", "GET", token=token_a)
    status_ps_b, ps_b = make_request(f"{PAYROLL_URL}/my-payslips", "GET", token=token_b)

    assert_true("Company A can fetch my-payslips", status_ps_a == 200,
                f"status={status_ps_a}")
    assert_true("Company B can fetch my-payslips", status_ps_b == 200,
                f"status={status_ps_b}")

    # Both should return only their own payslips (possibly empty)
    if isinstance(ps_a, list) and isinstance(ps_b, list):
        ps_ids_a = {p.get("id") for p in ps_a}
        ps_ids_b = {p.get("id") for p in ps_b}
        ps_overlap = ps_ids_a & ps_ids_b
        assert_eq("No overlapping payslip IDs between tenants", len(ps_overlap), 0)

    # ── Test 5: Cross-tenant run access ──
    log("\n--- Test: Cross-tenant payroll run access ---")

    if isinstance(runs_a, list) and len(runs_a) > 0:
        run_a_id = runs_a[0].get("id")
        status_cross, _ = make_request(f"{PAYROLL_URL}/runs/{run_a_id}", "GET", token=token_b)
        assert_true(
            "Company B cannot access Company A's payroll run",
            status_cross in (403, 404),
            f"Got status {status_cross}",
        )

    if isinstance(runs_b, list) and len(runs_b) > 0:
        run_b_id = runs_b[0].get("id")
        status_cross2, _ = make_request(f"{PAYROLL_URL}/runs/{run_b_id}", "GET", token=token_a)
        assert_true(
            "Company A cannot access Company B's payroll run",
            status_cross2 in (403, 404),
            f"Got status {status_cross2}",
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

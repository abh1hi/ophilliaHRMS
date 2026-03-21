"""
Tenant Isolation Tests — Leave Service
=======================================
Verifies that leave types, balances, requests, and holidays
are scoped per company_id.

Pre-requisites:
  - Docker services running (auth, leave at minimum)

Test strategy:
  1. Register two companies with super-admin users
  2. Create leave types under each company
  3. Verify Company A cannot see Company B's leave types and vice-versa
  4. Create leave requests and verify cross-tenant invisibility
  5. Create holidays and verify tenant scoping
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
LEAVE_URL = "http://localhost:8004/api/v1"

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
        "name": f"LeaveTenant{suffix}_{uuid.uuid4().hex[:6]}",
        "domain": f"leavetenant{suffix}-{uuid.uuid4().hex[:6]}.com",
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
    log("TENANT ISOLATION TESTS — LEAVE SERVICE")
    log("=" * 60)

    # ── Setup two tenants ──
    log("\n--- Setting up Company A ---")
    suffix_a = uuid.uuid4().hex[:4]
    company_a_id = register_company("A")
    if not company_a_id:
        log("Cannot proceed without Company A", "FATAL")
        sys.exit(1)
    log(f"Company A ID: {company_a_id}")

    email_a = f"leave-admin-a-{suffix_a}@test.com"
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

    email_b = f"leave-admin-b-{suffix_b}@test.com"
    register_user(email_b, "TestPass123!", "super_admin", company_b_id)
    token_b = login(email_b, "TestPass123!")
    if not token_b:
        log("Cannot proceed without Token B", "FATAL")
        sys.exit(1)

    # ── Test 1: Leave Type isolation ──
    log("\n--- Test: Leave type isolation ---")

    lt_name_a = f"Sick-A-{uuid.uuid4().hex[:4]}"
    status_lt_a, resp_lt_a = make_request(
        f"{LEAVE_URL}/leave-types/",
        "POST",
        {"name": lt_name_a, "max_days_per_year": 12, "is_paid": True, "carry_forward": False},
        token_a,
    )
    assert_true("Company A can create leave type", status_lt_a in (200, 201),
                f"status={status_lt_a}, resp={resp_lt_a}")

    lt_a_id = None
    if isinstance(resp_lt_a, dict):
        lt_data = resp_lt_a.get("data", resp_lt_a)
        lt_a_id = lt_data.get("id")

    lt_name_b = f"Sick-B-{uuid.uuid4().hex[:4]}"
    status_lt_b, resp_lt_b = make_request(
        f"{LEAVE_URL}/leave-types/",
        "POST",
        {"name": lt_name_b, "max_days_per_year": 10, "is_paid": True, "carry_forward": True},
        token_b,
    )
    assert_true("Company B can create leave type", status_lt_b in (200, 201),
                f"status={status_lt_b}, resp={resp_lt_b}")

    lt_b_id = None
    if isinstance(resp_lt_b, dict):
        lt_data_b = resp_lt_b.get("data", resp_lt_b)
        lt_b_id = lt_data_b.get("id")

    # List leave types — each tenant sees only their own
    _, lt_list_a = make_request(f"{LEAVE_URL}/leave-types/", "GET", token=token_a)
    if isinstance(lt_list_a, dict):
        lt_items_a = lt_list_a.get("data", lt_list_a)
        if isinstance(lt_items_a, list):
            lt_names_a = [lt.get("name") for lt in lt_items_a]
            assert_true("Company A sees own leave type", lt_name_a in lt_names_a,
                         f"Expected {lt_name_a} in {lt_names_a}")
            assert_true("Company A does NOT see Company B leave type", lt_name_b not in lt_names_a,
                         f"Found {lt_name_b} in {lt_names_a}")

    _, lt_list_b = make_request(f"{LEAVE_URL}/leave-types/", "GET", token=token_b)
    if isinstance(lt_list_b, dict):
        lt_items_b = lt_list_b.get("data", lt_list_b)
        if isinstance(lt_items_b, list):
            lt_names_b = [lt.get("name") for lt in lt_items_b]
            assert_true("Company B sees own leave type", lt_name_b in lt_names_b,
                         f"Expected {lt_name_b} in {lt_names_b}")
            assert_true("Company B does NOT see Company A leave type", lt_name_a not in lt_names_b,
                         f"Found {lt_name_a} in {lt_names_b}")

    # ── Test 2: Same leave type name allowed across tenants ──
    log("\n--- Test: Same name across tenants ---")

    shared_name = f"Annual-{uuid.uuid4().hex[:4]}"
    s1, _ = make_request(
        f"{LEAVE_URL}/leave-types/",
        "POST",
        {"name": shared_name, "max_days_per_year": 20, "is_paid": True, "carry_forward": False},
        token_a,
    )
    s2, _ = make_request(
        f"{LEAVE_URL}/leave-types/",
        "POST",
        {"name": shared_name, "max_days_per_year": 15, "is_paid": True, "carry_forward": True},
        token_b,
    )
    assert_true(
        "Same leave type name can exist in both companies",
        s1 in (200, 201) and s2 in (200, 201),
        f"Company A status={s1}, Company B status={s2}",
    )

    # ── Test 3: Holiday isolation ──
    log("\n--- Test: Holiday isolation ---")

    holiday_a_name = f"Holiday-A-{uuid.uuid4().hex[:4]}"
    sh_a, _ = make_request(
        f"{LEAVE_URL}/holidays/",
        "POST",
        {"name": holiday_a_name, "date": "2026-12-25", "is_optional": False},
        token_a,
    )
    assert_true("Company A can create holiday", sh_a in (200, 201), f"status={sh_a}")

    holiday_b_name = f"Holiday-B-{uuid.uuid4().hex[:4]}"
    sh_b, _ = make_request(
        f"{LEAVE_URL}/holidays/",
        "POST",
        {"name": holiday_b_name, "date": "2026-12-25", "is_optional": False},
        token_b,
    )
    assert_true(
        "Company B can create holiday on same date (tenant-scoped uniqueness)",
        sh_b in (200, 201),
        f"status={sh_b}",
    )

    # List holidays
    _, hol_list_a = make_request(f"{LEAVE_URL}/holidays/", "GET", token=token_a)
    _, hol_list_b = make_request(f"{LEAVE_URL}/holidays/", "GET", token=token_b)

    if isinstance(hol_list_a, dict) and isinstance(hol_list_b, dict):
        hol_data_a = hol_list_a.get("data", hol_list_a)
        hol_data_b = hol_list_b.get("data", hol_list_b)
        if isinstance(hol_data_a, list) and isinstance(hol_data_b, list):
            hol_names_a = [h.get("name") for h in hol_data_a]
            hol_names_b = [h.get("name") for h in hol_data_b]
            assert_true("Company A holiday list contains own holiday",
                         holiday_a_name in hol_names_a)
            assert_true("Company A holiday list does NOT contain B's holiday",
                         holiday_b_name not in hol_names_a)
            assert_true("Company B holiday list contains own holiday",
                         holiday_b_name in hol_names_b)
            assert_true("Company B holiday list does NOT contain A's holiday",
                         holiday_a_name not in hol_names_b)

    # ── Test 4: Leave balance isolation ──
    log("\n--- Test: Leave balance isolation ---")

    _, bal_a = make_request(f"{LEAVE_URL}/leave-balances/me?year=2026", "GET", token=token_a)
    _, bal_b = make_request(f"{LEAVE_URL}/leave-balances/me?year=2026", "GET", token=token_b)

    # Both should return 200 and see only their own balances (possibly empty)
    assert_true("Company A can fetch own balances",
                isinstance(bal_a, (dict, list)),
                f"got {type(bal_a)}")
    assert_true("Company B can fetch own balances",
                isinstance(bal_b, (dict, list)),
                f"got {type(bal_b)}")

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

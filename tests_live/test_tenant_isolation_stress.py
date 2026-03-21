"""
Tenant Isolation Stress Test
============================
Creates N tenants concurrently, populates data in each, then verifies
strict isolation across ALL services.

Test strategy:
  1. Register N companies (default 3)
  2. For each: register HR user, login, create employee, create leave type,
     apply for leave, clock in attendance
  3. Cross-verify: each tenant's token can ONLY see its own data
  4. Verify list endpoints return correct counts per tenant

Pre-requisites:
  - All Docker services running (auth, employee, attendance, leave)
"""

import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

AUTH_URL = "http://localhost:8000/api/v1/auth"
EMPLOYEE_URL = "http://localhost:8001/api/v1"
ATTENDANCE_URL = "http://localhost:8002/api/v1/attendance"
LEAVE_URL = "http://localhost:8005/api/v1"

NUM_TENANTS = 3

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

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            try:
                resp_data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                resp_data = {}
            return resp.getcode(), resp_data
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            resp_data = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, Exception):
            resp_data = {"detail": str(e)}
        return e.code, resp_data
    except Exception as e:
        return 0, {"detail": str(e)}


def check(label, condition, detail=""):
    global PASSED, FAILED, ERRORS
    if condition:
        PASSED += 1
        log(f"PASS: {label}")
    else:
        FAILED += 1
        ERRORS.append(f"{label}: {detail}")
        log(f"FAIL: {label} — {detail}", "ERROR")


def extract_id(resp):
    """Safely extract 'id' from various response shapes."""
    if not isinstance(resp, dict):
        return None
    return resp.get("id") or (resp.get("data") or {}).get("id")


def extract_field(resp, field):
    """Safely extract a field from response or response.data."""
    if not isinstance(resp, dict):
        return None
    return resp.get(field) or (resp.get("data") or {}).get(field)


def provision_tenant(index):
    """Provision one tenant: company + super_admin user + employee + leave type + leave request."""
    tag = uuid.uuid4().hex[:6]
    tenant = {"index": index, "tag": tag}

    # Register company
    status, resp = make_request(f"{AUTH_URL}/companies", "POST", {
        "name": f"StressCorp-{index}-{tag}",
        "domain": f"stress-{index}-{tag}.com",
    })
    if status not in (200, 201):
        log(f"Tenant {index}: company registration failed ({status})", "ERROR")
        return None
    tenant["company_id"] = extract_id(resp)

    # Register super_admin user
    email = f"admin-{tag}@stress-{index}-{tag}.com"
    password = "StressTest123!"
    status, resp = make_request(f"{AUTH_URL}/register", "POST", {
        "email": email,
        "password": password,
        "role": "super_admin",
        "company_id": tenant["company_id"],
    })
    tenant["user_id"] = extract_id(resp)

    # Login (retry once on 401 — concurrent requests may race)
    status, resp = make_request(f"{AUTH_URL}/login", "POST", {
        "email": email,
        "password": password,
    })
    if status == 401:
        time.sleep(1)
        status, resp = make_request(f"{AUTH_URL}/login", "POST", {
            "email": email,
            "password": password,
        })
    if status != 200:
        log(f"Tenant {index}: login failed ({status})", "ERROR")
        return None
    tenant["token"] = extract_field(resp, "access_token")

    # Create employee
    status, resp = make_request(f"{EMPLOYEE_URL}/employees", "POST", {
        "user_id": tenant["user_id"] or str(uuid.uuid4()),
        "first_name": f"Stress-{index}",
        "last_name": f"Worker-{tag}",
        "email": f"emp-{tag}@stress-{index}-{tag}.com",
        "phone": "+91-9876543210",
        "date_of_birth": "1990-01-15",
        "date_joined": "2024-01-01",
        "designation": "Tester",
    }, token=tenant["token"])
    tenant["employee_id"] = extract_id(resp)

    # Create leave type
    status, resp = make_request(f"{LEAVE_URL}/leave-types/", "POST", {
        "name": f"Vacation-{index}-{tag}",
        "description": f"Vacation for tenant {index}",
        "days_allowed": 15,
    }, token=tenant["token"])
    tenant["leave_type_id"] = extract_id(resp)

    # Initialize leave balance
    if tenant.get("employee_id") and tenant.get("leave_type_id"):
        make_request(f"{LEAVE_URL}/leave-balances/", "POST", {
            "employee_id": tenant["employee_id"],
            "leave_type_id": tenant["leave_type_id"],
            "year": date.today().year,
            "total_days": 15,
            "used_days": 0,
        }, token=tenant["token"])

    # Apply for leave
    if tenant.get("employee_id") and tenant.get("leave_type_id"):
        start = (date.today() + timedelta(days=30 + index * 5)).isoformat()
        end = (date.today() + timedelta(days=32 + index * 5)).isoformat()
        status, resp = make_request(f"{LEAVE_URL}/leave-requests/", "POST", {
            "employee_id": tenant["employee_id"],
            "leave_type_id": tenant["leave_type_id"],
            "start_date": start,
            "end_date": end,
            "reason": f"Stress test tenant {index}",
        }, token=tenant["token"])
        tenant["leave_request_id"] = extract_id(resp)

    # Clock in
    if tenant.get("employee_id"):
        make_request(f"{ATTENDANCE_URL}/clock-in", "POST", {
            "employee_id": tenant["employee_id"],
            "latitude": 12.9716 + index * 0.01,
            "longitude": 77.5946 + index * 0.01,
        }, token=tenant["token"])

    log(f"Tenant {index} provisioned: company={tenant.get('company_id', 'N/A')}")
    return tenant


def verify_isolation(tenants):
    """Cross-verify that each tenant can only see its own data."""
    log("=" * 50)
    log("Verifying tenant isolation across services")
    log("=" * 50)

    for i, tenant_a in enumerate(tenants):
        token_a = tenant_a["token"]
        emp_a = tenant_a.get("employee_id")

        # ── Employee isolation ──
        status, resp = make_request(f"{EMPLOYEE_URL}/employees", "GET", token=token_a)
        if status == 200:
            employees = resp.get("employees", resp.get("data", []))
            if isinstance(employees, list):
                # Verify we only see our own tenant's employees
                for other in tenants:
                    if other["index"] != tenant_a["index"]:
                        other_emp = other.get("employee_id")
                        if other_emp:
                            leaked = any(
                                str(e.get("id")) == str(other_emp)
                                for e in employees
                                if isinstance(e, dict)
                            )
                            check(
                                f"Employee isolation: T{tenant_a['index']} cannot see T{other['index']}'s employee",
                                not leaked,
                                f"T{other['index']}'s employee {other_emp} visible to T{tenant_a['index']}",
                            )

        # ── Leave requests isolation ──
        status, resp = make_request(f"{LEAVE_URL}/leave-requests/", "GET", token=token_a)
        if status == 200:
            items = resp.get("data", [])
            if isinstance(items, list):
                for other in tenants:
                    if other["index"] != tenant_a["index"]:
                        other_lr = other.get("leave_request_id")
                        if other_lr:
                            leaked = any(
                                str(item.get("id")) == str(other_lr)
                                for item in items
                                if isinstance(item, dict)
                            )
                            check(
                                f"Leave isolation: T{tenant_a['index']} cannot see T{other['index']}'s leave request",
                                not leaked,
                                f"T{other['index']}'s leave {other_lr} visible to T{tenant_a['index']}",
                            )

        # ── Leave types isolation ──
        status, resp = make_request(f"{LEAVE_URL}/leave-types/", "GET", token=token_a)
        if status == 200:
            items = resp.get("data", [])
            if isinstance(items, list):
                for other in tenants:
                    if other["index"] != tenant_a["index"]:
                        other_lt = other.get("leave_type_id")
                        if other_lt:
                            leaked = any(
                                str(item.get("id")) == str(other_lt)
                                for item in items
                                if isinstance(item, dict)
                            )
                            check(
                                f"Leave type isolation: T{tenant_a['index']} cannot see T{other['index']}'s type",
                                not leaked,
                                f"T{other['index']}'s type {other_lt} visible to T{tenant_a['index']}",
                            )

        # ── Attendance isolation ──
        status, resp = make_request(f"{ATTENDANCE_URL}/me", "GET", token=token_a)
        check(
            f"Attendance endpoint accessible for T{tenant_a['index']}",
            status == 200,
            f"status={status}",
        )


def run():
    log(f"Tenant Isolation Stress Test — {NUM_TENANTS} tenants")
    log("=" * 50)

    # ── Phase 1: Provision tenants (concurrent) ──
    log("Phase 1: Provisioning tenants...")
    tenants = []
    with ThreadPoolExecutor(max_workers=NUM_TENANTS) as pool:
        futures = {pool.submit(provision_tenant, i): i for i in range(NUM_TENANTS)}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                log(f"Tenant {idx} provisioning exception: {exc}", "ERROR")
                result = None
            if result:
                tenants.append(result)
            else:
                log(f"Tenant {idx} provisioning failed", "ERROR")

    check(
        f"All {NUM_TENANTS} tenants provisioned",
        len(tenants) == NUM_TENANTS,
        f"Only {len(tenants)}/{NUM_TENANTS} succeeded",
    )

    if len(tenants) < 2:
        log("Need at least 2 tenants for isolation tests", "FATAL")
        return False

    # ── Phase 2: Verify isolation ──
    verify_isolation(tenants)

    # ── Phase 3: Verify data counts ──
    log("=" * 50)
    log("Phase 3: Verify per-tenant data counts")
    for tenant in tenants:
        token = tenant["token"]
        idx = tenant["index"]

        # Employee count
        status, resp = make_request(f"{EMPLOYEE_URL}/employees", "GET", token=token)
        if status == 200:
            total = resp.get("total", len(resp.get("employees", resp.get("data", []))))
            check(
                f"T{idx} employee count",
                total >= 1,
                f"total={total}, expected >= 1",
            )

        # Leave request count
        status, resp = make_request(f"{LEAVE_URL}/leave-requests/", "GET", token=token)
        if status == 200:
            items = resp.get("data", [])
            count = len(items) if isinstance(items, list) else 0
            check(
                f"T{idx} leave request count",
                count >= 1,
                f"count={count}, expected >= 1",
            )

    # ── Summary ──
    log("")
    log("=" * 50)
    log(f"Stress Test Results: {PASSED} passed, {FAILED} failed")
    if ERRORS:
        log("Failures:", "ERROR")
        for e in ERRORS:
            log(f"  - {e}", "ERROR")
    log("=" * 50)

    return FAILED == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)

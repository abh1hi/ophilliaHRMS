"""
End-to-End Lifecycle Integration Test
======================================
Exercises the full employee lifecycle across services:

  1. Register company (auth)
  2. Register HR user (auth)
  3. Login as HR (auth)
  4. Create employee (employee-service)
  5. Create department + assign (employee-service)
  6. Create leave type (leave-service)
  7. Initialize leave balance (leave-service)
  8. Apply for leave (leave-service)
  9. Approve leave (leave-service)
 10. Clock in + clock out (attendance-service)
 11. Verify attendance records (attendance-service)
 12. Logout (auth) and verify token is revoked

Pre-requisites:
  - All Docker services running (auth, employee, attendance, leave)
"""

import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import date, datetime, timedelta

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

AUTH_URL = "http://localhost:8000/api/v1/auth"
EMPLOYEE_URL = "http://localhost:8001/api/v1"
ATTENDANCE_URL = "http://localhost:8002/api/v1/attendance"
LEAVE_URL = "http://localhost:8005/api/v1"

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
        with urllib.request.urlopen(req) as resp:
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


def run():
    tag = uuid.uuid4().hex[:6]
    log(f"Starting E2E lifecycle test (tag={tag})")

    # ── Step 1: Register company ──
    log("Step 1: Register company")
    status, resp = make_request(f"{AUTH_URL}/companies", "POST", {
        "name": f"LifecycleCorp-{tag}",
        "domain": f"lifecycle-{tag}.com",
    })
    check("Register company", status in (200, 201), f"status={status}")
    company_id = extract_id(resp)
    if not company_id:
        log("Cannot proceed without company_id", "FATAL")
        return

    # ── Step 2: Register super_admin user ──
    log("Step 2: Register super_admin user")
    admin_email = f"admin-{tag}@lifecycle-{tag}.com"
    admin_password = "LifecycleTest123!"
    status, resp = make_request(f"{AUTH_URL}/register", "POST", {
        "email": admin_email,
        "password": admin_password,
        "role": "super_admin",
        "company_id": company_id,
    })
    check("Register super_admin user", status in (200, 201), f"status={status}")
    admin_user_id = extract_id(resp)

    # ── Step 3: Login as super_admin ──
    log("Step 3: Login as super_admin")
    status, resp = make_request(f"{AUTH_URL}/login", "POST", {
        "email": admin_email,
        "password": admin_password,
    })
    check("Login as super_admin", status == 200, f"status={status}")
    token = extract_field(resp, "access_token")
    if not token:
        log("Cannot proceed without token", "FATAL")
        return

    # ── Step 4: Create employee ──
    log("Step 4: Create employee")
    emp_email = f"emp-{tag}@lifecycle-{tag}.com"
    status, resp = make_request(f"{EMPLOYEE_URL}/employees", "POST", {
        "user_id": admin_user_id or str(uuid.uuid4()),
        "first_name": "Jane",
        "last_name": "Lifecycle",
        "email": emp_email,
        "phone": "+91-9876543210",
        "date_of_birth": "1990-01-15",
        "date_joined": "2024-01-01",
        "designation": "Engineer",
    }, token=token)
    check("Create employee", status in (200, 201), f"status={status}, resp={resp}")
    employee_id = extract_id(resp)

    # ── Step 5: Create department ──
    log("Step 5: Create department")
    status, resp = make_request(f"{EMPLOYEE_URL}/departments", "POST", {
        "name": f"Engineering-{tag}",
        "description": "Lifecycle test department",
    }, token=token)
    check("Create department", status in (200, 201), f"status={status}")

    # ── Step 6: Create leave type ──
    log("Step 6: Create leave type")
    status, resp = make_request(f"{LEAVE_URL}/leave-types/", "POST", {
        "name": f"Annual-{tag}",
        "description": "Annual leave for lifecycle test",
        "days_allowed": 20,
    }, token=token)
    check("Create leave type", status in (200, 201), f"status={status}")
    leave_type_id = None
    if isinstance(resp, dict):
        leave_type_id = extract_id(resp)

    # ── Step 7: Initialize leave balance ──
    if leave_type_id and employee_id:
        log("Step 7: Initialize leave balance")
        status, resp = make_request(f"{LEAVE_URL}/leave-balances/", "POST", {
            "employee_id": employee_id,
            "leave_type_id": leave_type_id,
            "year": date.today().year,
            "total_days": 20,
            "used_days": 0,
        }, token=token)
        check("Initialize leave balance", status in (200, 201), f"status={status}")
    else:
        log("Step 7: Skipped (missing leave_type_id or employee_id)", "WARN")

    # ── Step 8: Apply for leave ──
    if leave_type_id and employee_id:
        log("Step 8: Apply for leave")
        start_date = (date.today() + timedelta(days=7)).isoformat()
        end_date = (date.today() + timedelta(days=9)).isoformat()
        status, resp = make_request(f"{LEAVE_URL}/leave-requests/", "POST", {
            "employee_id": employee_id,
            "leave_type_id": leave_type_id,
            "start_date": start_date,
            "end_date": end_date,
            "reason": "Lifecycle integration test",
        }, token=token)
        check("Apply for leave", status in (200, 201), f"status={status}, resp={resp}")
        leave_request_id = None
        if isinstance(resp, dict):
            leave_request_id = extract_id(resp)
    else:
        log("Step 8: Skipped (missing leave_type_id or employee_id)", "WARN")
        leave_request_id = None

    # ── Step 9: Approve leave ──
    if leave_request_id:
        log("Step 9: Approve leave request")
        status, resp = make_request(
            f"{LEAVE_URL}/leave-requests/{leave_request_id}/status",
            "PUT",
            {"status": "approved"},
            token=token,
        )
        check("Approve leave", status == 200, f"status={status}")
    else:
        log("Step 9: Skipped (no leave_request_id)", "WARN")

    # ── Step 10: Clock in / clock out ──
    if employee_id:
        log("Step 10: Clock in")
        status, resp = make_request(f"{ATTENDANCE_URL}/clock-in", "POST", {
            "employee_id": employee_id,
            "latitude": 12.9716,
            "longitude": 77.5946,
        }, token=token)
        check("Clock in", status in (200, 201), f"status={status}, resp={resp}")

        time.sleep(1)

        log("Step 10b: Clock out")
        status, resp = make_request(f"{ATTENDANCE_URL}/clock-out", "POST", {
            "employee_id": employee_id,
            "latitude": 12.9716,
            "longitude": 77.5946,
        }, token=token)
        check("Clock out", status in (200, 201), f"status={status}, resp={resp}")
    else:
        log("Step 10: Skipped (no employee_id)", "WARN")

    # ── Step 11: Verify attendance records ──
    log("Step 11: Verify attendance records")
    status, resp = make_request(f"{ATTENDANCE_URL}/me", "GET", token=token)
    check("Get my attendance", status == 200, f"status={status}")

    # ── Step 12: Logout and verify revocation ──
    log("Step 12: Logout")
    status, resp = make_request(f"{AUTH_URL}/logout", "POST", token=token)
    check("Logout", status in (200, 204), f"status={status}")

    log("Step 12b: Verify token revoked")
    time.sleep(0.5)
    status, resp = make_request(f"{EMPLOYEE_URL}/employees", "GET", token=token)
    check("Token revoked after logout", status in (401, 403), f"status={status} (expected 401/403)")

    # ── Summary ──
    log("=" * 50)
    log(f"E2E Lifecycle Test Results: {PASSED} passed, {FAILED} failed")
    if ERRORS:
        log("Failures:", "ERROR")
        for e in ERRORS:
            log(f"  - {e}", "ERROR")
    log("=" * 50)

    return FAILED == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)

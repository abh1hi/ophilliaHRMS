"""
Cross-Service Event Flow Integration Test
==========================================
Verifies that actions in one service produce observable side-effects
in other services via RabbitMQ events and HTTP callbacks.

Test scenarios:
  1. Employee creation → audit log entry (via event)
  2. Leave approval → notification log entry (via event)
  3. Health check aggregation — all services report healthy

Pre-requisites:
  - All Docker services running with RabbitMQ
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
ATTENDANCE_URL = "http://localhost:8002/api/v1"
LEAVE_URL = "http://localhost:8005/api/v1"
NOTIFICATION_URL = "http://localhost:8007/api/v1"
AUDIT_URL = "http://localhost:8006/api/v1"

HEALTH_ENDPOINTS = [
    ("gateway", "http://localhost/health"),
    ("auth", "http://localhost:8000/health"),
    ("employee", "http://localhost:8001/health"),
    ("attendance", "http://localhost:8002/health"),
    ("students", "http://localhost:8003/health"),
    ("payroll", "http://localhost:8004/health"),
    ("leave", "http://localhost:8005/health"),
    ("audit", "http://localhost:8006/health"),
    ("notification", "http://localhost:8007/health"),
]

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
        with urllib.request.urlopen(req, timeout=10) as resp:
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


def setup_tenant():
    """Create a company + super_admin user + login, returning (token, company_id, user_id)."""
    tag = uuid.uuid4().hex[:6]

    status, resp = make_request(f"{AUTH_URL}/companies", "POST", {
        "name": f"EventCorp-{tag}",
        "domain": f"event-{tag}.com",
    })
    if status not in (200, 201):
        return None, None, None
    company_id = extract_id(resp)

    email = f"admin-{tag}@event-{tag}.com"
    password = "EventTest123!"
    status, resp = make_request(f"{AUTH_URL}/register", "POST", {
        "email": email,
        "password": password,
        "role": "super_admin",
        "company_id": company_id,
    })
    user_id = extract_id(resp)

    status, resp = make_request(f"{AUTH_URL}/login", "POST", {
        "email": email,
        "password": password,
    })
    if status != 200:
        return None, company_id, user_id
    token = extract_field(resp, "access_token")
    return token, company_id, user_id


def test_health_checks():
    """Scenario 3: Verify all services report healthy with standard format."""
    log("=" * 50)
    log("Test: Health Check Aggregation")
    log("=" * 50)

    for name, url in HEALTH_ENDPOINTS:
        status, resp = make_request(url)
        if name == "gateway":
            # Gateway returns a simpler format
            check(
                f"Health: {name} responds",
                status == 200 and resp.get("status") in ("healthy", "degraded"),
                f"status={status}, resp={resp}",
            )
        else:
            check(
                f"Health: {name} responds",
                status == 200,
                f"status={status}",
            )
            # Accept both old format (flat) and new format (with checks object)
            has_status = resp.get("status") in ("healthy", "degraded")
            has_service = "service" in resp
            has_version = "version" in resp
            check(
                f"Health: {name} standard format",
                has_status and has_service and has_version,
                f"resp={resp}",
            )
            if resp.get("checks"):
                for dep, dep_status in resp["checks"].items():
                    check(
                        f"Health: {name}.{dep}",
                        dep_status == "ok",
                        f"{dep}={dep_status}",
                    )


def test_employee_creation_audit():
    """Scenario 1: Employee creation should produce an audit log entry."""
    log("=" * 50)
    log("Test: Employee Creation → Audit Log")
    log("=" * 50)

    token, company_id, user_id = setup_tenant()
    if not token:
        log("Setup failed, skipping", "WARN")
        return

    tag = uuid.uuid4().hex[:6]
    status, resp = make_request(f"{EMPLOYEE_URL}/employees", "POST", {
        "user_id": user_id or str(uuid.uuid4()),
        "first_name": "Audit",
        "last_name": f"Test-{tag}",
        "email": f"audit-{tag}@test.com",
        "phone": "+91-9876543210",
        "date_of_birth": "1990-01-15",
        "date_joined": "2024-01-01",
        "designation": "QA",
    }, token=token)
    check("Create employee for audit test", status in (200, 201), f"status={status}")

    # Wait for async event propagation
    log("Waiting 3s for event propagation...")
    time.sleep(3)

    # Query audit logs for this company
    status, resp = make_request(f"{AUDIT_URL}/audit/logs?limit=10", "GET", token=token)
    check("Query audit logs", status == 200, f"status={status}")

    if status == 200:
        items = resp.get("data", resp) if isinstance(resp, dict) else resp
        if isinstance(items, list):
            has_employee_event = any(
                "employee" in str(item).lower() for item in items
            )
            check(
                "Audit log contains employee event",
                has_employee_event,
                f"Found {len(items)} logs, none mention employee",
            )
        else:
            log(f"Unexpected audit response shape: {type(items)}", "WARN")


def test_leave_approval_notification():
    """Scenario 2: Leave approval should produce a notification."""
    log("=" * 50)
    log("Test: Leave Approval → Notification")
    log("=" * 50)

    token, company_id, user_id = setup_tenant()
    if not token:
        log("Setup failed, skipping", "WARN")
        return

    tag = uuid.uuid4().hex[:6]

    # Create employee
    status, resp = make_request(f"{EMPLOYEE_URL}/employees", "POST", {
        "user_id": user_id or str(uuid.uuid4()),
        "first_name": "Notify",
        "last_name": f"Test-{tag}",
        "email": f"notify-{tag}@test.com",
        "phone": "+91-9876543210",
        "date_of_birth": "1990-01-15",
        "date_joined": "2024-01-01",
        "designation": "QA",
    }, token=token)
    employee_id = extract_id(resp)

    # Create leave type
    status, resp = make_request(f"{LEAVE_URL}/leave-types/", "POST", {
        "name": f"Sick-{tag}",
        "description": "Sick leave",
        "days_allowed": 10,
    }, token=token)
    leave_type_id = extract_id(resp)

    if not employee_id or not leave_type_id:
        log("Cannot create leave request (missing IDs)", "WARN")
        return

    # Initialize balance
    make_request(f"{LEAVE_URL}/leave-balances/", "POST", {
        "employee_id": employee_id,
        "leave_type_id": leave_type_id,
        "year": date.today().year,
        "total_days": 10,
        "used_days": 0,
    }, token=token)

    # Apply for leave
    start_date = (date.today() + timedelta(days=14)).isoformat()
    end_date = (date.today() + timedelta(days=15)).isoformat()
    status, resp = make_request(f"{LEAVE_URL}/leave-requests/", "POST", {
        "employee_id": employee_id,
        "leave_type_id": leave_type_id,
        "start_date": start_date,
        "end_date": end_date,
        "reason": "Event flow test",
    }, token=token)
    leave_request_id = extract_id(resp)

    if not leave_request_id:
        log("Cannot approve leave (no request ID)", "WARN")
        return

    # Approve
    status, resp = make_request(
        f"{LEAVE_URL}/leave-requests/{leave_request_id}/status",
        "PUT",
        {"status": "approved"},
        token=token,
    )
    check("Approve leave", status == 200, f"status={status}")

    # Wait for async event propagation
    log("Waiting 3s for event propagation...")
    time.sleep(3)

    # Check notification logs
    status, resp = make_request(
        f"{NOTIFICATION_URL}/notifications/logs?limit=10",
        "GET",
        token=token,
    )
    check("Query notification logs", status == 200, f"status={status}")

    if status == 200:
        items = resp.get("data", resp) if isinstance(resp, dict) else resp
        if isinstance(items, list):
            has_leave_event = any(
                "leave" in str(item).lower() or "approved" in str(item).lower()
                for item in items
            )
            check(
                "Notification log contains leave approval event",
                has_leave_event,
                f"Found {len(items)} logs, none mention leave/approved",
            )


def run():
    log("Cross-Service Event Flow Integration Tests")
    log("=" * 50)

    test_health_checks()
    test_employee_creation_audit()
    test_leave_approval_notification()

    log("")
    log("=" * 50)
    log(f"Results: {PASSED} passed, {FAILED} failed")
    if ERRORS:
        log("Failures:", "ERROR")
        for e in ERRORS:
            log(f"  - {e}", "ERROR")
    log("=" * 50)

    return FAILED == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)

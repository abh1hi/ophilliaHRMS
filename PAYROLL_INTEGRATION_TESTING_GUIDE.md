# Payroll Service Integration Testing Guide

**Version:** 1.0  
**Scope:** Testing payroll service's integration with other OphilliaHRMS services  
**Environment:** Staging (before production deployment)  
**Duration:** 2-3 hours per full test cycle  
**Last Updated:** 2025-04-07

---

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Integration Points](#integration-points)
3. [Test Cases by Service](#test-cases-by-service)
4. [Performance & Load Testing](#performance--load-testing)
5. [Failure Scenario Testing](#failure-scenario-testing)
6. [Test Sign-Off](#test-sign-off)

---

## Test Environment Setup

### Prerequisites

```bash
# 1. Ensure all services running in staging
kubectl get services -n staging | grep -E "payroll|employee|leave|notification|auth"

# 2. Verify database connectivity
psql -h payroll-db-staging -U postgres -c "SELECT version();"

# 3. Check Redis connectivity
redis-cli -h payroll-redis-staging ping

# 4. Verify RabbitMQ health
curl -u guest:guest http://rabbitmq-staging:15672/api/overview

# 5. Get auth token for testing
TOKEN=$(curl -X POST http://auth-service-staging:8001/token \
  -d "username=test_admin&password=test123" | jq -r .access_token)

# 6. Export for reuse
export PAYROLL_API="http://payroll-service-staging:8003/api/v1"
export TOKEN="$TOKEN"
export COMPANY_ID="company-staging-uuid"
```

### Test Data Setup

```sql
-- Create test employees (10 employees for smoke test)
INSERT INTO employees (id, company_id, first_name, last_name, email, designation_id, department_id)
VALUES
  ('emp-001', '{{COMPANY_ID}}', 'Test', 'Employee1', 'emp1@test.com', 'des-001', 'dept-001'),
  ('emp-002', '{{COMPANY_ID}}', 'Test', 'Employee2', 'emp2@test.com', 'des-001', 'dept-001'),
  -- ... (10 total)

-- Assign salary structures
INSERT INTO employee_salaries (employee_id, salary_structure_id, ctc, effective_from)
VALUES
  ('emp-001', 'struct-001', 1200000, '2025-04-01'),
  ('emp-002', 'struct-001', 1200000, '2025-04-01'),
  -- ... (all 10)

-- Set tax profiles
INSERT INTO employee_tax_profiles (employee_id, financial_year, tax_regime, is_metro_city)
VALUES
  ('emp-001', 2026, 'new', true),
  ('emp-002', 2026, 'new', true),
  -- ... (all 10)
```

---

## Integration Points

### Dependency Map

```
Payroll Service
├── Employee Service (lookup salary, designations)
├── Leave Service (fetch LOP days)
├── Auth Service (JWT validation)
├── Notification Service (send alerts)
├── Database (PostgreSQL)
├── Cache (Redis)
└── Message Queue (RabbitMQ)
```

### Service Communication Methods

| Service | Protocol | Auth | Timeout | Fallback |
|---------|----------|------|---------|----------|
| **Employee** | REST (HTTP) | Internal token | 10s | Cached data |
| **Leave** | REST (HTTP) | Internal token | 5s | lop_days=0 |
| **Auth** | REST (HTTP) | JWT validation | N/A | 401 Unauthorized |
| **Notification** | Event (RabbitMQ) | Internal token | 30s | Retry queue |
| **Database** | PostgreSQL | User/Pass | 30s (pool) | Connection error |
| **Cache** | Redis | None | 5s | Cache miss |

---

## Test Cases by Service

### 1. Employee Service Integration

#### TC-1.1: Fetch Employee Salary Structure

**Objective:** Verify payroll can fetch employee salary from employee service

**Setup:**
```bash
EMPLOYEE_ID="emp-001"
```

**Steps:**
```bash
# Step 1: Create payroll run
curl -X POST $PAYROLL_API/payroll/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "period_start": "2025-04-01",
    "period_end": "2025-04-30",
    "run_type": "REGULAR"
  }' | jq -r '.data.id' > run_id.txt

RUN_ID=$(cat run_id.txt)

# Step 2: Compute payroll (triggers employee-service call)
curl -X POST $PAYROLL_API/payroll/runs/$RUN_ID/compute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Expected Result:**
```json
{
  "success": true,
  "data": {
    "id": "run-uuid",
    "status": "REVIEW",
    "total_employees": 10,
    "total_gross": 12000000,
    "exception_report": {
      "errors": [],
      "warnings": []
    }
  },
  "error": null
}
```

**Verification:**
- [ ] Status = REVIEW (not DRAFT)
- [ ] total_employees > 0
- [ ] No errors in exception_report
- [ ] All employees fetched from employee service

**Logs to Check:**
```bash
kubectl logs -f deployment/payroll-service-staging | grep "employee_service"
# Expected: "Successfully fetched salary for emp-001"
```

---

#### TC-1.2: Handle Employee Service Timeout

**Objective:** Verify graceful fallback if employee-service slow/down

**Setup:**
```bash
# Temporarily disable employee service
kubectl scale deployment employee-service-staging --replicas=0

# Wait 5 seconds for timeout
sleep 5
```

**Steps:**
```bash
# Try to compute payroll
curl -X POST $PAYROLL_API/payroll/runs/$RUN_ID/compute \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Result:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Employee service not available. Cannot create payroll run."
  }
}
```

**Cleanup:**
```bash
# Re-enable employee service
kubectl scale deployment employee-service-staging --replicas=1
```

**Verification:**
- [ ] Service returns 503 Unavailable
- [ ] Error message clear to user
- [ ] Appropriate logging

---

### 2. Leave Service Integration

#### TC-2.1: Fetch LOP Days Successfully

**Objective:** Verify payroll fetches Leave of Absence data

**Setup:**
```bash
# Create some LOP records in leave service
curl -X POST http://leave-service-staging:8002/api/v1/internal/lop-summary \
  -H "x-internal-token: $INTERNAL_TOKEN" \
  -d '{
    "employee_id": "emp-001",
    "period_start": "2025-04-01",
    "period_end": "2025-04-30"
  }'
```

**Steps:**
```bash
# Compute payroll (should fetch LOP)
curl -X POST $PAYROLL_API/payroll/runs/$RUN_ID/compute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"include_lop": true}'
```

**Expected Result:**
```json
{
  "success": true,
  "data": {
    "status": "REVIEW",
    "exception_report": {
      "errors": [],
      "warnings": []
    }
  }
}
```

**Verification:**
```bash
# Check if LOP was applied in payslips
curl -X GET $PAYROLL_API/payroll/runs/$RUN_ID/payslips \
  -H "Authorization: Bearer $TOKEN" | jq '.data[0].lop_days'
# Should be > 0 for employee with LOP
```

---

#### TC-2.2: Graceful Fallback When Leave Service Unavailable

**Objective:** Verify fallback to lop_days=0 if leave-service times out

**Setup:**
```bash
# Disable leave service (or simulate timeout)
kubectl exec -it pod/payroll-service-staging -- \
  curl -X POST http://localhost:8003/test/simulate-timeout \
  -d '{"service": "leave-service", "duration": "10s"}'
```

**Steps:**
```bash
# Compute payroll
curl -X POST $PAYROLL_API/payroll/runs/$RUN_ID/compute \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Result:**
```json
{
  "success": true,
  "data": {
    "status": "REVIEW",
    "exception_report": {
      "errors": [],
      "warnings": [
        "LOP data unavailable for 10 employees (leave-service unreachable)"
      ]
    }
  }
}
```

**Verification:**
- [ ] Payroll computed despite leave-service timeout
- [ ] Warning in exception_report
- [ ] All payslips have lop_days=0
- [ ] No errors (system degraded gracefully)

---

### 3. Database Integration

#### TC-3.1: Payslip Persistence & YTD Update

**Objective:** Verify payslips and YTD correctly written to database

**Steps:**
```bash
# Process payroll (writes to DB)
curl -X POST $PAYROLL_API/payroll/runs/$RUN_ID/process \
  -H "Authorization: Bearer $TOKEN"

# Wait for processing
sleep 10

# Query database for payslips
psql -h payroll-db-staging -U postgres payroll_db -c "
  SELECT COUNT(*) as payslip_count FROM payslips 
  WHERE payroll_run_id = '$RUN_ID';"
```

**Expected Result:**
```
 payslip_count 
───────────────
           10
```

**Verification:**
```bash
# Verify YTD updated
psql -h payroll-db-staging -U postgres payroll_db -c "
  SELECT employee_id, ytd_gross FROM employee_ytd 
  WHERE financial_year = 2026 LIMIT 5;"
```

- [ ] 10 payslips created
- [ ] YTD records updated for all employees
- [ ] Payslips locked (locked_at NOT NULL)

---

#### TC-3.2: Transaction Rollback on Error

**Objective:** Verify data consistency if process fails mid-way

**Setup:**
```bash
# Create a payroll with intentional error
# (e.g., employee with negative net after deductions)
```

**Steps:**
```bash
# Try to process
curl -X POST $PAYROLL_API/payroll/runs/$RUN_ID/process \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Result:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "NEGATIVE_NET_PAY",
    "message": "Employee emp-001 has negative net pay: ₹-50,000"
  }
}
```

**Verification:**
```bash
# Verify YTD NOT updated (transaction rolled back)
psql -h payroll-db-staging -U postgres payroll_db -c "
  SELECT COUNT(*) FROM payslips WHERE payroll_run_id = '$RUN_ID';"
# Should be 0 (no partial payslips)
```

- [ ] Process failed gracefully
- [ ] No partial data written
- [ ] YTD unchanged
- [ ] Run status = FAILED

---

### 4. Cache (Redis) Integration

#### TC-4.1: Idempotency Cache

**Objective:** Verify duplicate requests return cached response

**Steps:**
```bash
# Request 1: Create payroll run
RESPONSE=$(curl -X POST $PAYROLL_API/payroll/runs \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "period_start": "2025-04-01",
    "period_end": "2025-04-30",
    "idempotency_key": "unique-key-123"
  }')

echo $RESPONSE | jq '.data.id' > run_id_1.txt

# Request 2: Duplicate request (same idempotency_key)
RESPONSE=$(curl -X POST $PAYROLL_API/payroll/runs \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "period_start": "2025-04-01",
    "period_end": "2025-04-30",
    "idempotency_key": "unique-key-123"
  }')

echo $RESPONSE | jq '.data.id' > run_id_2.txt
```

**Expected Result:**
```bash
# Should return same run ID
diff run_id_1.txt run_id_2.txt
# No output = files identical
```

**Verification:**
```bash
# Check Redis cache
redis-cli -h payroll-redis-staging GET "idempotency:unique-key-123" | jq .
# Should have cached response

# Verify only 1 run created (not 2)
psql -h payroll-db-staging -U postgres payroll_db -c "
  SELECT COUNT(*) FROM payroll_runs WHERE idempotency_key = 'unique-key-123';"
# Should be 1
```

- [ ] Second request returns cached response (no new run)
- [ ] Cache expires after 24 hours
- [ ] Both requests return 200 OK

---

### 5. Message Queue (RabbitMQ) Integration

#### TC-5.1: Event Publishing

**Objective:** Verify payroll publishes events to RabbitMQ

**Steps:**
```bash
# Monitor RabbitMQ queue
rabbitmq-admin list_queues -V localhost | grep payroll

# Create and process payroll
curl -X POST $PAYROLL_API/payroll/runs/$RUN_ID/process \
  -H "Authorization: Bearer $TOKEN"

# Check queue messages
rabbitmq-admin get_messages queues/payroll.payslips_ready
```

**Expected Result:**
```
Message received on payroll.payslips_ready:
{
  "event_type": "payroll.payslips_ready",
  "run_id": "run-uuid",
  "payslips_generated": 10,
  "timestamp": "2025-04-07T13:00:00Z"
}
```

**Verification:**
- [ ] Event published to correct queue
- [ ] Event contains correct payload
- [ ] Queue processed by subscriber (PDF worker)
- [ ] PDFs generated within 10 minutes

---

## Performance & Load Testing

### Performance Benchmarks

Target metrics (for 500 employees):

| Operation | Metric | Target | Threshold |
|-----------|--------|--------|-----------|
| **Create run** | p99 latency | 500ms | < 1s |
| **Compute payroll** | p99 latency | 30s | < 60s |
| **Process payroll** | p99 latency | 45s | < 120s |
| **Download ECR** | p99 latency | 2s | < 5s |
| **TDS calculation** | Per-employee time | 50ms | < 100ms |

### Load Test Script

```bash
#!/bin/bash
# load_test.sh - Simulate concurrent payroll operations

for i in {1..10}; do
  echo "Request $i..."
  
  # Concurrent compute requests
  curl -X POST $PAYROLL_API/payroll/runs/$RUN_ID/compute \
    -H "Authorization: Bearer $TOKEN" &
done

wait

# Monitor latency
echo "✓ All requests completed"
```

### Test Execution

```bash
# 1. Create baseline
apache2-utils 'ab' tool:
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://payroll-service-staging:8003/api/v1/payroll/runs

# 2. Monitor during test
kubectl top pod -n staging | grep payroll

# 3. Collect metrics
# Check prometheus for:
# - payroll_api_request_duration_seconds
# - payroll_compute_duration_seconds
# - payroll_database_query_duration_seconds
```

**Pass Criteria:**
- [ ] p99 latency within target
- [ ] No timeouts (503s)
- [ ] Error rate < 0.1%
- [ ] CPU usage < 80%
- [ ] Memory usage < 2GB

---

## Failure Scenario Testing

### Scenario 1: Database Connection Loss

**Simulate:**
```bash
# Kill PostgreSQL pod
kubectl delete pod -n staging payroll-db-0

# Observe: Service returns 503, retries with backoff
# Verify: Automatic reconnection after pod restarts
```

**Expected:**
- [ ] Requests fail with 503
- [ ] Automatic retry (with exponential backoff)
- [ ] Recovery after 30-60 seconds
- [ ] No data loss

---

### Scenario 2: Redis Cache Full

**Simulate:**
```bash
# Fill Redis memory
redis-cli -h payroll-redis-staging DEBUG POPULATE 100000
```

**Expected:**
- [ ] System degrades (cache misses)
- [ ] No errors (falls back to DB)
- [ ] Performance acceptable
- [ ] Recovery when cache cleared

---

### Scenario 3: RabbitMQ Queue Overload

**Simulate:**
```bash
# Disable PDF worker
kubectl scale deployment payroll-pdf-worker --replicas=0

# Process multiple payrolls
# Queue depth grows
```

**Expected:**
- [ ] Payroll processing succeeds (async PDF)
- [ ] Queue depth monitored (alert if > 1000)
- [ ] Worker recovers when restarted
- [ ] All events processed

---

## Test Sign-Off

### Pre-Production Test Report

**Date:** ________________  
**Tester:** ________________  
**Environment:** Staging  
**Build/Version:** ________________

### Test Results Summary

| Service | Test Cases | Passed | Failed | Notes |
|---------|-----------|--------|--------|-------|
| Employee Service | 2 | 2 | 0 | All lookups working |
| Leave Service | 2 | 2 | 0 | Graceful fallback verified |
| Database | 2 | 2 | 0 | Transactions atomic |
| Redis | 1 | 1 | 0 | Idempotency working |
| RabbitMQ | 1 | 1 | 0 | Events publishing |
| **Performance** | 5 | 5 | 0 | All benchmarks met |
| **Failure Scenarios** | 3 | 3 | 0 | Resilience confirmed |
| **TOTAL** | **16** | **16** | **0** | ✓ PASS |

### Sign-Off

I certify that all integration tests have been executed and passed.

**QA Engineer:** _________________________ Date: _______

**Dev Lead:** _________________________ Date: _______

**Release Manager:** _________________________ Date: _______

---

## Continuous Integration Pipeline

### Automated Tests (CI/CD)

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_DB: payroll_test
      redis:
        image: redis:6
      rabbitmq:
        image: rabbitmq:3.8

    steps:
      - uses: actions/checkout@v2
      
      - name: Run Integration Tests
        run: |
          pytest tests/integration/ -v --cov=app
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v1
```

---

## Troubleshooting Test Failures

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `ConnectionRefused` | Service not running | `kubectl get pods -n staging` |
| `TimeoutError` | Network latency | Increase timeout to 30s |
| `Authentication Failed` | Invalid token | Regenerate token via auth-service |
| `Database locked` | Transaction lock | Check for stuck connections |
| `Queue overflow` | Consumer down | Restart worker pod |

---

## Post-Test Checklist

Before marking ready for production:

- [ ] All 16 integration tests passing
- [ ] Performance benchmarks met
- [ ] Failure scenarios handled gracefully
- [ ] Logs reviewed for errors
- [ ] Database consistency verified
- [ ] Cache functioning correctly
- [ ] Events publishing to RabbitMQ
- [ ] Sign-off from QA, Dev, and Release Manager

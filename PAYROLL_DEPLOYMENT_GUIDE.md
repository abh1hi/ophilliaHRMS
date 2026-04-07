# Payroll Service Deployment Guide

**Version:** 1.0  
**Last Updated:** 2025-04-07  
**Maintainer:** DevOps Team

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Steps](#deployment-steps)
3. [Post-Deployment Verification](#post-deployment-verification)
4. [Rollback Procedures](#rollback-procedures)
5. [Configuration Management](#configuration-management)
6. [Monitoring & Alerting Setup](#monitoring--alerting-setup)

---

## Pre-Deployment Checklist

### Code & Testing
- [ ] All tests passing (`pytest tests/ -v --cov`)
- [ ] Coverage > 80% on critical paths
- [ ] Code review approved by 2+ maintainers
- [ ] Security scan passed (OWASP top 10)
- [ ] No breaking schema changes (backward compatible)

### Database
- [ ] Migration scripts written and tested in staging
- [ ] Backup of current production database created
- [ ] Rollback migration prepared
- [ ] Data validation scripts written
- [ ] Schema changes do not lock tables > 5 seconds

### Dependencies
- [ ] All Python packages pinned in requirements.txt
- [ ] No known CVEs in dependencies (`pip audit`)
- [ ] Docker image built and scanned
- [ ] Database driver version compatible

### Documentation
- [ ] API documentation updated
- [ ] Environment variables documented in .env.example
- [ ] Breaking changes noted in CHANGELOG.md
- [ ] Runbooks updated for new procedures

### Team Readiness
- [ ] On-call engineer briefed
- [ ] Rollback engineer assigned
- [ ] HR stakeholders notified of change window
- [ ] Maintenance window scheduled (off-peak)

---

## Deployment Steps

### Phase 1: Pre-Flight (5 minutes)

1. **Create maintenance window alert**
   ```bash
   # Notify all users
   curl -X POST http://notification-service:8005/alerts \
     -H "Content-Type: application/json" \
     -d '{
       "type": "MAINTENANCE",
       "title": "Payroll Service Deployment",
       "message": "Payroll functionality will be unavailable for 10 minutes starting 2025-04-07 22:00 UTC",
       "duration_minutes": 10,
       "starts_at": "2025-04-07T22:00:00Z"
     }'
   ```

2. **Verify cluster health**
   ```bash
   # Check all services running
   kubectl get pods -n ophillia | grep -E "payroll|postgres|redis|rabbitmq"
   
   # Check node health
   kubectl get nodes
   ```

3. **Backup production database**
   ```bash
   # Create timestamped backup
   pg_dump -h payroll-db -U postgres payroll_db | \
     gzip > /backups/payroll_db_$(date +%Y%m%d_%H%M%S).sql.gz
   
   # Verify backup integrity
   gunzip -c /backups/payroll_db_*.sql.gz | head -20
   ```

4. **Snapshot RabbitMQ queue state**
   ```bash
   # Dump queue definitions
   rabbitmqctl export_definitions /backups/rabbitmq_definitions_$(date +%Y%m%d_%H%M%S).json
   ```

### Phase 2: Deployment (10 minutes)

1. **Update deployment manifest**
   ```bash
   # Edit image version in deployment
   kubectl set image deployment/payroll-service \
     payroll-service=payroll-service:v1.0.0 \
     -n ophillia
   ```

2. **Monitor rolling update**
   ```bash
   # Watch pod status (should take 2-3 min)
   kubectl rollout status deployment/payroll-service -n ophillia
   
   # Check logs for errors
   kubectl logs -f deployment/payroll-service -n ophillia --tail=50
   ```

3. **Run database migrations**
   ```bash
   # Connect to payroll service pod
   kubectl exec -it pod/payroll-service-xxx -n ophillia -- bash
   
   # Inside pod:
   cd /app
   alembic upgrade head
   
   # Verify schema
   psql -h payroll-db -U postgres payroll_db -c "\dt"
   ```

4. **Clear cache**
   ```bash
   # Flush Redis cache
   redis-cli -h payroll-redis FLUSHDB
   
   # Verify empty
   redis-cli -h payroll-redis DBSIZE
   ```

### Phase 3: Validation (5 minutes)

1. **Health check**
   ```bash
   # Service is healthy if all return 200
   curl -s http://payroll-service:8003/health/ready | jq .
   curl -s http://payroll-service:8003/health/live | jq .
   ```

2. **Smoke test critical endpoints**
   ```bash
   # Test with integration token
   TOKEN=$(curl -X POST http://auth-service:8001/token \
     -d "user=admin&password=test" | jq -r .token)
   
   # Test payroll runs endpoint
   curl -H "Authorization: Bearer $TOKEN" \
     http://payroll-service:8003/api/v1/payroll/runs | jq .
   ```

3. **Database connectivity**
   ```bash
   # Query as service user
   kubectl exec -it pod/payroll-service-xxx -n ophillia -- \
     psql -h payroll-db -U payroll_service payroll_db -c "SELECT COUNT(*) FROM payroll_runs;"
   ```

4. **RabbitMQ connectivity**
   ```bash
   # Check queue status
   rabbitmqctl list_queues | grep payroll
   ```

### Phase 4: Sign-Off (2 minutes)

1. **Notify stakeholders**
   ```bash
   # Send deployment complete notification
   curl -X POST http://notification-service:8005/alerts \
     -d '{
       "type": "SUCCESS",
       "title": "Payroll Service Deployed",
       "message": "v1.0.0 deployed successfully. All systems operational."
     }'
   ```

2. **Update CHANGELOG**
   ```bash
   # Document deployment time and version
   echo "## [1.0.0] - 2025-04-07" >> CHANGELOG.md
   echo "### Deployed" >> CHANGELOG.md
   echo "- TDS calculation engine (new regime)" >> CHANGELOG.md
   ```

3. **Close maintenance window**
   ```bash
   # System back to normal
   kubectl annotate deployment payroll-service maintenance=false --overwrite
   ```

---

## Post-Deployment Verification

### Immediate (First 5 minutes)

| Check | Command | Expected | Action if Failed |
|-------|---------|----------|------------------|
| Pod status | `kubectl get pods payroll-service-*` | Running | Restart pod, check logs |
| Memory usage | `kubectl top pod payroll-service-*` | < 1GB | Check for leaks, rollback |
| CPU usage | `kubectl top pod payroll-service-*` | < 20% baseline | Scale if needed |
| Error rate | Check logs for 5xx | 0 | Investigate errors, rollback |
| Queue depth | `rabbitmqctl list_queues` | Empty | Check consumer health |

### Short-term (First hour)

1. **Monitor key metrics**
   ```bash
   # Check Prometheus for:
   # - payroll_api_request_duration_seconds (p99 < 500ms)
   # - payroll_database_query_duration_seconds (p99 < 100ms)
   # - payroll_compute_errors_total (= 0)
   # - payroll_redis_operations_seconds (p99 < 10ms)
   ```

2. **Sample user interactions**
   ```bash
   # Test each major workflow:
   # 1. Create payroll run
   # 2. Compute payroll (verify TDS calculation)
   # 3. Download report (ECR file)
   # 4. Check YTD accuracy
   ```

3. **Verify data integrity**
   ```bash
   # Run validation script
   python scripts/validate_payroll_data.py --date 2025-04-07
   
   # Expected output:
   # ✓ All payroll runs have valid status
   # ✓ All payslips have matching runs
   # ✓ TDS calculations match new regime rules
   # ✓ No orphaned records
   ```

### Long-term (First 24 hours)

1. **Monitor business metrics**
   - Total payroll runs processed
   - Average processing time
   - User error rate
   - Compliance violations

2. **Check integration status**
   - Leave service calls (success rate > 99%)
   - Employee service calls (success rate > 99%)
   - Notification service deliveries (success rate > 99%)

3. **Database performance**
   ```bash
   # Check query performance
   SELECT query, calls, mean_time 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC LIMIT 10;
   ```

---

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

Use if:
- Critical API endpoints returning 500s
- Database connectivity lost
- > 10% error rate
- Data corruption detected

**Steps:**

1. **Revert to previous deployment**
   ```bash
   kubectl rollout undo deployment/payroll-service -n ophillia
   
   # Verify old version running
   kubectl get deployment payroll-service -n ophillia -o jsonpath='{.spec.template.spec.containers[0].image}'
   ```

2. **Revert database schema (if needed)**
   ```bash
   # Inside payroll service pod:
   alembic downgrade -1
   ```

3. **Clear cache**
   ```bash
   redis-cli -h payroll-redis FLUSHDB
   ```

4. **Verify rollback**
   ```bash
   # Health check
   curl http://payroll-service:8003/health/ready
   
   # Smoke test
   curl -H "Authorization: Bearer $TOKEN" \
     http://payroll-service:8003/api/v1/payroll/runs
   ```

5. **Notify stakeholders**
   ```bash
   # Send incident notification
   curl -X POST http://slack-webhook \
     -d '{
       "text": "⚠️ Payroll deployment rolled back. v1.0.0 → v0.9.9. Investigating issue."
     }'
   ```

### Graceful Rollback (5-30 minutes)

Use if:
- Non-critical issues
- No data corruption
- Specific feature broken
- Time to fix is > 2 hours

**Steps:**

1. **Pause new payroll runs**
   ```bash
   # Set feature flag to disable run creation
   kubectl set env deployment/payroll-service \
     ALLOW_NEW_RUNS=false -n ophillia
   ```

2. **Let existing jobs complete**
   ```bash
   # Monitor running processes
   kubectl logs -f deployment/payroll-service | grep "task"
   
   # Wait for all to finish (monitor queue depth)
   rabbitmqctl list_queues | grep payroll
   ```

3. **Perform rollback**
   ```bash
   kubectl rollout undo deployment/payroll-service
   ```

4. **Re-enable new runs**
   ```bash
   kubectl set env deployment/payroll-service \
     ALLOW_NEW_RUNS=true
   ```

### Data Recovery

If data was corrupted during deployment:

1. **Stop the service**
   ```bash
   kubectl scale deployment payroll-service --replicas=0
   ```

2. **Restore from backup**
   ```bash
   # Get latest backup
   BACKUP=$(ls -t /backups/payroll_db_*.sql.gz | head -1)
   
   # Restore database
   dropdb -h payroll-db -U postgres payroll_db
   createdb -h payroll-db -U postgres payroll_db
   gunzip -c $BACKUP | psql -h payroll-db -U postgres payroll_db
   ```

3. **Run data validation**
   ```bash
   python scripts/validate_payroll_data.py --repair
   ```

4. **Restart service**
   ```bash
   kubectl scale deployment payroll-service --replicas=3
   ```

---

## Configuration Management

### Environment Variables

**Required:**
```
# Database
DATABASE_URL=postgresql://payroll_service:password@payroll-db:5432/payroll_db

# Cache
REDIS_URL=redis://payroll-redis:6379/0

# Message Queue
RABBITMQ_URL=amqp://guest:guest@payroll-rabbitmq:5672/

# Services
AUTH_SERVICE_URL=http://auth-service:8001
LEAVE_SERVICE_URL=http://leave-service:8002
EMPLOYEE_SERVICE_URL=http://employee-service:8000
NOTIFICATION_SERVICE_URL=http://notification-service:8005

# Security
JWT_SECRET_KEY=<from secrets manager>
INTERNAL_SERVICE_TOKEN=<from secrets manager>

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Optional:**
```
# Timeouts (seconds)
LEAVE_SERVICE_TIMEOUT=5
EMPLOYEE_SERVICE_TIMEOUT=10
DATABASE_POOL_TIMEOUT=30

# Limits
MAX_PAYROLL_RUN_SIZE=10000
MAX_CONCURRENT_COMPUTES=5
IDEMPOTENCY_CACHE_TTL_HOURS=24

# Features
ENABLE_TDS_CALCULATION=true
ENABLE_LWF_DEDUCTION=true
ENABLE_PDF_GENERATION=true
```

### Secrets Management

**Store in HashiCorp Vault or AWS Secrets Manager:**

```bash
# Create secret
vault kv put secret/payroll/db \
  username=payroll_service \
  password=<secure-password>

# Reference in deployment
valueFrom:
  secretKeyRef:
    name: payroll-secrets
    key: db-password
```

---

## Monitoring & Alerting Setup

### Prometheus Metrics

**Critical metrics to monitor:**

```yaml
# alerting_rules.yml
groups:
  - name: payroll
    rules:
      # API health
      - alert: PayrollAPIErrorRate
        expr: rate(payroll_api_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
      
      # Database health
      - alert: PayrollDatabaseLatency
        expr: payroll_database_query_duration_seconds{quantile="0.99"} > 0.5
        for: 10m
        labels:
          severity: warning
      
      # Queue depth
      - alert: PayrollQueueDepth
        expr: rabbitmq_queue_messages{queue=~"payroll.*"} > 1000
        for: 15m
        labels:
          severity: warning
      
      # Memory usage
      - alert: PayrollServiceMemory
        expr: container_memory_usage_bytes{pod=~"payroll.*"} > 2000000000
        for: 5m
        labels:
          severity: warning
```

### Log Aggregation

**Configure ELK Stack or Datadog:**

```json
// Example: Datadog dashboard
{
  "dashboard_title": "Payroll Service Health",
  "widgets": [
    {
      "type": "timeseries",
      "queries": [
        {
          "query": "avg:payroll.api.request_duration{*}",
          "label": "API Latency (p99)"
        }
      ]
    },
    {
      "type": "query_value",
      "queries": [
        {
          "query": "sum:payroll.errors{*}.as_count()",
          "label": "Total Errors (24h)"
        }
      ]
    }
  ]
}
```

### Health Check Endpoints

**Implement in service:**

```python
@app.get("/health/live")
async def liveness():
    """Pod is alive (Kubernetes liveness probe)"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """Pod is ready to serve traffic (Kubernetes readiness probe)"""
    # Check database connection
    # Check Redis connection
    # Check RabbitMQ connection
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "redis": "ok",
            "rabbitmq": "ok"
        }
    }
```

**Kubernetes probes:**

```yaml
spec:
  containers:
  - name: payroll-service
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8003
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8003
      initialDelaySeconds: 10
      periodSeconds: 5
```

---

## Troubleshooting Common Issues

### Issue: TDS Calculation Incorrect

**Symptoms:** Employees reporting wrong TDS deduction

**Root Cause:** Tax slab or regime configuration incorrect

**Fix:**
1. Verify `TAX_SLABS_NEW_2025_26` in code matches current law
2. Verify employee's `tax_regime` is correctly set
3. Check `standard_deduction` amount (should be ₹75,000 for new regime)
4. Re-run compute on affected run (doesn't affect already-locked payslips)

### Issue: Leave Service Timeout

**Symptoms:** LOP data showing 0 for all employees, warnings in exception report

**Root Cause:** Leave service is slow or down

**Expected behavior:** Falls back gracefully with warning

**No action needed** — system designed to handle this. HR can manually override LOP if needed.

### Issue: Negative Net Salary

**Symptoms:** Process fails with "NEGATIVE_NET_PAY" error

**Root Cause:** Deductions exceed gross (salary error or over-deduction)

**Fix:**
1. Review employee's salary structure
2. Check for manual deductions (arrears, loans, advances)
3. Verify pro-rata calculation if mid-month join
4. Reject payroll, correct, and recompute

---

## Deployment Checklist Summary

- [ ] Pre-flight checklist completed
- [ ] Database backup created and verified
- [ ] Maintenance window notified to users
- [ ] Deployment completed successfully
- [ ] All health checks passing
- [ ] Smoke tests successful
- [ ] Metrics and logs normal
- [ ] Stakeholders notified
- [ ] Documentation updated
- [ ] On-call engineer briefed

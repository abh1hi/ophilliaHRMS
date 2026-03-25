# 04 — Deployment Failure Scenarios

---

### Scenario DEP1: Bad Deployment (Breaking Change)

**Trigger:** Code bug in new release, incompatible API change, broken dependency

**Timeline:**
1. `T+0s` — `docker-compose up --build -d` pulls new code
2. `T+30s` — New container image built, old container stopped
3. `T+30s` — New container starts, runs entrypoint: `alembic upgrade head && uvicorn start`
4. `T+31s` — Application crashes on startup (bad import, missing env var, syntax error)
5. `T+31s` — Container exits, Docker restarts (unless-stopped)
6. `T+32s` — Restart loop begins (see Scenario C2)
7. `T+32s` — Service unavailable, health check failing
8. `T+?` — Manual rollback required

**System Behavior:**
- Docker Compose `--build` replaces the image — old image may still exist locally
- No built-in rollback mechanism in Docker Compose
- Other services: unaffected if they don't depend on the broken service's API
- Database: migrations may have already run (irreversible DDL changes)

**User Impact:**
- If auth-service: system-wide impact (no new logins)
- If other service: module-specific outage
- Duration: until manual rollback or fix deployed

**Data Safety:**
- If migration ran successfully before app crash: DB schema is updated
- Risk: new schema without matching code = API errors on that table
- If migration was DDL-only (ADD COLUMN): backward compatible, low risk
- If migration was destructive (DROP COLUMN, RENAME): data at risk

**Recovery Steps:**
```bash
# 1. Stop the broken service
docker stop hrms-<service>

# 2. Rollback to previous image (if available)
docker-compose up -d --no-build <service>  # Uses cached image

# 3. If migration needs rollback
docker exec hrms-<service> alembic downgrade -1

# 4. Verify
docker logs hrms-<service> --tail 50
```

**Best Case:** App crash on startup, no migration ran. Rollback by reverting code and rebuilding.
**Worst Case:** Destructive migration ran, app crashes. Data schema and code are now mismatched. Requires forward-fix or complex migration rollback.

---

### Scenario DEP2: Partial Deployment (Some Services Updated, Others Not)

**Trigger:** Deploying one service without updating its dependents, interrupted deployment

**Timeline:**
1. `T+0s` — Auth-service updated with new API response format
2. `T+0s` — Employee-service still running old code expecting old format
3. `T+0s` — Employee-service calls auth-service internal API
4. `T+0s` — Response parsing fails (unexpected field, missing field, type change)
5. `T+0s` — Employee-service returns 500 for affected endpoints

**System Behavior:**
- No API versioning enforced between services (all use `/api/v1/`)
- No contract testing between services
- Internal service tokens (INTERNAL_SERVICE_TOKEN) don't verify API compatibility
- Each service independently consumes auth-service's JWT public key (compatible as long as key unchanged)

**Inter-Service Call Points:**
| Caller | Callee | Method | Risk |
|--------|--------|--------|------|
| Employee → Auth | User validation | HTTP | API contract change |
| Attendance → Employee | Employee lookup | HTTP | API contract change |
| Leave → Employee | Employee verification | HTTP | API contract change |
| Payroll → Employee | Employee salary lookup | HTTP | API contract change |
| Notification → Auth | User email lookup | HTTP | API contract change |

**User Impact:** Subtle — some features work, others fail. Hard to diagnose. E.g., "I can log in but I can't create an employee" (because employee-service fails to validate with updated auth-service).

**Data Safety:** Generally safe. Failed API calls don't write partial data.

**Best Case:** Breaking change is minor (added field). Old code ignores new fields. No impact.
**Worst Case:** Breaking change to shared data format. Multiple services fail. Requires full coordinated deployment.

**Mitigation Required:**
- Deploy all services atomically: `docker-compose up --build -d` (rebuilds everything)
- Or implement API versioning (`/api/v1/`, `/api/v2/`) with backward compatibility period

---

### Scenario DEP3: Schema Mismatch (DB vs Service Code)

**Trigger:** Migration runs but code rollback happens, or migration fails halfway

**Timeline (Migration Fails Halfway):**
1. `T+0s` — Service starts, runs `alembic upgrade head`
2. `T+2s` — Migration 0003 begins: `ALTER TABLE employees ADD COLUMN new_field...`
3. `T+3s` — Migration 0003 succeeds (DDL committed immediately in PostgreSQL)
4. `T+3s` — Migration 0004 begins: `ALTER TABLE employees ALTER COLUMN old_field...`
5. `T+4s` — Migration 0004 fails (e.g., data type incompatibility)
6. `T+4s` — Alembic marks 0003 as applied but 0004 not applied
7. `T+4s` — Application startup proceeds with entrypoint
8. `T+5s` — Application code expects 0004 schema — queries fail

**System Behavior:**
- Alembic migration tracking (`alembic_version` table) records last successful revision
- PostgreSQL DDL is auto-committed (not wrapped in transaction for most ALTER TABLE)
- Partial schema state: some columns/tables from 0003 exist, 0004 changes don't
- Application ORM expects final schema — `column not found` or `wrong type` errors

**Critical PostgreSQL DDL Behavior:**
```
ALTER TABLE ... ADD COLUMN     → Auto-committed, cannot rollback
ALTER TABLE ... DROP COLUMN    → Auto-committed, cannot rollback
ALTER TABLE ... ALTER TYPE     → Auto-committed, cannot rollback
CREATE INDEX CONCURRENTLY      → Cannot run inside transaction
```

**User Impact:** Service fails on any query touching affected table. May work for other tables.

**Data Safety:**
- Existing data: SAFE (columns added, not modified)
- If DROP COLUMN ran: DATA LOST for that column (irreversible)
- Schema inconsistency between alembic_version and actual DB state

**Recovery:**
```bash
# 1. Check current migration state
docker exec hrms-db psql -U postgres -d employee_db \
  -c "SELECT version_num FROM alembic_version;"

# 2. Check actual schema
docker exec hrms-db psql -U postgres -d employee_db \
  -c "\d employees"

# 3. Either:
# a) Fix and re-run failed migration
docker exec hrms-employee alembic upgrade head

# b) Stamp the version to match actual state
docker exec hrms-employee alembic stamp <revision_id>

# c) Manually fix schema to match code
docker exec hrms-db psql -U postgres -d employee_db \
  -c "ALTER TABLE employees ..."
```

**Best Case:** Failed migration was additive (ADD COLUMN). Easy to retry.
**Worst Case:** Failed migration was destructive and partially applied. Manual schema surgery required.

---

## Deployment Safety Checklist

Before any deployment:

```
□ All services using compatible API contracts?
□ Database migrations backward-compatible?
□ Old code can work with new schema? (deploy DB first, then code)
□ New code can work with old schema? (deploy code first, then DB)
□ Rollback plan documented?
□ Database backup taken?
□ Health check endpoints tested?
□ .env.docker files match required environment variables?
```

### Safe Deployment Order

```
1. Take database backup
2. Run migrations FIRST (additive only: ADD COLUMN, CREATE TABLE)
   docker exec hrms-<service> alembic upgrade head
3. Deploy infrastructure changes (docker-compose.yml)
4. Deploy backend services (one at a time, verify health)
5. Deploy frontend (last — it calls the APIs)
6. Verify all health endpoints return "healthy"
7. Run smoke tests on critical paths (login, employee CRUD)
```

### Migration Safety Rules

| Operation | Safe to Deploy? | Rollback Possible? |
|-----------|----------------|-------------------|
| ADD COLUMN (nullable) | Yes | Yes (DROP COLUMN) |
| ADD COLUMN (NOT NULL + default) | Yes | Yes |
| CREATE TABLE | Yes | Yes (DROP TABLE) |
| CREATE INDEX | Yes (CONCURRENTLY) | Yes (DROP INDEX) |
| DROP COLUMN | DANGEROUS | NO — data lost |
| RENAME COLUMN | DANGEROUS | Requires code change |
| ALTER TYPE | RISKY | May fail with existing data |
| DROP TABLE | DANGEROUS | NO — data lost |

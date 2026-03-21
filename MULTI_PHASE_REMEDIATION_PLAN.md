# OphilliaHRMS — Multi-Phase Remediation Plan

**Created**: 2026-03-20
**Status**: Planning
**Scope**: Fix all gaps identified during contract audit — data integrity, security, API completeness, and architecture.

---

## Phase Overview

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
 Tenant      Security    API         Features    Polish
 Isolation   Hardening   Completeness            & Docs

 ~3 days     ~2 days     ~2 days     ~2 days     ~1 day
```

Total estimated effort: ~10 working days

---

## Phase 1: Multi-Tenant Isolation (CRITICAL)

**Goal**: Every service scopes all data by `company_id`. No cross-tenant data leakage.

**Why first**: This is a data integrity and privacy issue. Everything else is pointless if tenant A can see tenant B's data.

### 1A — Attendance Service
| Task | Details |
|------|---------|
| Add `company_id` column to `attendance_records` model | UUID, not null, indexed |
| Add `company_id` column to `geofence_locations` model | UUID, not null, indexed |
| Add `company_id` column to `attendance_policies` model | UUID, not null, indexed |
| Add `company_id` column to `attendance_tasks` model | UUID, not null, indexed |
| Create Alembic migration `0004_add_tenant_isolation` | Add columns to all 4 tables |
| Add `get_db_with_tenant` dependency (copy from employee-service) | Extract company_id from JWT into session |
| Update all repository classes with `_scoped()` pattern | Auto-filter + auto-set company_id |
| Update all endpoint handlers to use `get_db_with_tenant` | Replace raw `get_db` |
| Update response schemas to include `company_id` | Visible in API responses |

### 1B — Leave Service (parallel with 1A)
| Task | Details |
|------|---------|
| Add `company_id` to `leave_requests` model | UUID, not null, indexed |
| Add `company_id` to `leave_types` model | UUID, not null, indexed |
| Add `company_id` to `leave_balances` model | UUID, not null, indexed |
| Add `company_id` to `holidays` model | UUID, not null, indexed |
| Create Alembic migration | Add columns to all 4 tables |
| Add `get_db_with_tenant` dependency | Same pattern as employee-service |
| Update all repository classes with tenant scoping | `_scoped()` on every query |
| Update endpoint handlers | Use `get_db_with_tenant` |
| Make leave type `name` unique per company, not globally | Remove global unique constraint |

### 1C — Payroll Service (parallel with 1A, 1B)
| Task | Details |
|------|---------|
| Add `company_id` to `payroll_runs` model | UUID, not null, indexed |
| Add `company_id` to `payslips` model | UUID, not null, indexed |
| Add `company_id` to `salary_structures` model | UUID, not null, indexed |
| Add `company_id` to `employee_salaries` model | UUID, not null, indexed |
| Create Alembic migration | Add columns to all 4 tables |
| Add `get_db_with_tenant` dependency | Same pattern |
| Update all repositories with tenant scoping | `_scoped()` pattern |
| Update endpoint handlers | Use `get_db_with_tenant` |

### 1D — Students Service (parallel with 1A, 1B, 1C)
| Task | Details |
|------|---------|
| Verify `company_id` exists on `students`, `classes`, `guardians` models | Add if missing |
| Add `get_db_with_tenant` dependency | Same pattern |
| Update all repositories with tenant scoping | `_scoped()` pattern |
| Update endpoint handlers | Use `get_db_with_tenant` |

### 1E — Notification Service (parallel with above)
| Task | Details |
|------|---------|
| Add `company_id` to `notification_logs` model | UUID, not null, indexed |
| Add `company_id` to `notification_preferences` model | UUID, not null, indexed |
| Create Alembic migration | Add columns |
| Update repository queries with tenant scoping | Filter by company_id |

### 1F — Event Payload Standardization
| Task | Details |
|------|---------|
| Add `company_id` to all RabbitMQ event payloads across all publishers | attendance, leave, payroll, students |
| Update audit-service event consumer to index `company_id` | Already has the column, just needs to extract it |

### Phase 1 Testing (run in parallel as each service completes)

```
Test Matrix — run per service:
┌─────────────────────────────────────────────────────┐
│ 1. Create two companies (Company A, Company B)      │
│ 2. Create users in each company                     │
│ 3. Create data (employees/attendance/etc) in each   │
│ 4. Login as Company A user                          │
│ 5. Verify: can see Company A data                   │
│ 6. Verify: CANNOT see Company B data                │
│ 7. Verify: create auto-sets correct company_id      │
│ 8. Verify: events include company_id in payload     │
└─────────────────────────────────────────────────────┘
```

**Parallel test commands**:
```bash
# Terminal 1: Test attendance isolation
python tests_live/test_tenant_isolation_attendance.py

# Terminal 2: Test leave isolation
python tests_live/test_tenant_isolation_leave.py

# Terminal 3: Test payroll isolation
python tests_live/test_tenant_isolation_payroll.py

# Terminal 4: Test students isolation
python tests_live/test_tenant_isolation_students.py
```

**Definition of Done**: Zero cross-tenant data leakage in any service.

---

## Phase 2: Security Hardening

**Goal**: Close authentication/authorization gaps. No unauthenticated writes, no privilege escalation.

**Depends on**: Phase 1 (tenant isolation must be in place first)

### 2A — Secure Company Registration
| Task | Details |
|------|---------|
| Add rate limiting to `POST /auth/companies` | 3/hour per IP |
| Option A: Require Super Admin auth for company creation | Most restrictive |
| Option B: Add invitation-code flow for self-service signup | For SaaS onboarding |
| Decision: Choose one based on deployment model | Document the choice |

### 2B — JWT Blacklist Propagation
| Task | Details |
|------|---------|
| Add Redis-based token blacklist check to employee-service `get_current_user` | Check `jti` against Redis |
| Add same check to attendance-service | Same implementation |
| Add same check to leave-service | Same implementation |
| Add same check to payroll-service | Same implementation |
| Add same check to students-service | Same implementation |
| Add same check to notification-service | Same implementation |
| Share Redis connection config across all services | Use existing `hrms-redis` container |

**Implementation pattern** (add to each service's `security.py`):
```python
async def is_blacklisted(jti: str) -> bool:
    redis = get_redis()  # shared connection
    return await redis.exists(f"blacklist:{jti}")
```

### 2C — RBAC Fixes
| Task | Details |
|------|---------|
| Employee service: Allow HR role on create/update/deactivate endpoints | Code currently only allows Super Admin |
| Department service: Allow HR role on create/update endpoints | Same fix |
| Attendance tasks/assign: Add manager relationship check | Prevent arbitrary task assignment |

### 2D — Cross-Service Reference Validation
| Task | Details |
|------|---------|
| Attendance service: Verify `employee_id` belongs to same company before storing | On clock-in, manual entry, school-mode |
| Leave service: Verify `employee_id` belongs to same company | On leave request, balance creation |
| Payroll service: Verify `employee_id` belongs to same company | On salary assignment, payroll run |

### Phase 2 Testing

```
Security Test Matrix:
┌──────────────────────────────────────────────────────────┐
│ 1. Logout user → try using old JWT on each service      │
│    Expected: 401 on all services (blacklist works)       │
│                                                          │
│ 2. Employee-role user → try create employee              │
│    Expected: 403 Forbidden                               │
│                                                          │
│ 3. Company A user → try referencing Company B employee   │
│    Expected: 404 Not Found (scoped query returns nothing)│
│                                                          │
│ 4. Unauthenticated → POST /companies (if secured)       │
│    Expected: 401 or rate-limited                         │
│                                                          │
│ 5. Non-manager → assign task to another employee         │
│    Expected: 403 Forbidden                               │
└──────────────────────────────────────────────────────────┘
```

**Definition of Done**: All security tests pass. No privilege escalation paths.

---

## Phase 3: API Completeness

**Goal**: Add missing CRUD operations and the SELECT_COMPANY flow. No dead-end entities.

**Depends on**: Phase 1 (tenant isolation), Phase 2 (auth fixes)

### 3A — Auth Service: Company Management
| Task | Details |
|------|---------|
| `PATCH /auth/companies/{id}` | Update company name/domain. Super Admin only. |
| `DELETE /auth/companies/{id}` (soft delete) | Set `is_active = false`. Super Admin only. |
| `POST /auth/select-company` | Set active company in session/JWT for multi-company admins |
| Update `post-login-context` to handle inactive companies | Filter out `is_active = false` |

### 3B — Frontend: Select Company Flow
| Task | Details |
|------|---------|
| Create `SelectCompanyPage.vue` | List companies, click to select, redirect to dashboard |
| Update router with `/select-company` route | With onboarding guard |
| Update auth store with `selectCompany()` action | Calls `POST /auth/select-company` |

### 3C — Leave Service: Missing CRUD
| Task | Details |
|------|---------|
| `PATCH /leave/leave-types/{id}` | Update leave type (name, days, active status) |
| `DELETE /leave/leave-types/{id}` | Soft delete (set `is_active = false`) |
| `PATCH /leave/leave-balances/{id}` | Adjust balances manually (HR correction) |

### 3D — Payroll Service: Missing CRUD
| Task | Details |
|------|---------|
| `PATCH /salary/structures/{id}` | Update structure percentages |
| `DELETE /salary/structures/{id}` | Soft delete (add `is_active` flag) |
| `GET /salary/employee/{employee_id}/history` | Salary history (all records, not just active) |

### 3E — Attendance Service: Missing CRUD
| Task | Details |
|------|---------|
| `PATCH /attendance/geofences/{id}` | Update geofence name/coords/radius |
| `DELETE /attendance/geofences/{id}` | Soft delete (set `is_active = false`) |
| `PATCH /attendance/policies/{id}` | Update policy method/times |
| `DELETE /attendance/policies/{id}` | Hard delete (policies are config, not data) |

### 3F — Pagination Gaps
| Task | Details |
|------|---------|
| Add pagination to `GET /salary/structures` | skip/limit params |
| Add pagination to `GET /payroll/runs` | skip/limit params |
| Add pagination to `GET /notifications/logs` | skip/limit params |
| Add pagination to `GET /leave/holidays` | skip/limit params |
| Add pagination to `GET /attendance/geofences` | skip/limit params |
| Add pagination to `GET /attendance/policies` | skip/limit params |

### Phase 3 Testing

```
API Completeness Test Matrix:
┌─────────────────────────────────────────────────────────┐
│ For each new endpoint:                                  │
│ 1. Happy path — valid request returns expected response │
│ 2. Auth — unauthenticated request returns 401           │
│ 3. RBAC — wrong role returns 403                        │
│ 4. Not found — invalid ID returns 404                   │
│ 5. Validation — bad input returns 422                   │
│ 6. Tenant — only affects own company data               │
│                                                         │
│ SELECT_COMPANY flow:                                    │
│ 1. Login as Super Admin with 3 companies                │
│ 2. Verify post-login-context returns SELECT_COMPANY     │
│ 3. Select company → verify dashboard loads              │
│ 4. Verify all subsequent API calls use selected company │
└─────────────────────────────────────────────────────────┘
```

**Definition of Done**: All entities have full CRUD. No orphaned data paths.

---

## Phase 4: Feature Enhancements

**Goal**: Add operational features that improve day-to-day usability.

**Depends on**: Phase 3 (API completeness)

### 4A — Soft Delete Pattern Standardization
| Task | Details |
|------|---------|
| Add `is_active` flag to `departments` model | Default true |
| Add `is_active` flag to `salary_structures` model | Default true |
| Add `is_active` flag to `leave_types` model (verify exists) | Default true |
| Update all list queries to filter `is_active = true` by default | Add `include_inactive` query param for admin |

### 4B — Bulk Operations
| Task | Details |
|------|---------|
| `POST /employees/bulk` | CSV/JSON import of multiple employees |
| `POST /leave/leave-balances/bulk` | Allocate balances for all employees of a leave type + year |
| `POST /attendance/school-mode/bulk` | Mark attendance for multiple employees at once |

### 4C — Health Check Standardization
| Task | Details |
|------|---------|
| Standardize health check response format across all services | `{status, service, version, checks: {database, rabbitmq}}` |
| Add RabbitMQ health check to services that currently skip it | attendance, leave, payroll, students |
| Add Redis health check to auth-service | It uses Redis for blacklist |

### 4D — Rate Limiting
| Task | Details |
|------|---------|
| Add rate limiting to employee-service write endpoints | 30/min per user |
| Add rate limiting to attendance clock-in/out | 5/min per user (prevent abuse) |
| Add rate limiting to leave request creation | 10/min per user |

### Phase 4 Testing

```
Feature Test Matrix:
┌──────────────────────────────────────────────────────┐
│ Soft deletes:                                        │
│ 1. Delete entity → verify is_active = false          │
│ 2. List endpoint → verify deleted entity hidden      │
│ 3. List with include_inactive=true → verify visible  │
│                                                      │
│ Bulk operations:                                     │
│ 1. Upload valid CSV → all records created            │
│ 2. Upload CSV with errors → partial success + report │
│ 3. Upload 1000+ rows → completes within timeout      │
│                                                      │
│ Health checks:                                       │
│ 1. All services up → all return healthy              │
│ 2. Kill DB → services report db: disconnected        │
│ 3. Kill RabbitMQ → services report rabbitmq: down    │
│                                                      │
│ Rate limiting:                                       │
│ 1. Send N+1 requests → Nth+1 returns 429             │
│ 2. Wait for window reset → requests succeed again    │
└──────────────────────────────────────────────────────┘
```

**Definition of Done**: All features work. Health checks are reliable.

---

## Phase 5: Polish, Contracts & Documentation

**Goal**: Update all contracts to match reality. Clean up tech debt.

**Depends on**: Phase 4

### 5A — Contract Updates
| Task | Details |
|------|---------|
| Update all 8 service contracts to v3 | Reflect all new endpoints, schemas, tenant fields |
| Update `SERVICE_AUTH_INTEGRATION_GUIDE.md` | Add blacklist check instructions, tenant dependency |
| Add gateway contract | Document all nginx route mappings |

### 5B — API Versioning Preparation
| Task | Details |
|------|---------|
| Document v1 API freeze policy | No breaking changes after this point |
| Add `Deprecation` header support to gateway | For future v2 migration |

### 5C — Integration Test Suite
| Task | Details |
|------|---------|
| Create end-to-end test: full user lifecycle | Register company → register user → login → create employee → clock in → apply leave → run payroll → logout |
| Create cross-service test: event flow | Employee created → audit log appears → notification sent |
| Create tenant isolation stress test | 10 companies, 100 users, verify zero leakage |

### 5D — Cleanup
| Task | Details |
|------|---------|
| Remove any unused imports/dead code found during audit | Per-service cleanup |
| Verify all Alembic migration chains are linear and clean | No broken `down_revision` pointers |
| Verify all `.env.docker` files have consistent variable names | Standardize across services |

---

## Parallel Execution Map

```
Week 1:
┌──────────────────────────────────────────────────────────────┐
│ Day 1-2: Phase 1A-1E (all 5 services in parallel)           │
│                                                              │
│   Dev 1: attendance-service tenant isolation                 │
│   Dev 2: leave-service tenant isolation                      │
│   Dev 3: payroll-service tenant isolation                    │
│   Dev 4: students-service + notification-service             │
│                                                              │
│ Day 2: Phase 1F (event standardization — after services done)│
│                                                              │
│ Day 2-3: Phase 1 Testing (parallel per service)              │
│          + Phase 2A-2B start (security — independent work)   │
│                                                              │
│ Day 3: Phase 2C-2D (RBAC fixes + cross-service validation)  │
│                                                              │
│ Day 3: Phase 2 Testing                                       │
└──────────────────────────────────────────────────────────────┘

Week 2:
┌──────────────────────────────────────────────────────────────┐
│ Day 4-5: Phase 3A-3F (API completeness — parallelizable)    │
│                                                              │
│   Dev 1: Auth company CRUD + select-company backend          │
│   Dev 2: Leave + Payroll missing CRUD                        │
│   Dev 3: Attendance missing CRUD + pagination                │
│   Dev 4: Frontend SelectCompanyPage                          │
│                                                              │
│ Day 5: Phase 3 Testing                                       │
│                                                              │
│ Day 6-7: Phase 4A-4D (features — parallelizable)            │
│                                                              │
│   Dev 1: Soft delete standardization                         │
│   Dev 2: Bulk operations                                     │
│   Dev 3: Health checks + rate limiting                       │
│                                                              │
│ Day 7: Phase 4 Testing                                       │
│                                                              │
│ Day 8: Phase 5 (polish + final contracts + integration tests)│
└──────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy

### Test Levels

| Level | When | What |
|-------|------|------|
| Unit tests | During development | Repository scoping, model validations |
| Service tests | After each phase task | Single service endpoint correctness |
| Integration tests | After each phase | Cross-service flows (events, auth) |
| Tenant isolation tests | After Phase 1 | Multi-company data separation |
| Security tests | After Phase 2 | Auth bypass, privilege escalation |
| End-to-end tests | After Phase 5 | Full user lifecycle |

### Parallel Test Execution

```bash
# Run all service tests in parallel (one terminal per service)
docker compose --profile core --profile hr --profile student up -d

# Terminal 1
pytest services/attendance-service/tests/ -v --tb=short

# Terminal 2
pytest services/leave-service/tests/ -v --tb=short

# Terminal 3
pytest services/payroll-service/tests/ -v --tb=short

# Terminal 4
pytest services/employee-service/tests/ -v --tb=short

# Terminal 5
pytest services/students-service/tests/ -v --tb=short

# Terminal 6 — cross-service integration
pytest tests_live/ -v --tb=short
```

### Regression Gate

Before merging any phase:
1. All existing tests pass
2. New tests pass
3. Tenant isolation test passes (after Phase 1)
4. Security test suite passes (after Phase 2)
5. Manual smoke test of login → dashboard flow

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing data has NULL company_id after migration | Queries break with NOT NULL constraint | Migration must backfill: assign existing rows to a default company before adding NOT NULL |
| Redis unavailable breaks JWT blacklist check | All services reject valid tokens | Make blacklist check fail-open (log warning, allow request) with circuit breaker |
| Bulk import timeout on large datasets | 504 Gateway Timeout | Use async task queue (RabbitMQ) for bulk operations, return job ID |
| Breaking API changes during Phase 3 | Frontend crashes | Version new endpoints, keep old ones working until frontend updated |

---

## Success Criteria

- [ ] Zero cross-tenant data leakage (Phase 1)
- [ ] Logged-out JWT rejected by all services within 1 second (Phase 2)
- [ ] All entities have full CRUD lifecycle (Phase 3)
- [ ] Health checks report actual dependency status (Phase 4)
- [ ] All 9 service contracts match implementation (Phase 5)
- [ ] End-to-end test passes: company creation → payroll run (Phase 5)

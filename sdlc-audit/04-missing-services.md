# Missing HRMS Services

Comparison against a complete enterprise HRMS domain model reveals the following services that are **not yet implemented** but required for a production-ready platform.

---

## Tier 1: Core Missing Services (Required for MVP+)

### 1. Organization Service

**Why Needed:** Currently departments are flat entities in the employee service with no hierarchy, no org chart, and no organizational structure modeling.

**Responsibilities:**
- Organization hierarchy (company → division → department → team)
- Org chart generation and traversal
- Reporting relationships (who reports to whom)
- Cost center management
- Location/branch management
- Department budgets and headcount caps

**Key APIs:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/org/units` | Create organizational unit |
| GET | `/org/units/tree` | Get full org tree |
| GET | `/org/units/{id}/children` | Get direct children |
| GET | `/org/units/{id}/ancestors` | Get ancestors to root |
| PUT | `/org/units/{id}` | Update unit |
| POST | `/org/units/{id}/move` | Move unit in hierarchy |
| GET | `/org/reporting-chain/{employee_id}` | Get reporting chain |
| POST | `/org/locations` | CRUD for locations/branches |
| GET | `/org/headcount/{unit_id}` | Headcount summary |

**Domain Ownership:**
- Organizational units (hierarchy)
- Reporting relationships
- Cost centers
- Locations/branches

---

### 2. Recruitment / ATS Service

**Why Needed:** No talent acquisition pipeline exists. Companies cannot post jobs, receive applications, or track candidates.

**Responsibilities:**
- Job posting lifecycle (draft → published → closed)
- Application tracking (applied → screening → interview → offer → hired/rejected)
- Interview scheduling and feedback
- Offer management
- Candidate database
- Job board integrations (Indeed, LinkedIn)
- Careers page API

**Key APIs:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/recruitment/jobs` | Create job posting |
| GET | `/recruitment/jobs` | List jobs (filters: status, department) |
| PUT | `/recruitment/jobs/{id}` | Update job |
| POST | `/recruitment/jobs/{id}/publish` | Publish to job boards |
| POST | `/recruitment/applications` | Submit application |
| GET | `/recruitment/applications` | List applications (pipeline view) |
| PATCH | `/recruitment/applications/{id}/stage` | Move to next stage |
| POST | `/recruitment/interviews` | Schedule interview |
| POST | `/recruitment/offers` | Create offer letter |
| POST | `/recruitment/offers/{id}/accept` | Accept offer → trigger onboarding |

**Domain Ownership:**
- Job postings
- Applications & candidates
- Interview records
- Offers
- Recruitment pipeline stages

---

### 3. Performance Management Service

**Why Needed:** No mechanism to track employee performance, set goals, conduct reviews, or manage appraisals.

**Responsibilities:**
- Goal/OKR setting and tracking
- Performance review cycles (quarterly/annual)
- 360-degree feedback collection
- Self-assessments
- Manager assessments
- Performance ratings and calibration
- Performance Improvement Plans (PIPs)

**Key APIs:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/performance/goals` | Set employee goal |
| GET | `/performance/goals` | List goals (employee/team) |
| PATCH | `/performance/goals/{id}/progress` | Update goal progress |
| POST | `/performance/reviews/cycles` | Create review cycle |
| GET | `/performance/reviews/cycles` | List review cycles |
| POST | `/performance/reviews` | Submit review |
| GET | `/performance/reviews/{employee_id}` | Get employee reviews |
| POST | `/performance/feedback/360` | Submit 360 feedback |
| POST | `/performance/pips` | Create PIP |
| GET | `/performance/ratings/calibration` | Calibration view |

**Domain Ownership:**
- Goals/OKRs
- Review cycles
- Performance reviews
- Feedback records
- PIPs
- Ratings

---

### 4. Reporting & Analytics Service

**Why Needed:** No cross-service reporting, dashboards, or analytics capabilities exist. Each service only returns its own data.

**Responsibilities:**
- Cross-service data aggregation
- Dashboard KPIs (headcount, attrition, attendance rate, payroll summary)
- Scheduled report generation
- Custom report builder
- Export (PDF, Excel, CSV)
- Real-time metrics computation

**Key APIs:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/reports/dashboard/hr` | HR dashboard KPIs |
| GET | `/reports/dashboard/admin` | Admin overview |
| GET | `/reports/headcount` | Headcount by dept/location/status |
| GET | `/reports/attrition` | Attrition rate and trends |
| GET | `/reports/attendance/summary` | Attendance rate aggregation |
| GET | `/reports/payroll/summary` | Payroll cost by department |
| GET | `/reports/leave/utilization` | Leave utilization report |
| POST | `/reports/custom` | Custom report query |
| GET | `/reports/{id}/export` | Export as PDF/Excel |
| POST | `/reports/scheduled` | Schedule recurring report |

**Domain Ownership:**
- Report definitions
- Scheduled reports
- Dashboard configurations
- Aggregated metrics cache

---

## Tier 2: Platform Services (Required for Enterprise Grade)

### 5. Workflow / Approval Engine

**Why Needed:** Approval logic is currently embedded in individual services (leave service, payroll). This creates duplication and inconsistency.

**Responsibilities:**
- Configurable multi-step approval workflows
- Workflow templates (leave, payroll, expense, onboarding, etc.)
- Dynamic approver resolution (based on org hierarchy)
- Escalation rules (auto-escalate after N days)
- Delegation (out-of-office approver)
- Workflow audit trail

**Key APIs:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/workflows/templates` | Create workflow template |
| GET | `/workflows/templates` | List templates |
| POST | `/workflows/instances` | Start workflow instance |
| GET | `/workflows/instances/{id}` | Get instance status |
| POST | `/workflows/instances/{id}/approve` | Approve step |
| POST | `/workflows/instances/{id}/reject` | Reject step |
| POST | `/workflows/instances/{id}/delegate` | Delegate approval |
| GET | `/workflows/pending` | My pending approvals |

**Domain Ownership:**
- Workflow templates
- Workflow instances
- Approval steps
- Escalation rules
- Delegation records

---

### 6. Document Management Service

**Why Needed:** Employee service stores `staff_photo_url` and `staff_documents_urls` as plain strings with no actual file handling.

**Responsibilities:**
- File upload/download (S3/MinIO backend)
- Document categorization (ID proof, offer letter, tax forms, etc.)
- Version control for documents
- Access control (who can view/download)
- Document expiry tracking (visa, license renewal)
- Digital signature integration

**Key APIs:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/documents/upload` | Upload file |
| GET | `/documents/{id}` | Download file |
| GET | `/documents/employee/{id}` | List employee documents |
| DELETE | `/documents/{id}` | Delete document |
| GET | `/documents/expiring` | Expiring documents alert |
| POST | `/documents/{id}/sign` | Request digital signature |

**Domain Ownership:**
- File storage metadata
- Document categories
- Access permissions
- Expiry tracking

---

### 7. Training & Development Service

**Why Needed:** No mechanism for employee skill development, training programs, or certification tracking.

**Responsibilities:**
- Training program creation and scheduling
- Course enrollment and tracking
- Certification management
- Skill assessment
- Training budget tracking
- Learning path recommendations

**Key APIs:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/training/programs` | Create training program |
| GET | `/training/programs` | List programs |
| POST | `/training/enrollments` | Enroll employee |
| PATCH | `/training/enrollments/{id}/complete` | Mark complete |
| POST | `/training/certifications` | Add certification |
| GET | `/training/certifications/expiring` | Expiring certs |
| GET | `/training/skills/{employee_id}` | Skill matrix |

**Domain Ownership:**
- Training programs
- Enrollments
- Certifications
- Skill assessments

---

## Tier 3: Advanced Services (Competitive Differentiation)

### 8. Expense Management Service

**Responsibilities:** Employee expense claims, receipt uploads, approval workflows, reimbursement tracking, policy enforcement.

**Key APIs:** Expense creation, receipt upload, approval, reimbursement status, policy CRUD.

---

### 9. Onboarding / Offboarding Service

**Responsibilities:** New hire checklist management, onboarding task assignment, document collection, exit interview scheduling, asset return tracking, knowledge transfer.

**Key APIs:** Onboarding template CRUD, task assignment, progress tracking, offboarding initiation.

---

### 10. Asset Management Service

**Responsibilities:** Company asset tracking (laptops, phones, access cards), assignment to employees, return tracking, depreciation.

**Key APIs:** Asset CRUD, assign to employee, return, track status, depreciation report.

---

### 11. Benefits & Insurance Service

**Responsibilities:** Health insurance enrollment, benefits plan management, open enrollment periods, life/disability insurance, retirement plans.

**Key APIs:** Plan CRUD, enrollment, claims, beneficiary management.

---

### 12. AI / Insights Engine

**Responsibilities:** Predictive analytics (attrition risk, performance trends), smart recommendations (salary benchmarks, optimal scheduling), anomaly detection (attendance fraud, payroll outliers).

**Key APIs:** Attrition prediction, salary recommendations, anomaly alerts, trend analysis.

---

## Service Dependency Map

```
                    ┌─────────────────────────────┐
                    │   Workflow/Approval Engine   │
                    └──────┬──────────────┬───────┘
                           │              │
            ┌──────────────▼──┐    ┌──────▼──────────────┐
            │  Leave Service  │    │  Payroll Service     │
            └─────────────────┘    └─────────────────────┘
                                          │
                    ┌─────────────────────►│
                    │                      │
            ┌───────┴──────────┐    ┌──────▼──────────────┐
            │ Attendance Svc   │    │  Reporting Service   │
            └──────────────────┘    └─────────────────────┘
                    │                      ▲
                    │              ┌───────┘
            ┌───────▼──────────┐  │  ┌────────────────────┐
            │ Employee Service ├──┘  │ Performance Svc     │
            └───────┬──────────┘     └────────────────────┘
                    │                      ▲
            ┌───────▼──────────┐           │
            │ Organization Svc ├───────────┘
            └──────────────────┘
                    │
            ┌───────▼──────────┐
            │ Recruitment Svc  │
            └──────────────────┘
```

---

## Implementation Priority

| Priority | Service | Effort | Business Value |
|----------|---------|--------|----------------|
| P0 | Organization Service | Medium | Enables proper hierarchy, unblocks manager workflows |
| P0 | Reporting & Analytics | Medium | Every client needs dashboards and reports |
| P1 | Recruitment / ATS | Large | Core HRMS feature; top client request |
| P1 | Workflow Engine | Medium | Eliminates approval logic duplication |
| P1 | Performance Management | Large | Required for enterprise clients |
| P2 | Document Management | Small | Unblocks file uploads in employee service |
| P2 | Training & Development | Medium | Value-add for education vertical |
| P2 | Expense Management | Medium | Common enterprise requirement |
| P3 | Onboarding/Offboarding | Medium | Improves employee lifecycle |
| P3 | Asset Management | Small | Nice-to-have |
| P3 | Benefits & Insurance | Large | Region-specific complexity |
| P3 | AI/Insights Engine | Large | Long-term differentiator |

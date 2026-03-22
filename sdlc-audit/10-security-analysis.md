# Security Engineering Analysis

---

## OWASP Top 10 Assessment

| # | Vulnerability | Risk Level | Status | Details |
|---|--------------|------------|--------|---------|
| A01 | Broken Access Control | MEDIUM | ⚠ PARTIAL | RBAC implemented, but tenant isolation relies on ORM events (fail-silent risk) |
| A02 | Cryptographic Failures | HIGH | ⚠ CRITICAL GAPS | AES-256-GCM for PII (good), but no TLS anywhere, secrets in Git |
| A03 | Injection | LOW | ✅ GOOD | SQLAlchemy ORM prevents SQL injection; Pydantic validates input |
| A04 | Insecure Design | MEDIUM | ⚠ PARTIAL | Good architecture, but fail-open cross-service validation is risky |
| A05 | Security Misconfiguration | HIGH | ⚠ CRITICAL | Default RabbitMQ credentials, Redis no auth, Swagger in dev |
| A06 | Vulnerable Components | UNKNOWN | ⚠ NOT TESTED | No dependency vulnerability scanning (safety/snyk not in CI) |
| A07 | Auth Failures | LOW | ✅ GOOD | Strong password hashing (Argon2id), RS256 JWT, refresh rotation |
| A08 | Data Integrity Failures | MEDIUM | ⚠ PARTIAL | No signed events, no request signing between services |
| A09 | Logging Failures | LOW | ✅ GOOD | Structured logging, audit trail, payload sanitization |
| A10 | SSRF | LOW | ✅ GOOD | Internal URLs hardcoded, no user-supplied URL fetching |

---

## Authentication Analysis

### Strengths

| Feature | Implementation | Rating |
|---------|---------------|--------|
| Password hashing | Argon2id (19MB memory, 2 iterations) | Excellent |
| JWT signing | RS256 (asymmetric, 4096-bit RSA) | Excellent |
| Token expiry | Access: 15min, Refresh: 30 days | Good |
| Token revocation | Redis blacklist, checked on every request | Good |
| Refresh rotation | Old token revoked on each refresh | Good |
| Password policy | 10+ chars, upper+lower+digit+special | Good |
| Enumeration protection | Forgot-password returns same response always | Good |
| Magic links | Bcrypt-hashed, one-time use, 15-min expiry | Good |

### Weaknesses

| Gap | Risk | Recommendation |
|-----|------|----------------|
| No 2FA/MFA | HIGH | Add TOTP (pyotp) as mandatory for admin roles |
| No login attempt tracking | HIGH | Track failures per email; lock after 5 attempts for 15 min |
| No password history | MEDIUM | Store last 5 hashes; prevent reuse |
| No password expiry | LOW | Optional; consider for compliance |
| No email verification | MEDIUM | Require email confirmation on registration |
| Fail-open JWT blacklist | MEDIUM | If Redis down, revoked tokens are accepted |
| Static service-to-service tokens | MEDIUM | Use short-lived JWT for service auth |
| No session fingerprinting | LOW | Add device/IP binding to sessions |

---

## Authorization Analysis

### RBAC Matrix

| Action | Super Admin | HR | Manager | Employee |
|--------|:-:|:-:|:-:|:-:|
| Manage companies | ✅ | ❌ | ❌ | ❌ |
| Create users with roles | ✅ | ❌ | ❌ | ❌ |
| Change user roles | ✅ | ✅* | ❌ | ❌ |
| CRUD employees | ✅ | ✅ | ❌ | ❌ |
| View employee list | ✅ | ✅ | ✅ | ❌ |
| View own profile | ✅ | ✅ | ✅ | ✅ |
| Clock in/out | ✅ | ✅ | ✅ | ✅ |
| View all attendance | ✅ | ✅ | ✅ | ❌ |
| Manage geofences | ✅ | ✅ | ❌ | ❌ |
| Apply for leave | ✅ | ✅ | ✅ | ✅ |
| Approve leave | ✅ | ✅ | ✅ | ❌ |
| Run payroll | ✅ | ✅ | ❌ | ❌ |
| View payslips (all) | ✅ | ✅ | ❌ | ❌ |
| View own payslips | ✅ | ✅ | ✅ | ✅ |
| View audit logs | ✅ | ✅ | ❌ | ❌ |
| Export audit CSV | ✅ | ❌ | ❌ | ❌ |

*HR can assign HR/Manager/Employee roles but cannot create/demote super_admin.

### Privilege Escalation Guards
- ✅ Cannot grant a higher role than your own
- ✅ Cannot change your own role
- ✅ Cannot modify users in another company
- ✅ HR cannot demote super_admin

### Authorization Gaps
- No resource-level access control (e.g., manager can't restrict to own department)
- No scope-based permissions (coarse role-based only)
- No API-level permission granularity (all-or-nothing per role)
- No delegation support (acting on behalf of)

---

## Data Protection Analysis

### Encryption at Rest

| Data | Method | Key Management | Rating |
|------|--------|---------------|--------|
| Employee PII (Aadhaar, PAN, bank) | AES-256-GCM | Static key in env var | Good algorithm, poor key management |
| Passwords | Argon2id | N/A (one-way hash) | Excellent |
| Refresh tokens | Bcrypt hash | N/A (one-way hash) | Good |
| Magic link tokens | Bcrypt hash | N/A (one-way hash) | Good |
| JWT private key | RSA 4096-bit | **Hardcoded in .env file** | CRITICAL — must move to vault |
| Payroll data | Not encrypted | N/A | RISK — salary data stored in plaintext |
| Audit logs | Not encrypted | N/A | Acceptable — sanitized payloads |

### Encryption in Transit

| Communication Path | TLS | Rating |
|-------------------|-----|--------|
| Client → Gateway | **No** | CRITICAL — all traffic in plaintext |
| Gateway → Services | **No** | HIGH — internal traffic unencrypted |
| Services → PostgreSQL | **No** | MEDIUM — database connections unencrypted |
| Services → RabbitMQ | **No** | MEDIUM — event messages unencrypted |
| Services → Redis | **No** | MEDIUM — cache/blacklist unencrypted |

### Sensitive Data in Git Repository

| Item | File | Risk |
|------|------|------|
| JWT RSA Private Key | `services/auth-service/.env.docker` | CRITICAL |
| JWT RSA Public Key | Multiple `.env.docker` files | LOW (public key) |
| PostgreSQL Password | `docker-compose.yml`, `.env.docker` | HIGH |
| PII Encryption Key | `services/employee-service/.env.docker` | CRITICAL |
| Internal Service Tokens | Multiple `.env.docker` files | HIGH |
| RabbitMQ Credentials | `docker-compose.yml` | MEDIUM |

---

## Network Security

### Current Security Posture

```
Internet
    │
    ▼ (Port 80 — NO TLS)
┌──────────────┐
│ Nginx Gateway│ ← Rate limiting, security headers, CORS
│              │ ← No WAF, no IP filtering
└──────┬───────┘
       │ (Unencrypted HTTP)
       ▼
┌──────────────────────────────┐
│ Docker Bridge Network        │
│                              │
│ All services accessible      │
│ to each other               │
│                              │
│ No network policies         │
│ No service mesh              │
│ No mTLS                     │
│                              │
│ PostgreSQL: No auth beyond   │
│   user/password              │
│ Redis: No authentication     │
│ RabbitMQ: guest/guest        │
└──────────────────────────────┘
```

### Recommendations

1. **Add TLS at Gateway** — Use Let's Encrypt or self-signed cert for dev
2. **Add Redis AUTH** — `requirepass` in Redis config
3. **Change RabbitMQ Credentials** — Replace guest/guest with strong credentials
4. **Add Network Policies** — Restrict which services can talk to which
5. **Consider Service Mesh** — Istio/Linkerd for mTLS between services
6. **Add WAF** — ModSecurity or AWS WAF for OWASP protection

---

## Rate Limiting Analysis

| Endpoint | Limit | Scope | Backend |
|----------|-------|-------|---------|
| POST /auth/companies | 3/hour | IP | In-memory (slowapi) |
| POST /auth/register | 5/min | IP | In-memory |
| POST /auth/login | 10/min | IP | In-memory |
| POST /employees (CRUD) | 30/min | IP | In-memory |
| POST /employees/bulk | 10/min | IP | In-memory |
| POST /attendance/clock-in | 5/min | IP | In-memory |
| POST /attendance/clock-out | 5/min | IP | In-memory |
| POST /leave-requests | 10/min | IP | In-memory |
| GET /audit/logs/export/csv | 5/min | IP | In-memory |
| Gateway /auth/login | 5 req/s | IP | Nginx (burst 10) |
| Gateway (general API) | 30 req/s | IP | Nginx (burst 20) |

### Issues
- **In-memory only** — Resets on service restart; not shared across replicas
- **IP-based only** — No per-user or per-tenant rate limiting
- **No distributed backend** — Must move to Redis for multi-instance

---

## Security Hardening Checklist

### Immediate (P0)

- [ ] Move all secrets to environment injection (not .env files in Git)
- [ ] Enable TLS at Nginx gateway (even self-signed for dev)
- [ ] Add Redis AUTH password
- [ ] Change RabbitMQ default credentials
- [ ] Rotate all exposed keys and tokens
- [ ] Add `git-secrets` pre-commit hook to prevent future leaks
- [ ] Review and rotate PII encryption key

### Short-Term (P1)

- [ ] Add 2FA/MFA for admin roles
- [ ] Implement login attempt tracking + account lockout
- [ ] Add dependency vulnerability scanning in CI (safety/snyk)
- [ ] Add SAST scanning in CI (bandit)
- [ ] Move rate limiting to Redis backend
- [ ] Add email verification for registration
- [ ] Implement short-lived service-to-service JWT tokens

### Medium-Term (P2)

- [ ] Deploy HashiCorp Vault for secrets management
- [ ] Enable PostgreSQL SSL connections
- [ ] Add mTLS between services (service mesh)
- [ ] Add DAST scanning (OWASP ZAP) in CI
- [ ] Implement API request signing
- [ ] Add security headers: Content-Security-Policy, Permissions-Policy
- [ ] Add HSTS (HTTP Strict Transport Security)

### Long-Term (P3)

- [ ] SOC 2 Type II compliance preparation
- [ ] GDPR compliance (data export/deletion endpoints)
- [ ] Penetration testing (third-party)
- [ ] Bug bounty program
- [ ] Encryption key rotation automation
- [ ] Zero-trust network architecture

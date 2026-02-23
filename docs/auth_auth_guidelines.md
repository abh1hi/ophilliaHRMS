# 🔐 Authentication & Authorization Guidelines

This document defines the standards for securing HRMS microservices.

## 1. Authentication Standard
- **Mechanism**: JSON Web Tokens (JWT).
- **Algorithm**: `HS256` (Current Development) / `RS256` (Target Production).
- **Transport**: All external API calls must use `HTTPS`.
- **Header**: `Authorization: Bearer <token>`

### Token Structure
Tokens must contain the following claims:
- `sub`: The UUID of the user.
- `exp`: Expiration timestamp (UTC).
- `iat`: Issued-at timestamp (UTC).
- `type`: Either `access` or `refresh`.

### Expiration Policies
- **Access Tokens**: 30 minutes.
- **Refresh Tokens**: 7 days (Database-backed for revocation support).
- **Magic Link Tokens**: 15 minutes.

---

## 2. Authorization (RBAC)
We use Role-Based Access Control to restrict access to resources. Roles are enforced at the API level using the `require_role` dependency.

| Role | Permissions Description |
| :--- | :--- |
| `super_admin` | Global system configuration, database management, and platform-wide monitoring. |
| `hr` | Employee lifecycle management, payroll processing, and organizational structure updates. |
| `manager` | Team attendance approvals, leave requests, and performance tracking. |
| `employee` | Access to personal profile, attendance logging, and personal payslips. |

### Enforcing Roles in FastAPI
```python
@router.get("/sensitive-data")
async def get_data(current_user: User = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN))):
    return {"data": "HR specific information"}
```

---

## 3. Service-to-Service Communication
Internal calls between microservices must be authenticated.

- **Option A (mTLS)**: Mutual TLS between containers (Planned for Mesh).
- **Option B (Internal JWT)**: A specific service-token signed with an internal secret.
- **Option C (API Gateway)**: The API Gateway strips public auth and injects internal headers (e.g., `X-User-ID`, `X-User-Role`).

---

## 4. Security Best Practices
1. **Never** log sensitive tokens or passwords.
2. **Never** return the `hashed_password` in API responses.
3. **Always** use `argon2` for password hashing.
4. **Always** check `is_active` status before authorizing a request.

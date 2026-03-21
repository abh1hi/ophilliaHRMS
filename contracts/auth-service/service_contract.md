# Auth Service Contract (v3)

The Auth Service handles Authentication, Authorization (RBAC), session management, and multi-tenant company registration for the HRMS platform.

## Base URL
- **Internal (Docker)**: `http://auth-service:8000/api/v1`
- **Gateway**: `/api/v1/auth/*`

---

## Authentication
- **Mechanism**: JWT (JSON Web Tokens)
- **Algorithm**: RS256
- **Token Type**: Bearer Token
- **Headers**: `Authorization: Bearer <token>`

### JWT Payload Claims
```json
{
  "sub": "user-uuid",
  "role": "super_admin",
  "email": "user@example.com",
  "company_id": "company-uuid",
  "jti": "unique-token-id",
  "iat": 1700000000,
  "exp": 1700003600
}
```

---

## JWT Blacklist

The auth-service maintains a Redis-based JWT blacklist to support immediate token revocation across all services.

- **On logout**, the auth-service writes the key `bl:{jti}` to Redis with a TTL equal to the token's remaining lifetime.
- **All downstream services** (employee-service, leave-service, attendance-service, payroll-service, notification-service, students-service) check Redis for the `bl:{jti}` key before accepting any JWT.
- If the key exists, the token is considered revoked and the request is rejected with `401 Unauthorized`.
- This mechanism ensures that a single logout invalidates the token globally, without requiring inter-service HTTP calls.

**Redis Key Format**
| Key | Value | TTL |
| :--- | :--- | :--- |
| `bl:{jti}` | `"1"` | Remaining seconds until token `exp` |

---

## Endpoints

### 1. Register Company (Tenant)
Creates a new company / tenant for SaaS mode.

| Method | Path | Auth | Rate Limit |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/companies` | None | 3/hour |

**Request Body**
```json
{
  "name": "Acme Corp",
  "domain": "acme.com"
}
```

**Response (201 Created)**
```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "domain": "acme.com",
  "is_active": true,
  "created_at": "ISO-8601"
}
```

**Errors**: `400` if domain already registered.

---

### 2. List Companies
Returns all registered companies.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/auth/companies` | Bearer Token | Super Admin |

**Response (200 OK)**
```json
{
  "total": 3,
  "companies": [
    {
      "id": "uuid",
      "name": "Acme Corp",
      "domain": "acme.com",
      "is_active": true,
      "created_at": "ISO-8601"
    }
  ]
}
```

---

### 3. Update Company
Updates the name and/or domain of an existing company.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PATCH` | `/auth/companies/{id}` | Bearer Token | Super Admin |

**Request Body**
```json
{
  "name": "New Company Name",
  "domain": "newdomain.com"
}
```
All fields are optional — only provided fields are updated.

**Response (200 OK)**: CompanyResponse
```json
{
  "id": "uuid",
  "name": "New Company Name",
  "domain": "newdomain.com",
  "is_active": true,
  "created_at": "ISO-8601"
}
```

**Errors**: `404` if company not found. `400` if domain already in use.

---

### 4. Delete Company (Soft Delete)
Soft-deletes a company by setting `is_active=false`.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `DELETE` | `/auth/companies/{id}` | Bearer Token | Super Admin |

**Response (200 OK)**: CompanyResponse
```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "domain": "acme.com",
  "is_active": false,
  "created_at": "ISO-8601"
}
```

**Errors**: `404` if company not found.

---

### 5. Post-Login Context
Returns the next action the frontend should take after login. This is the **single source of truth** for post-login routing decisions. Inactive companies (`is_active=false`) are filtered out of the `companies` list.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/auth/post-login-context` | Bearer Token |

**Response (200 OK)**
```json
{
  "role": "super_admin",
  "companies": [],
  "next_action": "CREATE_COMPANY",
  "selected_company": null
}
```

| `next_action` value | Condition |
| :--- | :--- |
| `CREATE_COMPANY` | Super Admin + 0 companies |
| `SELECT_COMPANY` | Super Admin + 2+ companies |
| `ENTER_DASHBOARD` | All other cases |

---

### 6. Select Company
Sets the active company for the current session. Used by multi-company admins to switch between tenants. Returns a new token pair scoped to the selected company.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `POST` | `/auth/select-company` | Bearer Token |

**Request Body**
```json
{
  "company_id": "uuid"
}
```

**Response (200 OK)**: Token object
```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "uuid:secret",
  "token_type": "bearer"
}
```

**Errors**: `404` if company not found or inactive. `403` if user does not have access to the company.

---

### 7. Register User
Registers a new user account.

| Method | Path | Auth | Rate Limit |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | None | 5/min |

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "role": "employee",
  "company_id": "uuid"
}
```

- `company_id` is required in SaaS mode, auto-assigned in Single-Tenant mode.
- `role` defaults to `employee` if omitted.

**Response (201 Created)**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "email": "user@example.com",
  "role": "employee",
  "is_active": true,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

---

### 8. Login
Authenticates user and returns access/refresh tokens.

| Method | Path | Auth | Rate Limit |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | None | 10/min |

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK)**
```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "uuid:secret",
  "token_type": "bearer"
}
```

---

### 9. Refresh Token
Rotates the refresh token and issues a new access token.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `POST` | `/auth/refresh` | None |

**Query Parameters**
- `refresh_token` (string, required) — format: `uuid:secret`

**Response (200 OK)**
```json
{
  "access_token": "new_jwt_token",
  "refresh_token": "new_uuid:new_secret",
  "token_type": "bearer"
}
```

---

### 10. Get Current User (Me)
Returns profile data for the authenticated user.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/auth/me` | Bearer Token |

**Response (200 OK)**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "email": "user@example.com",
  "role": "employee",
  "is_active": true,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

---

### 11. Logout
Blacklists the current access token (writes `bl:{jti}` to Redis) and revokes all refresh tokens.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `POST` | `/auth/logout` | Bearer Token |

**Response**: `204 No Content`

---

### 12. Update User Role
Updates the RBAC role of a specific user.

| Method | Path | Auth | RBAC Role |
| :--- | :--- | :--- | :--- |
| `PATCH` | `/auth/users/{user_id}/role` | Bearer Token | HR, Super Admin |

**Request Body**
```json
{
  "role": "manager"
}
```

**Response (200 OK)**: UserResponse object

---

### 13. Magic Link Request
Sends a one-time login link via email. Auto-creates a placeholder user if email not found.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `POST` | `/auth/magic-link` | None |

**Request Body**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK)**
```json
{
  "message": "Magic link sent"
}
```

---

### 14. Verify Magic Link
Verifies the token from a magic link and issues tokens.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/auth/verify-magic` | None |

**Query Parameters**
- `token` (string, required)

**Response (200 OK)**: Token object (access_token, refresh_token, token_type)

---

### 15. Forgot Password
Initiates the password reset flow. Always returns success (email-enumeration safe).

| Method | Path | Auth |
| :--- | :--- | :--- |
| `POST` | `/auth/forgot-password` | None |

**Request Body**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK)**
```json
{
  "message": "If this email exists, a password reset link has been sent"
}
```

---

### 16. Reset Password
Completes the password reset using token from email. Revokes all existing sessions.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `POST` | `/auth/reset-password` | None |

**Request Body**
```json
{
  "token": "uuid:secret",
  "new_password": "new_secure_password"
}
```

**Response (200 OK)**
```json
{
  "message": "Password updated successfully"
}
```

---

### 17. Health Check

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/health` | None |

**Response (200 OK)**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

---

## Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `400` | Bad Request | Invalid input (duplicate email, domain already registered, etc.) |
| `401` | Unauthorized | Missing or invalid authentication token |
| `403` | Forbidden | Authenticated user lacks sufficient permissions |
| `404` | Not Found | Requested resource does not exist |
| `422` | Validation Error | Input data fails Pydantic validation |
| `429` | Too Many Requests | Rate limit exceeded |

---

## RBAC Roles

| Role | Description |
| :--- | :--- |
| `super_admin` | Full system control, company management |
| `hr` | Employee management, payroll, role assignments |
| `manager` | Departmental management and approvals |
| `employee` | Standard access to own profile, leave, and payroll |

---

## Database Tables

### companies
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `name` | String | Unique, indexed, not null |
| `domain` | String | Unique, indexed, nullable |
| `is_active` | Boolean | Default: true |
| `created_at` | DateTime | UTC |

### users
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `company_id` | UUID | FK -> companies.id, indexed, not null |
| `email` | String | Unique, indexed, not null |
| `hashed_password` | String | Nullable (for magic-link-only accounts) |
| `role` | String | Default: employee, indexed |
| `is_active` | Boolean | Default: true |
| `created_at` | DateTime | UTC, indexed |
| `updated_at` | DateTime | UTC |

### refresh_tokens
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `user_id` | UUID | FK -> users.id |
| `token_hash` | String | Bcrypt hash of secret |
| `expires_at` | DateTime | UTC |
| `revoked` | Boolean | Default: false |
| `created_at` | DateTime | UTC |

### magic_tokens
| Column | Type | Constraints |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `user_id` | UUID | FK -> users.id |
| `token_hash` | String | Bcrypt hash of secret |
| `purpose` | String | login, reset_password |
| `expires_at` | DateTime | UTC |
| `used` | Boolean | Default: false |
| `created_at` | DateTime | UTC |

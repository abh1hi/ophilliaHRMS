# 🔐 Auth Service Contract (v1)

The Auth Service handles Authentication, Authorization (RBAC), and session management for the HRMS platform.

## 🚀 Base URL
- **Production**: `https://auth.hrms.com/api/v1`
- **Internal (Docker)**: `http://auth-service:8000/api/v1`

---

## 🔑 Authentication
- **Mechanism**: JWT (JSON Web Tokens)
- **Algorithm**: RS256 (Planned) / HS256 (Current)
- **Token Type**: Bearer Token
- **Headers**: `Authorization: Bearer <token>`

---

## 📡 Endpoints

### 1. Register User
Registers a new user account with a default role.

| Method | Path | Auth | Rate Limit |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | None | 5/min |

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "role": "employee"
}
```

**Response (201 Created)**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "employee",
  "is_active": true,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

---

### 2. Login
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

### 3. Refresh Token
Rotates the refresh token and issues a new access token.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `POST` | `/auth/refresh` | None |

**Query Parameters**
- `refresh_token` (string, required)

**Response (200 OK)**
```json
{
  "access_token": "new_jwt_token",
  "refresh_token": "new_uuid:new_secret",
  "token_type": "bearer"
}
```

---

### 4. Get Current User (Me)
Returns profile data for the authenticated user.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/auth/me` | Bearer Token |

**Response (200 OK)**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "employee",
  "is_active": true,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

---

### 5. Update User Role
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

**Response (200 OK)**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "manager",
  "is_active": true,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

---

### 6. Magic Link Request
Sends a one-time login link via email.

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

### 7. Verify Magic Link
Verifies the token from a magic link.

| Method | Path | Auth |
| :--- | :--- | :--- |
| `GET` | `/auth/verify-magic` | None |

**Query Parameters**
- `token` (string, required)

**Response (200 OK)**
```json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer"
}
```

---

### 8. Forgot Password
Initiates the password reset flow.

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

### 9. Reset Password
Resets the password using a token.

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

## 🛠 Error Codes

| Status Code | Meaning | Description |
| :--- | :--- | :--- |
| `401` | Unauthorized | Missing or invalid authentication token. |
| `403` | Forbidden | Authenticated user lacks sufficient permissions. |
| `404` | Not Found | Requested resource (e.g., user) does not exist. |
| `422` | Validation Error | Input data fails validation (Pydantic). |
| `429` | Too Many Requests | Rate limit exceeded. |

---

## 🛡️ RBAC Roles
- `super_admin`: Full system control.
- `hr`: Employee management, payroll, and role assignments.
- `manager`: Departmental management and approvals.
- `employee`: Standard access to own profile, leave, and payroll.

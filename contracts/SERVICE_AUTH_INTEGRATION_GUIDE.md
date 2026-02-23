# 🔐 Service Auth Integration Guide

> **Audience**: Developers building HRMS microservices (Employee, Attendance, Payroll, Leave, Notification, Audit, etc.)  
> **Auth Service Internal URL**: `http://auth-service:8000/api/v1`

This guide explains how every microservice in the HRMS platform must integrate with the Auth Service for JWT validation, role verification, expired token handling, and service-to-service authentication.

---

## 1. Required Headers

All protected endpoints must receive the following HTTP headers from the caller:

| Header | Value | Required |
| :--- | :--- | :--- |
| `Authorization` | `Bearer <access_token>` | ✅ Yes |
| `X-Request-ID` | Unique UUID per request | ✅ Yes (for tracing) |
| `X-Service-Name` | Name of the calling service | ✅ Yes (for audit logs) |
| `Content-Type` | `application/json` | ✅ Yes |

**Example:**
```http
GET /api/v1/employees/me HTTP/1.1
Host: employee-service:8001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Service-Name: employee-service
Content-Type: application/json
```

---

## 2. How to Validate a JWT

Each service must validate the JWT on **every protected request**. Do **not** trust the token blindly — always verify it.

### 2.1 Validation Flow

```
Incoming Request
      │
      ▼
Extract Bearer Token from Authorization header
      │
      ▼
Decode & verify JWT signature (shared SECRET_KEY / public key)
      │
      ▼
Check token expiry (exp claim)
      │
      ▼
Extract payload: user_id, role, email
      │
      ▼
Proceed with request using extracted identity
```

### 2.2 Python Implementation (FastAPI Dependency)

Install required libraries:
```
python-jose[cryptography]
```

**`app/core/auth.py`**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from pydantic import BaseModel
import os

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")   # Must match auth-service SECRET_KEY
ALGORITHM = "HS256"                          # HS256 current | RS256 planned

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth-service:8000/api/v1/auth/login")


class TokenPayload(BaseModel):
    sub: str        # user_id (UUID)
    role: str       # employee | manager | hr | super_admin
    email: str


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        email: str = payload.get("email")

        if not user_id or not role:
            raise credentials_exception

        return TokenPayload(sub=user_id, role=role, email=email)

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please refresh your token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception
```

### 2.3 JWT Payload Structure

The Auth Service issues tokens with the following claims:

```json
{
  "sub": "uuid-of-user",
  "role": "employee",
  "email": "user@example.com",
  "iat": 1700000000,
  "exp": 1700003600
}
```

| Claim | Type | Description |
| :--- | :--- | :--- |
| `sub` | `string` (UUID) | Unique user identifier |
| `role` | `string` | RBAC role of the user |
| `email` | `string` | User's email address |
| `iat` | `int` | Issued-at timestamp (Unix) |
| `exp` | `int` | Expiry timestamp (Unix) |

---

## 3. How to Verify Roles (RBAC)

After extracting the token payload, enforce role-based access using a dependency.

### 3.1 RBAC Role Hierarchy

| Role | Level | Permissions |
| :--- | :--- | :--- |
| `super_admin` | 4 | Full system access |
| `hr` | 3 | Employee mgmt, payroll, role assignment |
| `manager` | 2 | Department mgmt, leave approvals |
| `employee` | 1 | Own profile, own leave, own payroll |

### 3.2 Role-Check Dependency

**`app/core/roles.py`**
```python
from fastapi import Depends, HTTPException, status
from app.core.auth import TokenPayload, get_current_user
from typing import List


def require_roles(*allowed_roles: str):
    """
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: TokenPayload = Depends(require_roles("super_admin", "hr"))):
            ...
    """
    def role_checker(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}. Your role: {current_user.role}",
            )
        return current_user
    return role_checker
```

### 3.3 Usage in Endpoints

```python
from app.core.roles import require_roles
from app.core.auth import TokenPayload

# Only HR and Super Admin can access
@router.get("/employees", dependencies=[Depends(require_roles("hr", "super_admin"))])
async def list_employees():
    ...

# Any authenticated user can access their own data
@router.get("/me")
async def get_my_profile(current_user: TokenPayload = Depends(get_current_user)):
    return {"user_id": current_user.sub, "role": current_user.role}
```

---

## 4. How to Handle Expired Tokens

Tokens issued by the Auth Service have a short lifespan (default: **60 minutes**).

### 4.1 Expiry Behavior

| Scenario | HTTP Status | Response Detail |
| :--- | :--- | :--- |
| Valid token | `200 OK` | Normal response |
| Expired token | `401 Unauthorized` | `"Token has expired. Please refresh your token."` |
| Invalid/tampered token | `401 Unauthorized` | `"Invalid or missing authentication token"` |
| Missing token | `401 Unauthorized` | `"Not authenticated"` |

### 4.2 Client-Side Refresh Flow

When a service/client receives `401` with expired token detail, it must call the Auth Service refresh endpoint:

```
POST http://auth-service:8000/api/v1/auth/refresh?refresh_token=<refresh_token>
```

**Response:**
```json
{
  "access_token": "new_jwt_token",
  "refresh_token": "new_uuid:new_secret",
  "token_type": "bearer"
}
```

> ⚠️ **Refresh tokens are rotated on every use.** Store the new refresh token after each refresh call.

### 4.3 Services Must NOT Cache Tokens

- Services must **never cache** user JWTs.
- Validate the token on **every request**.
- Only short-lived validation results (e.g., role lookups) may be cached in Redis with a TTL ≤ 60 seconds.

---

## 5. Service-to-Service Authentication

When a microservice calls another microservice internally (not on behalf of a user), it must use an **internal service token** — not a user JWT.

### 5.1 How It Works

```
Service A                         Service B
   │                                   │
   │─── POST /api/v1/some-endpoint ───►│
   │    X-Service-Token: <svc_token>   │
   │    X-Service-Name: service-a      │
   │                                   │
   │◄── 200 OK ────────────────────────│
```

### 5.2 Internal Service Token

Each service is issued a shared secret token set in the environment:

```env
# .env (auth-service)
INTERNAL_SERVICE_TOKEN=super-secret-internal-token-change-in-production
```

All services share this token via Docker environment variables:

```env
# .env (every service)
AUTH_SERVICE_URL=http://auth-service:8000
INTERNAL_SERVICE_TOKEN=super-secret-internal-token-change-in-production
AUTH_SECRET_KEY=your-jwt-secret-key
```

### 5.3 Sending a Service-to-Service Request

```python
import httpx
import os

INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")


async def call_auth_service(endpoint: str, method: str = "GET", payload: dict = None):
    headers = {
        "X-Service-Token": INTERNAL_SERVICE_TOKEN,
        "X-Service-Name": "employee-service",   # replace with calling service name
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=3.0) as client:
        for attempt in range(3):
            try:
                response = await client.request(
                    method,
                    f"{AUTH_SERVICE_URL}{endpoint}",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                if attempt == 2:
                    raise
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Auth service error: {e.response.status_code}")
```

### 5.4 Validating the Internal Token on the Receiving Service

Services that expose internal-only endpoints must validate the `X-Service-Token`:

```python
from fastapi import Header, HTTPException, status
import os

INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN")


def verify_service_token(x_service_token: str = Header(...)):
    if x_service_token != INTERNAL_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal service token",
        )
```

**Usage on internal-only endpoints:**
```python
@router.get("/internal/user/{user_id}", dependencies=[Depends(verify_service_token)])
async def get_user_internal(user_id: str):
    # Only reachable by other internal services
    ...
```

---

## 6. Error Reference

| Status | Reason | Action |
| :--- | :--- | :--- |
| `401` — Missing token | No `Authorization` header sent | Include `Authorization: Bearer <token>` |
| `401` — Expired token | Token `exp` has passed | Refresh using `/auth/refresh` |
| `401` — Invalid token | Signature verification failed | Re-authenticate; log error |
| `403` — Forbidden | Role insufficient for endpoint | Check required roles; deny gracefully |
| `503` — Auth service down | Auth service unreachable | Return `503` to client; do not crash; log error |

---

## 7. Environment Variables Checklist

Every service must define these in its `.env`:

```env
AUTH_SECRET_KEY=<same-secret-as-auth-service>
AUTH_SERVICE_URL=http://auth-service:8000
INTERNAL_SERVICE_TOKEN=<shared-internal-token>
```

> 🔒 **Never hardcode secrets.** Always read from environment variables.

---

## 8. Integration Checklist

Before marking auth integration as complete on any service:

- [ ] JWT decoded and verified on every protected request
- [ ] `exp` claim checked — expired tokens return `401`
- [ ] Role extracted from payload — unauthorized roles return `403`
- [ ] `X-Request-ID` logged on every request
- [ ] Service-to-service calls use `X-Service-Token`, not user JWT
- [ ] Auth service failure returns `503` — service does **not** crash
- [ ] Timeout of ≤ 3 seconds set on all calls to Auth Service
- [ ] No JWT or secrets hardcoded in source code
- [ ] Internal endpoints protected with `verify_service_token` dependency

---

*This guide follows the [HRMS Communication Model](../hrms-communication-model-document.md) and [HRMS Development Rulebook](../hrms-development-rulebook.md).*

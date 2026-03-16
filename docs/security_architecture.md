# OphilliaHRMS - Security & Architecture Documentation

## 1. ACCESS CONTROL MODEL

### Access Control Architecture

OphilliaHRMS uses a microservices-based API architecture with a central API Gateway acting as the sole entry point for all external requests.

- **Authentication Method**: JWT (JSON Web Tokens) with RS256 asymmetric encryption. Access tokens are short-lived (15 minutes), and refresh tokens are long-lived (30 days) and stored securely.
- **Authorization Model**: Role-Based Access Control (RBAC). Roles are attached to the users and validated in the Gateway and Service layers.
- **Token Flow**:
  1. User authenticates via the Auth Service to receive a JWT.
  2. For subsequent requests, the client attaches the JWT in the `Authorization: Bearer <access_token>` header.
  3. The token is checked initially by the API Gateway (or within the service itself if the gateway passes it through).
- **Service-to-Service Authentication**: Internal communications between microservices use dedicated internal service tokens. External REST calls must include the user's JWT validation, but no internal services are publicly exposed.
- **Permission Validation Layer**: Business logic authorization (checking if a user owns a resource or has the right role) is enforced at the individual microservice level. 

### Request Flow
**User → API Gateway → Service → Database**
1. **User/Client** makes an HTTPS request to `/api/v1/...` with their JWT token.
2. **API Gateway (Nginx)** receives the request, enforces HTTPS, rate limits if necessary, and optionally pre-validates the token before forwarding to the target Service. The gateway also injects an `X-Correlation-ID` header if one is missing.
3. **Microservice (FastAPI)** receives the request, validates the JWT, checks if the user's role (extracted from JWT) permits access to the endpoint, and runs business logic. 
4. **Database (PostgreSQL)** executes the queries securely via SQLAlchemy ORM (preventing SQL injection), returning results to the service isolating data based on the service's schema.

---

## 2. ROLE AND PERMISSION MATRIX

OphilliaHRMS implements a strictly hierarchical RBAC system. Permissions generally inherit upwards unless explicitly restricted.

| ROLE | SERVICE | ACTIONS ALLOWED | DATA SCOPE | API ENDPOINTS |
| --- | --- | --- | --- | --- |
| **employee** | Employee, Attendance, Leave | View profile, update personal info, view payslips, clock in/out, request leave. | Self (Own data only) | `GET /employees/{id}`<br>`POST /leave-requests` |
| **manager** | Employee, Attendance, Leave | View team profiles, approve team leaves, view team attendance. | Team members only | `GET /employees?department=X`<br>`PATCH /leave-requests/{id}` |
| **hr** | All Services | Manage employees, approve leave overrides, run payroll, view system-wide reports. | All employees | `POST /employees`<br>`POST /payroll/run` |
| **super_admin** | Auth, Audit, All | Manage services, define roles, system configuration, view audit logs. | Entire System | `GET /audit/logs`<br>`PATCH /roles/{id}` |

### Permission Hierarchy & Fine-Grained Controls
- **Hierarchical Access**: A Manager can do everything an Employee can for themselves, plus manager-specific actions for their direct reports. HR acts cross-departmentally.
- **Data Scoping**: Permissions are dynamically scoped by contextual rules (e.g., managers can only query `employee_id` values mapping to their sub-hierarchy).

---

## 3. SERVICE LEVEL ACCESS CONTROL

### Auth Service
- **Purpose**: Handles login, JWT issuance, and user credential validation.
- **Accessible by**: All users (login/refresh).
- **Internal vs External**: Login endpoints are external; token validation endpoints are accessible internally by other services.
- **API Permission Validation**: Registration/Admin endpoints are restricted to `hr` and `super_admin`.

### Employee Service
- **Purpose**: Core employee profile management and organizational structure.
- **Accessible by**: employee, manager, hr, super_admin.
- **Internal vs External**: External for profile viewing/editing. Internal for other services looking up employee details.
- **API Permission Validation**: Employees can `GET` their own ID. HR can `POST`/`PATCH` globally.

### Attendance Service
- **Purpose**: Tracks employee clock-ins, physical presence, and daily hours.
- **Accessible by**: employee (log time), manager (view team), hr (edit/correct).
- **Internal vs External**: External API for terminal/web clock-in. Internal event emissions to Payroll.
- **API Permission Validation**: Time entries are strictly bound to the authenticated user's ID. Modifications require HR roles.

### Leave Service
- **Purpose**: Manage employee absences, sick days, and vacation time.
- **Accessible by**: employee (request), manager/hr (approve/deny).
- **Internal vs External**: External API. Internal triggers for `leave.approved` events via RabbitMQ.
- **API Permission Validation**: Role validation required for the `/approve` and `/reject` endpoints.

### Payroll Service
- **Purpose**: Calculating salaries, processing tax, generating payslips.
- **Accessible by**: hr, super_admin.
- **Internal vs External**: Strictly restricted external access for HR to run payroll. Employees can read-only their own generated payslips.
- **API Permission Validation**: Idempotency keys (`Idempotency-Key` header) are required to prevent duplicate payroll runs.

---

## 4. DATABASE SECURITY ARCHITECTURE

- **Number of Database Instances**: The system follows the **Database per service (Strict Isolation)** pattern.
- **Architecture Setup**: Each microservice has its own isolated PostgreSQL database (e.g., `auth_db`, `employee_db`, `payroll_db`). 

#### Advantages
- **Fault Tolerance**: If the `attendance_db` crashes, the `employee_db` and `auth_db` remain operational, allowing users to still log in and view their profiles.
- **Security Isolation**: An SQL injection (if one were theoretically possible) in one service cannot extract data from another service.
- **Scalability**: Databases can be scaled independently.

#### Risks
- **Data Consistency**: Requires eventual consistency via an event broker (RabbitMQ) to sync states, complicating transactional operations.

---

## 5. DATABASE ACCESS CONTROL

- **Which services can access which database**: 
  - Auth Service → `auth_db`
  - Employee Service → `employee_db`
  - Payroll Service → `payroll_db`
- **Database Rules**: NO CROSS-DATABASE JOINS. Services do not share database credentials or connections.
- **User Roles & Credentials**: Each service connects using specific, isolated PostgreSQL credentials injected via secret environment variables. No service connects using the `postgres` superuser in production.
- **Connection Management**: Connections use SQLAlchemy connection pooling with defined timeouts.

---

## 6. DATA ISOLATION STRATEGY

OphilliaHRMS enforces database-level and application-level data isolation.

- **Service-Level Database Isolation**: Data is inherently isolated because the underlying persistence layers are separated per service.
- **Row-Level Security (RLS) / Application-Level Multi-Tenancy**: The application logic enforces scoping dynamically:
  - When an Employee queries `/api/v1/leave-requests`, the FastAPI backend automatically injects a restriction clause for `employee_id = <jwt_user_id>`.
  - No database queries are built using concatenated strings, strictly preventing authorization bypass through SQL injection.

---

## 7. SECURITY HARDENING

- **Encryption in Transit**: TLS/HTTPS is enforced at the Nginx API Gateway level. Internal service-to-service communication is entirely enclosed within the Docker Compose network.
- **Encryption at Rest**: PostgreSQL volumes should be encrypted at the host infrastructure level. Passwords are hashed using bcrypt.
- **Secret Management**: Passwords, JWT secret keys, and DB URIs are managed via environment variables (and should use Docker secrets or AWS Secrets Manager in production).
- **API Gateways & Firewalls**: Internal services are NOT mapped to the host's public network interface. Only the API Gateway is exposed. 
- **Rate Limiting**: The gateway enforces rate limits and exposes headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`).
- **CORS Restriction**: CORS is explicitly restricted.

---

## 8. AUDIT AND MONITORING

- **Centralized Audit Service**: Driven asynchronously via RabbitMQ. When a critical action occurs (e.g., `employee.created`, `leave.approved`), the initiating service publishes an immutable event, which the Audit Service consumes and logs. 
- **Tracing**: Every external request gets an `X-Correlation-ID`. This ID is injected into all subsequent REST or asynchronous event calls, allowing logs to be traced end-to-end.
- **Logging Stack**: Structured JSON logs are ingested by ELK Stack or Loki/Grafana. Every log contains:
  - `request_id` (Correlation ID)
  - `service_name`
  - `timestamp`
  - `user_id`

---

## 9. SECURITY RISK ANALYSIS

| Risk Identifier | Weakness Description | Mitigation Strategy |
| --- | --- | --- |
| **Token Theft (XSS)** | If access tokens are stored in `localStorage`, XSS could lead to token theft. | Implement secure `HttpOnly` cookies for refresh tokens. Keep access token lifetimes short (15 mins). |
| **Service-to-Service Spoofing** | If the internal network is breached, an attacker could spoof internal REST calls. | Require internal service JWTs or mTLS for all service-to-service HTTP requests. |
| **Event Replay Attacks** | Asynchronous events could be intercepted or replayed in the broker queue. | Enforce idempotency keys on RabbitMQ consumers. Consumer services must verify if an `event_id` exists. |
| **Rate Limit Evasion** | Attackers could rotate IPs to bypass rate limiting on login points. | Use progressive delays, CAPTCHA, or account lockouts for the Auth Service. |

---

## 10. FINAL ARCHITECTURE SUMMARY

- **Overall Access Strategy**: A robust API Gateway + stateless microservices model utilizing brief-lived JWTs and hierarchical RBAC.
- **Database Isolation Strategy**: Gold-standard "Database-per-service" architectural isolation, fully preventing unintended cross-service data spillage. 
- **Security Strength Level**: **High**. Follows zero-trust internal principles using correlation IDs, segregated networks (Docker internal DNS), asynchronous logging via RabbitMQ, and Pydantic input sanitization.
- **Recommended Improvements**: 
  1. Enforce **mTLS** between containers.
  2. Implement **OWASP ZAP** in the CI/CD pipeline to catch regressions.

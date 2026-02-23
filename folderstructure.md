# 📦 HRMS Production-Grade Folder Structure

Microservices Architecture (FastAPI + PostgreSQL + Docker)

Designed for: - 2 vCPU - 8GB RAM - 100GB NVMe - Fully isolated
microservices - Single PostgreSQL instance (multiple databases)

------------------------------------------------------------------------

# 🏗️ Root Project Structure

hrms-platform/ │ ├── services/ │ ├── auth-service/ │ ├──
employee-service/ │ ├── attendance-service/ │ ├── payroll-service/ │ ├──
leave-service/ │ ├── notification-service/ │ └── audit-service/ │ ├──
gateway/ │ └── nginx/ │ ├── infrastructure/ │ ├── docker-compose.yml │
├── .env │ ├── postgres/ │ │ └── init-multiple-dbs.sql │ ├── redis/ │
└── rabbitmq/ │ ├── scripts/ │ ├── backup.sh │ ├── restore.sh │ └──
migrate-all.sh │ ├── docs/ │ ├── architecture.md │ ├── api-contracts.md
│ └── deployment.md │ ├── .github/ │ └── workflows/ │ └── ci.yml │ └──
README.md

------------------------------------------------------------------------

# 🧩 Standard Microservice Structure

Each service MUST follow this structure for consistency and isolation.

service-name/ │ ├── app/ │ ├── main.py │ │ │ ├── api/ │ │ ├── v1/ │ │ │
├── endpoints/ │ │ │ │ ├── module_routes.py │ │ │ │ └── health.py │ │ │
└── router.py │ │ └── dependencies.py │ │ │ ├── core/ │ │ ├── config.py
│ │ ├── security.py │ │ ├── logging.py │ │ └── constants.py │ │ │ ├──
models/ │ │ ├── base.py │ │ └── entity_models.py │ │ │ ├── schemas/ │ │
└── request_response_models.py │ │ │ ├── services/ │ │ └──
business_logic.py │ │ │ ├── repositories/ │ │ └── database_repository.py
│ │ │ ├── db/ │ │ ├── session.py │ │ ├── base.py │ │ └── migrations/ │ │
│ ├── events/ │ │ ├── publisher.py │ │ └── consumer.py │ │ │ ├──
middleware/ │ │ └── request_id.py │ │ │ └── utils/ │ └── helpers.py │
├── tests/ │ ├── unit/ │ ├── integration/ │ ├── security/ │ └──
performance/ │ ├── alembic.ini ├── Dockerfile ├── requirements.txt ├──
.env └── pytest.ini

------------------------------------------------------------------------

# 🔐 Auth Service (Example Specialization)

Handles authentication, JWT, and RBAC.

auth-service/app/ │ ├── api/v1/endpoints/ │ ├── login.py │ ├──
register.py │ ├── refresh.py │ └── roles.py │ ├── core/ │ ├── jwt.py │
├── password_hashing.py │ └── rbac.py │ ├── models/ │ ├── user.py │ └──
role.py │ └── services/ └── auth_service.py

------------------------------------------------------------------------

# 🗄 PostgreSQL Strategy

Single PostgreSQL container Multiple isolated databases:

-   auth_db
-   employee_db
-   attendance_db
-   payroll_db
-   leave_db
-   notification_db
-   audit_db

NO cross-database queries allowed.

------------------------------------------------------------------------

# 🌐 Gateway Structure

gateway/nginx/ │ ├── nginx.conf └── Dockerfile

Routes traffic to internal services using Docker DNS.

------------------------------------------------------------------------

# 🐳 Infrastructure Layer

infrastructure/ │ ├── docker-compose.yml ├──
postgres/init-multiple-dbs.sql ├── redis/ └── rabbitmq/

Single command deployment:

docker compose up --build -d

------------------------------------------------------------------------

# 🧪 Testing Structure

Each service includes:

tests/ ├── unit/ ├── integration/ ├── security/ └── performance/

Minimum 80% coverage required.

------------------------------------------------------------------------

# 🚀 Production Validation Checklist

-   Services deploy independently
-   Killing one service does not crash others
-   Each service owns its database
-   No shared models across services
-   Communication only via REST or events
-   Dockerized and CI/CD ready

------------------------------------------------------------------------

# 🎯 Architecture Principle

A microservice must be: - Deployable independently - Scalable
independently - Killable independently - Testable independently

If any service failure affects others, the architecture is incorrect.

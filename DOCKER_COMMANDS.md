# OphilliaHRMS — Docker Commands Reference

> **All commands must be run from the project root:**
> ```
> cd C:\Users\abhin\Desktop\ophilliaHRMS
> ```
> Running from a service subdirectory will fail — `docker-compose.yml` lives at the root.

---

## Profiles & Container Names

| Profile   | Service name (in compose)  | Container name      |
| --------- | -------------------------- | ------------------- |
| `core`    | `hrms-db`                  | `hrms-db`           |
| `core`    | `redis`                    | `hrms-redis`        |
| `core`    | `rabbitmq`                 | `hrms-rabbitmq`     |
| `core`    | `auth-service`             | `hrms-auth`         |
| `core`    | `notification-service`     | `hrms-notification` |
| `core`    | `audit-service`            | `hrms-audit`        |
| `core`    | `onboarding-service`       | `hrms-onboarding`   |
| `core`    | `frontend`                 | `hrms-frontend`     |
| `core`    | `gateway`                  | `hrms-gateway`      |
| `hr`      | `employee-service`         | `hrms-employee`     |
| `hr`      | `attendance-service`       | `hrms-attendance`   |
| `hr`      | `leave-service`            | `hrms-leave`        |
| `hr`      | `payroll-service`          | `hrms-payroll`      |
| `student` | `students-service`         | `hrms-students`     |

> **Rule:** `hr` and `student` services depend on `core` (DB, Redis, RabbitMQ, auth).
> Always start `core` first, or use `--profile core --profile hr` together.

---

## Starting Services

### Start everything (all profiles)
```bash
docker compose --profile core --profile hr --profile student up --build -d
```

### Start core infrastructure only
```bash
docker compose --profile core up --build -d
```

### Start core + HR module
```bash
docker compose --profile core --profile hr up --build -d
```

### Start without rebuilding images
```bash
docker compose --profile core --profile hr up -d
```

### Start in foreground (see logs live)
```bash
docker compose --profile core --profile hr up --build
```

---

## Rebuilding

### Rebuild all images (no cache)
```bash
docker compose --profile core --profile hr --profile student build --no-cache
```

### Rebuild a single service image (no restart)
```bash
# core profile services
docker compose --profile core build auth-service
docker compose --profile core build frontend
docker compose --profile core build gateway

# hr profile services
docker compose --profile hr build employee-service
docker compose --profile hr build attendance-service
docker compose --profile hr build leave-service
docker compose --profile hr build payroll-service
```

### Rebuild and restart a single service (core must already be running)
```bash
# core profile services
docker compose --profile core up --build -d --no-deps auth-service
docker compose --profile core up --build -d --no-deps gateway
docker compose --profile core up --build -d --no-deps frontend

# hr profile services
docker compose --profile hr up --build -d --no-deps employee-service
docker compose --profile hr up --build -d --no-deps attendance-service
docker compose --profile hr up --build -d --no-deps leave-service
docker compose --profile hr up --build -d --no-deps payroll-service
```

---

## Stopping Services

### Stop all running services
```bash
docker compose --profile core --profile hr --profile student down
```

### Stop and remove volumes (wipes database, rabbitmq, redis data)
```bash
docker compose --profile core --profile hr --profile student down -v
```

### Stop a single service
```bash
docker compose --profile core stop auth-service
docker compose --profile core stop frontend
docker compose --profile hr stop attendance-service
docker compose --profile hr stop employee-service
```

---

## Restarting

### Restart all services
```bash
docker compose --profile core --profile hr restart
```

### Restart a single service
```bash
docker compose --profile core restart auth-service
docker compose --profile core restart frontend
docker compose --profile hr restart attendance-service
docker compose --profile hr restart employee-service
```

---

## Logs

> For single-service logs you can also use `docker logs` directly — no profile needed:
> ```bash
> docker logs -f hrms-attendance
> docker logs -f hrms-employee
> docker logs --tail=100 hrms-auth
> ```

### View all logs (follow mode)
```bash
docker compose --profile core --profile hr logs -f
```

### View logs for a single service (compose style)
```bash
docker compose --profile core logs -f auth-service
docker compose --profile core logs -f frontend
docker compose --profile hr logs -f attendance-service
docker compose --profile hr logs -f employee-service
```

### View last 100 lines of a service
```bash
docker logs --tail=100 hrms-auth
docker logs --tail=100 hrms-attendance
docker logs --tail=100 hrms-employee
```

### View logs for multiple services
```bash
docker compose --profile core --profile hr logs -f auth-service employee-service attendance-service
docker compose --profile core logs -f auth-service gateway frontend
```

---

## Status & Health

### List running containers with status
```bash
docker compose ps
```

### List all containers (including stopped)
```bash
docker compose ps -a
```

### Check health of a specific container
```bash
docker inspect --format='{{.State.Health.Status}}' hrms-auth
docker inspect --format='{{.State.Health.Status}}' hrms-attendance
docker inspect --format='{{.State.Health.Status}}' hrms-employee
```

### Check resource usage
```bash
docker stats --no-stream
```

---

## Database

### Open psql shell on the database
```bash
docker exec -it hrms-db psql -U postgres
```

### List all databases
```bash
docker exec -it hrms-db psql -U postgres -c "\l"
```

### Connect to a specific service database
```bash
docker exec -it hrms-db psql -U postgres -d auth_db
docker exec -it hrms-db psql -U postgres -d employee_db
docker exec -it hrms-db psql -U postgres -d attendance_db
docker exec -it hrms-db psql -U postgres -d leave_db
docker exec -it hrms-db psql -U postgres -d payroll_db
docker exec -it hrms-db psql -U postgres -d students_db
```

### Run Alembic migrations for a service
```bash
docker exec -it hrms-auth alembic upgrade head
docker exec -it hrms-employee alembic upgrade head
docker exec -it hrms-attendance alembic upgrade head
docker exec -it hrms-leave alembic upgrade head
```

### Dump a database
```bash
docker exec hrms-db pg_dump -U postgres auth_db > backup_auth.sql
docker exec hrms-db pg_dump -U postgres employee_db > backup_employee.sql
docker exec hrms-db pg_dump -U postgres attendance_db > backup_attendance.sql
```

### Restore a database
```bash
docker exec -i hrms-db psql -U postgres auth_db < backup_auth.sql
docker exec -i hrms-db psql -U postgres employee_db < backup_employee.sql
docker exec -i hrms-db psql -U postgres attendance_db < backup_attendance.sql
```

---

## Attendance Service

### Health check
```bash
curl http://localhost:8002/health
```

### View logs
```bash
docker logs -f hrms-attendance
```

### Run migrations
```bash
docker exec -it hrms-attendance alembic upgrade head
```

### Run idempotency tests
```bash
docker exec -it hrms-attendance pytest tests/unit/test_idempotency_middleware.py -v
```

### Access shell
```bash
docker exec -it hrms-attendance bash
```

### View database
```bash
docker exec -it hrms-db psql -U postgres -d attendance_db
```

### Monitor startup alerts (RabbitMQ)
```bash
docker exec hrms-rabbitmq rabbitmqctl list_bindings
# Look for: attendance.stale_records_alert
```

---

## RabbitMQ

### Management UI
Open http://localhost:15672 (guest / guest)

### List queues
```bash
docker exec hrms-rabbitmq rabbitmqctl list_queues
```

---

## Redis

### Open redis CLI
```bash
docker exec -it hrms-redis redis-cli
```

### Check keys
```bash
docker exec -it hrms-redis redis-cli KEYS '*'
```

### Flush all cached data
```bash
docker exec -it hrms-redis redis-cli FLUSHALL
```

---

## Cleanup

### Remove stopped containers
```bash
docker compose rm -f
```

### Remove all unused images
```bash
docker image prune -f
```

### Remove all unused images, volumes, and networks (full cleanup)
```bash
docker system prune -a --volumes -f
```

### Remove only this project's volumes (wipes all data)
```bash
docker volume rm ophilliahrms_hrms-db-data ophilliahrms_rabbitmq-data ophilliahrms_redis-data
```

---

## Exec / Shell Access

### Open a bash shell inside a service container
```bash
docker exec -it hrms-auth bash
docker exec -it hrms-attendance bash
docker exec -it hrms-employee bash
docker exec -it hrms-leave bash
docker exec -it hrms-notification bash
```

### Run a one-off Python command inside a service
```bash
docker exec -it hrms-auth python -c "print('hello')"
docker exec -it hrms-attendance python -c "print('Attendance Service')"
docker exec -it hrms-employee python -c "print('Employee Service')"
```

---

## Networking

### Inspect the HRMS network
```bash
docker network inspect hrms-network
```

### List all containers on the network
```bash
docker network inspect hrms-network --format='{{range .Containers}}{{.Name}} {{end}}'
```

---

## Port Reference

| Service              | Port  |
| -------------------- | ----- |
| Frontend             | 3000  |
| Gateway (nginx)      | 80    |
| Auth Service         | 8000  |
| Employee Service     | 8001  |
| Attendance Service   | 8002  |
| Students Service     | 8003  |
| Payroll Service      | 8004  |
| Leave Service        | 8005  |
| Audit Service        | 8006  |
| Notification Service | 8007  |
| PostgreSQL           | 5432  |
| RabbitMQ AMQP        | 5672  |
| RabbitMQ Management  | 15672 |
| Redis                | 6379  |

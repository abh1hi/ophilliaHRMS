# OphilliaHRMS — Docker Commands Reference

## Profiles

The system uses Docker Compose profiles to deploy modular blocks:

| Profile   | Services                                                        |
| --------- | --------------------------------------------------------------- |
| `core`    | frontend, gateway, hrms-db, rabbitmq, redis, auth, notification, audit |
| `hr`      | employee, attendance, leave, payroll                            |
| `student` | students-service                                                |

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

### Rebuild all images from scratch (no cache) - Parallel
```bash
docker compose --profile core --profile hr --profile student build --no-cache
```

### Rebuild all images from scratch (no cache) - Sequential (one at a time)
```bash
docker compose build --no-cache auth-service && \
docker compose build --no-cache employee-service && \
docker compose build --no-cache attendance-service && \
docker compose build --no-cache leave-service && \
docker compose build --no-cache payroll-service && \
docker compose build --no-cache frontend
```

### Rebuild a single service
```bash
docker compose build auth-service
docker compose build attendance-service
docker compose build employee-service
docker compose build frontend
```

### Rebuild a single service with no cache
```bash
docker compose build --no-cache auth-service
docker compose build --no-cache attendance-service
docker compose build --no-cache employee-service
```

### Rebuild and restart a single service (without touching others)
```bash
docker compose up --build -d --no-deps auth-service
docker compose up --build -d --no-deps attendance-service
docker compose up --build -d --no-deps employee-service
docker compose up --build -d --no-deps frontend
```

### Rebuild and restart frontend only
```bash
docker compose up --build -d --no-deps frontend
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
docker compose stop auth-service
docker compose stop attendance-service
docker compose stop employee-service
docker compose stop frontend
```

---

## Restarting

### Restart all services
```bash
docker compose --profile core --profile hr restart
```

### Restart a single service
```bash
docker compose restart auth-service
docker compose restart attendance-service
docker compose restart employee-service
docker compose restart frontend
```

---

## Logs

### View all logs (follow mode)
```bash
docker compose --profile core --profile hr logs -f
```

### View logs for a single service
```bash
docker compose logs -f auth-service
docker compose logs -f attendance-service
docker compose logs -f employee-service
docker compose logs -f frontend
```

### View last 100 lines of a service
```bash
docker compose logs --tail=100 auth-service
docker compose logs --tail=100 attendance-service
docker compose logs --tail=100 employee-service
```

### View logs for multiple services
```bash
docker compose logs -f auth-service employee-service attendance-service
docker compose logs -f auth-service gateway frontend
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
# Auth service
docker exec -it hrms-db psql -U postgres -d auth_db

# Employee service
docker exec -it hrms-db psql -U postgres -d employee_db

# Attendance service
docker exec -it hrms-db psql -U postgres -d attendance_db

# Leave service
docker exec -it hrms-db psql -U postgres -d leave_db

# Payroll service
docker exec -it hrms-db psql -U postgres -d payroll_db

# Students service
docker exec -it hrms-db psql -U postgres -d students_db
```

### Run Alembic migrations for a service
```bash
# Auth service
docker exec -it hrms-auth alembic upgrade head

# Employee service
docker exec -it hrms-employee alembic upgrade head

# Attendance service
docker exec -it hrms-attendance alembic upgrade head

# Leave service
docker exec -it hrms-leave alembic upgrade head
```

### Dump a database
```bash
# Auth
docker exec hrms-db pg_dump -U postgres auth_db > backup_auth.sql

# Attendance
docker exec hrms-db pg_dump -U postgres attendance_db > backup_attendance.sql

# Employee
docker exec hrms-db pg_dump -U postgres employee_db > backup_employee.sql
```

### Restore a database
```bash
# Auth
docker exec -i hrms-db psql -U postgres auth_db < backup_auth.sql

# Attendance
docker exec -i hrms-db psql -U postgres attendance_db < backup_attendance.sql

# Employee
docker exec -i hrms-db psql -U postgres employee_db < backup_employee.sql
```

---

## Attendance Service

### Health check
```bash
curl http://localhost:8002/health
```

### View logs
```bash
docker compose logs -f attendance-service
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

### View database (attendance service DB)
```bash
docker exec -it hrms-db psql -U postgres -d attendance_db
```

### Monitor startup alerts (RabbitMQ)
Events published on startup if stale records > 24h detected:
```bash
# In RabbitMQ management UI, subscribe to:
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

| Service             | Port  |
| ------------------- | ----- |
| Frontend            | 3000  |
| Gateway (nginx)     | 80    |
| Auth Service        | 8000  |
| Employee Service    | 8001  |
| Attendance Service  | 8002  |
| Students Service    | 8003  |
| Payroll Service     | 8004  |
| Leave Service       | 8005  |
| Audit Service       | 8006  |
| Notification Service| 8007  |
| PostgreSQL          | 5432  |
| RabbitMQ AMQP       | 5672  |
| RabbitMQ Management | 15672 |
| Redis               | 6379  |

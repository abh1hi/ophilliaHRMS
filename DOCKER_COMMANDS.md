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

### Rebuild all images from scratch (no cache)
```bash
docker compose --profile core --profile hr --profile student build --no-cache
```

### Rebuild a single service
```bash
docker compose build auth-service
```

### Rebuild a single service with no cache
```bash
docker compose build --no-cache auth-service
```

### Rebuild and restart a single service (without touching others)
```bash
docker compose up --build -d --no-deps auth-service
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
```

### View last 100 lines of a service
```bash
docker compose logs --tail=100 auth-service
```

### View logs for multiple services
```bash
docker compose logs -f auth-service employee-service gateway
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
docker exec -it hrms-db psql -U postgres -d hrms_auth
```

### Run Alembic migrations for a service
```bash
docker exec -it hrms-auth alembic upgrade head
```

### Dump a database
```bash
docker exec hrms-db pg_dump -U postgres hrms_auth > backup_auth.sql
```

### Restore a database
```bash
docker exec -i hrms-db psql -U postgres hrms_auth < backup_auth.sql
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
```

### Run a one-off Python command inside a service
```bash
docker exec -it hrms-auth python -c "print('hello')"
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

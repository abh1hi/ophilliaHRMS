# 07 — Backup & Disaster Recovery Strategy

## Current State: No Backup Strategy Exists

| Component | Backup Method | Status |
|-----------|--------------|--------|
| PostgreSQL (8 DBs) | None | NO BACKUP |
| Redis | AOF on Docker volume | Minimal (local only) |
| RabbitMQ | tmpfs (volatile) | NO PERSISTENCE |
| Application code | Git repository | Safe (remote) |
| Docker images | Local build cache | Rebuildable from source |
| Configuration (.env) | In repository | Safe (but secrets exposed) |
| Uploaded files | Unknown storage | NOT BACKED UP |

---

## Recommended Backup Plan

### Tier 1: PostgreSQL Database Backup

#### Daily Full Backup (pg_dump)

```bash
#!/bin/bash
# /opt/hrms/scripts/backup-db.sh

BACKUP_DIR="/opt/hrms/backups/postgres"
DATE=$(date +%Y-%m-%d_%H%M)
RETENTION_DAYS=30

DATABASES=(auth_db employee_db attendance_db students_db leave_db notification_db audit_db payroll_db)

mkdir -p "$BACKUP_DIR"

for DB in "${DATABASES[@]}"; do
    docker exec hrms-db pg_dump -U postgres -Fc "$DB" > "$BACKUP_DIR/${DB}_${DATE}.dump"

    if [ $? -eq 0 ]; then
        echo "[OK] Backed up $DB"
    else
        echo "[FAIL] Failed to backup $DB" >&2
    fi
done

# Compress all dumps into single archive
tar -czf "$BACKUP_DIR/hrms_full_${DATE}.tar.gz" "$BACKUP_DIR"/*_${DATE}.dump
rm -f "$BACKUP_DIR"/*_${DATE}.dump

# Remove backups older than retention period
find "$BACKUP_DIR" -name "hrms_full_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "[DONE] Backup completed: hrms_full_${DATE}.tar.gz"
```

**Schedule:** Daily at 02:00 AM via cron
```cron
0 2 * * * /opt/hrms/scripts/backup-db.sh >> /var/log/hrms-backup.log 2>&1
```

#### Hourly Incremental Backup (WAL Archiving)

```bash
# PostgreSQL WAL archiving configuration
# Add to docker-compose.yml as custom postgresql.conf mount

archive_mode = on
archive_command = 'cp %p /backups/wal/%f'
wal_level = replica
max_wal_senders = 3
```

```yaml
# docker-compose.yml addition for PostgreSQL
hrms-db:
  volumes:
    - hrms-db-data:/var/lib/postgresql/data
    - ./backups/wal:/backups/wal          # WAL archive mount
    - ./infra/postgresql.conf:/etc/postgresql/custom.conf  # Custom config
  command: postgres -c config_file=/etc/postgresql/custom.conf
```

#### Backup Frequency & Retention

| Backup Type | Frequency | Retention | Storage |
|-------------|-----------|-----------|---------|
| Full dump (pg_dump) | Daily 02:00 | 30 days | Local + Remote |
| WAL segments | Continuous | 7 days | Local + Remote |
| VPS snapshot | Weekly | 4 weeks | Provider storage |

### Tier 2: Remote Backup (Off-Site)

```bash
#!/bin/bash
# /opt/hrms/scripts/sync-backups.sh
# Sync to remote storage (S3, B2, or remote VPS)

# Option A: S3-compatible storage
aws s3 sync /opt/hrms/backups/ s3://hrms-backups/ --delete

# Option B: Backblaze B2
b2 sync /opt/hrms/backups/ b2://hrms-backups/

# Option C: rsync to remote VPS
rsync -avz /opt/hrms/backups/ user@backup-vps:/backups/hrms/
```

**Schedule:** After daily backup
```cron
30 2 * * * /opt/hrms/scripts/sync-backups.sh >> /var/log/hrms-backup-sync.log 2>&1
```

### Tier 3: Redis Backup

Redis AOF file is already persisted to Docker volume. For additional safety:

```bash
#!/bin/bash
# Trigger Redis BGSAVE and copy RDB snapshot
docker exec hrms-redis redis-cli BGSAVE
sleep 5
docker cp hrms-redis:/data/dump.rdb /opt/hrms/backups/redis/dump_$(date +%Y%m%d).rdb
```

---

## Recovery Time & Point Objectives

| Scenario | RPO (Data Loss) | RTO (Downtime) |
|----------|-----------------|----------------|
| Single service crash | 0 (auto-restart) | 30-60 seconds |
| PostgreSQL crash | 0 (WAL recovery) | 1-2 minutes |
| Redis crash | ~1 second (AOF) | 10-30 seconds |
| RabbitMQ restart | ALL queued events | 30 seconds |
| Full VPS loss (with backup) | Up to 24 hours (daily dump) or minutes (WAL) | 1-4 hours |
| Full VPS loss (no backup) | TOTAL LOSS | N/A (unrecoverable) |
| DB corruption (with backup) | Up to last backup | 30-60 minutes |
| Accidental data deletion | Up to last backup | 15-30 minutes (point restore) |

---

## Disaster Recovery Procedures

### Procedure DR1: Full VPS Loss — Recovery from Backup

**Prerequisites:** Backup files available on remote storage. New VPS provisioned.

```bash
# === STEP 1: Provision New VPS ===
# Install Docker, Docker Compose
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin

# === STEP 2: Clone Repository ===
git clone <repo-url> /opt/hrms
cd /opt/hrms

# === STEP 3: Restore Configuration ===
# Copy .env.docker files (should be in secrets manager, not git)
# Update any VPS-specific settings (IP, domain)

# === STEP 4: Start Infrastructure Only ===
docker compose up -d hrms-db hrms-redis rabbitmq
sleep 30  # Wait for PostgreSQL to initialize

# === STEP 5: Restore Database Backup ===
# Download latest backup from remote
aws s3 cp s3://hrms-backups/hrms_full_latest.tar.gz /tmp/

# Extract
tar -xzf /tmp/hrms_full_latest.tar.gz -C /tmp/restore/

# Restore each database
for DB in auth_db employee_db attendance_db students_db leave_db notification_db audit_db payroll_db; do
    docker exec -i hrms-db pg_restore -U postgres -d "$DB" --clean --if-exists \
        < "/tmp/restore/${DB}_latest.dump"
    echo "Restored $DB"
done

# === STEP 6: Apply Pending Migrations ===
# If backup predates latest code, run migrations
for SERVICE in auth employee attendance students payroll leave audit notification; do
    docker compose run --rm ${SERVICE}-service alembic upgrade head
done

# === STEP 7: Start All Services ===
docker compose up -d

# === STEP 8: Verify ===
# Check all health endpoints
for PORT in 8000 8001 8002 8003 8004 8005 8006 8007; do
    curl -s http://localhost:${PORT}/health | jq .
done

# === STEP 9: Update DNS ===
# Point domain to new VPS IP
```

**Estimated time:** 1-4 hours depending on backup size and network speed.

---

### Procedure DR2: Database Corruption — Point-in-Time Recovery

```bash
# === STEP 1: Stop Affected Service ===
docker stop hrms-<service>

# === STEP 2: Identify Corruption ===
docker exec hrms-db psql -U postgres -d <db_name> \
    -c "SELECT * FROM pg_stat_database WHERE datname='<db_name>';"

# === STEP 3: Create Emergency Backup ===
docker exec hrms-db pg_dump -U postgres -Fc <db_name> > /tmp/emergency_<db_name>.dump

# === STEP 4: Drop and Recreate Database ===
docker exec hrms-db psql -U postgres -c "DROP DATABASE IF EXISTS <db_name>;"
docker exec hrms-db psql -U postgres -c "CREATE DATABASE <db_name>;"

# === STEP 5: Restore from Last Good Backup ===
docker exec -i hrms-db pg_restore -U postgres -d <db_name> \
    < /opt/hrms/backups/postgres/<db_name>_latest.dump

# === STEP 6: Apply WAL for Point-in-Time Recovery (if configured) ===
# Requires WAL archiving to be enabled (see Tier 1 above)
# This step replays transactions between backup time and corruption time

# === STEP 7: Restart Service ===
docker start hrms-<service>
```

---

### Procedure DR3: Accidental Data Deletion

```bash
# === STEP 1: IMMEDIATELY Stop Writes ===
# If deletion was via API, the transaction is already committed.
# Stop the affected service to prevent further damage:
docker stop hrms-<service>

# === STEP 2: Check Audit Log ===
# The audit service may have recorded the DELETE event
docker exec hrms-db psql -U postgres -d audit_db \
    -c "SELECT * FROM audit_logs WHERE event_type LIKE '%delete%' ORDER BY timestamp DESC LIMIT 10;"

# === STEP 3: Restore from Backup ===
# Option A: Full database restore (loses all changes since backup)
# Option B: Extract specific table from backup

# Extract single table from backup dump:
docker exec -i hrms-db pg_restore -U postgres -d <db_name> \
    --table=<table_name> --data-only --clean \
    < /opt/hrms/backups/postgres/<db_name>_latest.dump

# === STEP 4: Restart Service ===
docker start hrms-<service>
```

---

## Backup Verification

Backups that aren't tested are not backups. Schedule monthly verification:

```bash
#!/bin/bash
# /opt/hrms/scripts/verify-backup.sh
# Run on a separate VM or local Docker to test restore

# 1. Start temporary PostgreSQL
docker run -d --name pg-verify -e POSTGRES_PASSWORD=test postgres:16-alpine
sleep 10

# 2. Create databases
for DB in auth_db employee_db attendance_db; do
    docker exec pg-verify psql -U postgres -c "CREATE DATABASE $DB;"
done

# 3. Restore latest backup
for DB in auth_db employee_db attendance_db; do
    docker exec -i pg-verify pg_restore -U postgres -d "$DB" \
        < "/opt/hrms/backups/postgres/${DB}_latest.dump"
    echo "Restore $DB: $?"
done

# 4. Verify row counts
for DB in auth_db employee_db attendance_db; do
    echo "=== $DB ==="
    docker exec pg-verify psql -U postgres -d "$DB" \
        -c "SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"
done

# 5. Cleanup
docker rm -f pg-verify
```

---

## Backup Architecture Diagram

```
┌──────────────────────────────────────────────────┐
│                    VPS (Primary)                  │
│                                                    │
│  ┌──────────┐    ┌─────────────────────────────┐ │
│  │PostgreSQL│───▶│ /opt/hrms/backups/postgres/  │ │
│  │ 8 DBs    │    │  daily full dumps            │ │
│  └──────────┘    │  WAL archive (continuous)    │ │
│                   └──────────────┬──────────────┘ │
│  ┌──────────┐                    │                 │
│  │  Redis   │───▶ AOF on volume  │                 │
│  └──────────┘                    │                 │
│                                   │                 │
│  ┌──────────┐                    │                 │
│  │ RabbitMQ │ ← tmpfs (FIX!)    │                 │
│  └──────────┘                    │                 │
│                                   │                 │
└──────────────────────────────────┼─────────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  Remote Storage    │
                          │  (S3 / B2 / VPS)  │
                          │                    │
                          │  30 days retention │
                          │  Encrypted at rest │
                          └────────────────────┘
```

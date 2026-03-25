# Production Failure Playbook & Disaster Recovery Guide

> **System:** OphilliaHRMS
> **Architecture:** Docker-based microservices on single VPS
> **Date:** 2026-03-24
> **Audience:** Engineering, DevOps, SRE

---

## Purpose

This document set serves as the **Production Failure Playbook** for OphilliaHRMS. It covers what happens during every category of failure, how to detect it, how to recover, and how to prevent it.

---

## Document Index

| # | Document | Scope |
|---|----------|-------|
| 01 | [System Overview & SPOFs](01-system-overview.md) | Architecture, service map, dependency graph, single points of failure |
| 02 | [Infrastructure & Container Failures](02-infra-container-failures.md) | VPS down, disk full, OOM, container crash, Docker daemon crash |
| 03 | [Application & Database Failures](03-app-database-failures.md) | Service crash, gateway down, auth down, PostgreSQL crash, Redis failure |
| 04 | [Deployment Failures](04-deployment-failures.md) | Bad deploy, partial deploy, schema mismatch |
| 05 | [Container Lifecycle & Restart Policies](05-container-lifecycle.md) | Stop/start/crash behavior, restart policies, in-flight request impact |
| 06 | [Data Safety & Consistency](06-data-safety.md) | Transaction behavior, crash-time writes, cache-DB consistency, data loss risks |
| 07 | [Backup & Disaster Recovery](07-backup-dr.md) | Backup strategy, RTO/RPO, full VPS loss recovery, DB corruption recovery |
| 08 | [Monitoring & Detection](08-monitoring.md) | What to monitor, alerting strategy, Prometheus/Grafana setup |
| 09 | [HA Improvements & Risk Matrix](09-ha-risk-matrix.md) | Remove SPOFs, redundancy, load balancing, blue-green deploys, risk matrix |
| 10 | [Best Practices & Architecture Diagrams](10-best-practices-diagrams.md) | Graceful shutdown, circuit breakers, idempotency, diagrams |

---

## Critical Findings Summary

### Severity: CRITICAL
| Finding | Impact |
|---------|--------|
| Single PostgreSQL instance, no replication | Total data unavailability on DB failure |
| RabbitMQ uses tmpfs (volatile) | All queued events lost on broker restart |
| No automated backups | No recovery possible from data corruption/loss |
| No HTTPS on gateway | Credentials transmitted in plaintext |
| Redis has no authentication | Any compromised container can manipulate token blacklist |

### Severity: HIGH
| Finding | Impact |
|---------|--------|
| Single VPS — no redundancy | Complete system outage on hardware failure |
| 480 max DB connections (8 services × 60) vs ~100 PG default | Connection exhaustion under load |
| Inconsistent entrypoints (Gunicorn vs raw Uvicorn) | Unreliable graceful shutdown for 6 of 8 services |
| allkeys-lru Redis eviction | Revoked JWT tokens could be re-accepted when cache full |
| Default RabbitMQ credentials (guest/guest) | Security vulnerability |

### Severity: MEDIUM
| Finding | Impact |
|---------|--------|
| No circuit breakers between services | Cascading failures on dependency outage |
| No Prometheus metrics (except audit) | Blind to performance degradation |
| No query timeouts in PostgreSQL | Slow queries can exhaust connection pool |
| Students service runs as root | Container escape risk |

---

## Quick Reference: What to Do When...

| Situation | Action | Document |
|-----------|--------|----------|
| VPS is unreachable | Check provider status, restore from backup | [02](02-infra-container-failures.md), [07](07-backup-dr.md) |
| "502 Bad Gateway" on all pages | Check if gateway or backend containers are running | [03](03-app-database-failures.md) |
| Users can't log in | Check auth-service container, Redis, PostgreSQL | [03](03-app-database-failures.md) |
| Database is corrupted | Stop services, restore from backup, replay WAL | [07](07-backup-dr.md) |
| Container in restart loop | Check `docker logs`, look for OOM or config error | [02](02-infra-container-failures.md), [05](05-container-lifecycle.md) |
| Disk is full | Identify large files, prune Docker, expand volume | [02](02-infra-container-failures.md) |
| Deployment broke everything | Rollback containers, check migration compatibility | [04](04-deployment-failures.md) |
| Events not being processed | Check RabbitMQ management UI, consumer logs | [03](03-app-database-failures.md) |

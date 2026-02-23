# 📊 Logging & Observability Standard

This document defines the requirements for logging, monitoring, and tracing across all HRMS microservices.

## 1. Structured Logging
All microservices must use **Structured JSON Logging**. This allows central log aggregators (ELK, Loki) to parse and index fields efficiently.

### Required Fields
Every log entry must include:
- `timestamp`: ISO-8601 (UTC).
- `level`: INFO, WARN, ERROR, DEBUG.
- `service_name`: The name of the microservice (e.g., `auth-service`).
- `request_id`: A unique UUID for tracing requests across services.
- `message`: Human-readable description.

### Optional but Recommended Fields
- `user_id`: If the request is authenticated.
- `duration_ms`: Latency of the operation.
- `exception`: Full stack trace (only for ERROR level).
- `method` / `path`: HTTP metadata.

---

## 2. Distributed Tracing (Request ID)
To track a single user action across multiple services, a `request_id` must be propagated.

1. **API Gateway**: Generates a new `X-Request-ID` if not present.
2. **Microservices Middleware**: 
   - Extracts `X-Request-ID` from incoming headers.
   - Attaches it to the current logging context.
   - Injects it into any outgoing requests to other services.
   - Returns it in the `X-Request-ID` response header.

---

## 3. Metrics & Monitoring
Every service must expose metrics for Prometheus scraping.

### Standard Metrics (RED Pattern)
- **Requests**: Rate of incoming requests per second.
- **Errors**: Rate of failed requests (5xx status codes).
- **Duration**: Latency distribution (p95, p99).

### Health Checks
Every service must implement a `/health` endpoint that returns:
- `status`: "healthy" or "unhealthy".
- `database`: Connectivity status.
- `broker`: Message broker connectivity (if applicable).

---

## 4. Operational Rules
1. **No Sensitive Data**: Never log passwords, JWT secrets, or PII (Personally Identifiable Information) like full credit card numbers.
2. **Log Levels**:
   - `ERROR`: System failure, database down, 5xx errors. (Triggers alerts).
   - `WARN`: 4xx errors, degraded performance, retries.
   - `INFO`: Normal business flow (e.g., "User logged in").
   - `DEBUG`: Detailed technical info for development.
3. **Log Retention**: Minimum 30 days in the central log store.

---

## 5. Implementation Example (FastAPI)
Using the custom logger defined in `app.core.logging`:

```python
import logging
logger = logging.getLogger(__name__)

@router.post("/process")
async def process(user_id: str, request: Request):
    logger.info(
        "Processing data", 
        extra={
            "request_id": request.state.request_id, 
            "user_id": user_id
        }
    )
```

# ⚠️ Error Handling Standard

To ensure consistency across microservices, all HRMS APIs must follow this error handling standard.

## 1. Response Format
All errors must return a standardized JSON structure.

```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable description of the error",
    "details": {},
    "request_id": "uuid-for-tracing"
  }
}
```

---

## 2. HTTP Status Codes

| Status Code | Usage | Example |
| :--- | :--- | :--- |
| `400 Bad Request` | General client-side error. | Invalid JSON payload. |
| `401 Unauthorized` | Missing or invalid auth. | Expired token. |
| `403 Forbidden` | Valid auth but poor permissions. | Employee trying to access HR payroll. |
| `404 Not Found` | Resource does not exist. | Employee ID not found. |
| `422 Unprocessable Entity` | Pydantic validation failure. | Email missing '@' symbol. |
| `429 Too Many Requests` | Rate limit exceeded. | Too many login attempts. |
| `500 Internal Error` | Server-side crash or unhandled bug. | Database connection lost. |

---

## 3. Error Codes List

| Code | Description |
| :--- | :--- |
| `AUTH_EXPIRED` | JWT token has expired. |
| `AUTH_INVALID` | JWT signature is invalid or tampered. |
| `INSUFFICIENT_PERMISSIONS` | User role does not match requirement. |
| `RESOURCE_NOT_FOUND` | Database lookup failed to find the entity. |
| `VALIDATION_FAILED` | Input fields failed schema checks. |
| `RATE_LIMIT_EXCEEDED` | Request throttled. |

---

## 4. Internal Handling & Logging

1. **Structured Logging**: All errors must be logged in JSON format including the `request_id`.
2. **Do Not Leak Details**: Never return raw Python stack traces or database error messages (e.g., SQL syntax errors) to the client.
3. **Graceful Failures**: If a dependent service (e.g., Notification Service) is down, the primary service (e.g., Leave Service) should log a 503 and return a partial success or a clean error, not a crash.

---

## 5. Implementation in FastAPI

Use the global exception handler to catch unhandled errors and format them.

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": request.state.request_id
            }
        }
    )
```

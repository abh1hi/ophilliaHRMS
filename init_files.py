import os

services = [
    "auth-service",
    "employee-service",
    "attendance-service",
    "payroll-service",
    "leave-service",
    "notification-service",
    "audit-service"
]

root_path = r"c:\Users\abhin\Desktop\ophilliaHRMS"

dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

requirements_content = """fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1
pydantic[email]==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.26.0
asyncpg==0.29.0
"""

main_py_content = """from fastapi import FastAPI
from .api.v1.router import api_router

app = FastAPI(title="{service_name}", version="1.0.0")

@app.get("/health")
async def health_check():
    return {{"status": "healthy", "service": "{service_name}"}}

app.include_router(api_router, prefix="/api/v1")
"""

router_py_content = """from fastapi import APIRouter
from .endpoints import health

api_router = APIRouter()
# api_router.include_router(some_module.router, prefix="/module", tags=["module"])
"""

for service in services:
    service_path = os.path.join(root_path, "services", service)
    
    # Write Dockerfile
    with open(os.path.join(service_path, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)
        
    # Write requirements.txt
    with open(os.path.join(service_path, "requirements.txt"), "w") as f:
        f.write(requirements_content)
        
    # Write empty .env
    with open(os.path.join(service_path, ".env"), "w") as f:
        f.write("# Environment variables")
        
    # Write alembic.ini (basic)
    with open(os.path.join(service_path, "alembic.ini"), "w") as f:
        f.write("# Alembic configuration")
        
    # Write pytest.ini
    with open(os.path.join(service_path, "pytest.ini"), "w") as f:
        f.write("[pytest]\\ntestpaths = tests\\npython_files = test_*.py")
        
    # Write app/main.py
    with open(os.path.join(service_path, "app", "main.py"), "w") as f:
        f.write(main_py_content.format(service_name=service))
        
    # Write app/api/v1/router.py
    with open(os.path.join(service_path, "app", "api", "v1", "router.py"), "w") as f:
        f.write(router_py_content)
        
    # Create empty __init__.py files
    open(os.path.join(service_path, "app", "__init__.py"), "a").close()
    open(os.path.join(service_path, "app", "api", "__init__.py"), "a").close()
    open(os.path.join(service_path, "app", "api", "v1", "__init__.py"), "a").close()
    open(os.path.join(service_path, "app", "api", "v1", "endpoints", "__init__.py"), "a").close()

print("Basic files initialized.")

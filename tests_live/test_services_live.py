import urllib.request
import urllib.error
import urllib.parse
import json
import uuid
from datetime import datetime
import time

BASE_URLS = {
    "auth": "http://localhost:8000/api/v1/auth",
    "employee": "http://localhost:8001/api/v1/employees",
    "attendance": "http://localhost:8002/api/v1",
    "students": "http://localhost:8003/api/v1/students",
    "leave": "http://localhost:8004/api/v1",
    "notification": "http://localhost:8005/api/v1/preferences",
    "gateway": "http://localhost/api/v1"
}

def make_request(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req_data = None
    if data:
        req_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        start = time.time()
        with urllib.request.urlopen(req) as response:
            resp_data = response.read()
            duration = round(time.time() - start, 3)
            try:
                parsed = json.loads(resp_data)
            except json.JSONDecodeError:
                parsed = resp_data.decode("utf-8")
            return response.getcode(), parsed, duration
    except urllib.error.HTTPError as e:
        resp_data = e.read()
        try:
            parsed = json.loads(resp_data)
        except json.JSONDecodeError:
            parsed = resp_data.decode("utf-8")
        return e.code, parsed, 0
    except Exception as e:
        return 0, str(e), 0

def run_tests():
    print("--- HRMS Live Endpoints E2E Test ---")
    results = []
    
    # 1. Auth Service: Register Company
    print("\n[Auth] Registering Company...")
    company_data = {
        "name": f"TestCorp {uuid.uuid4().hex[:6]}",
        "domain": f"test{uuid.uuid4().hex[:6]}.com"
    }
    status, resp, duration = make_request(f"{BASE_URLS['auth']}/companies", "POST", company_data)
    results.append({"step": "Register Company", "status": status, "response": resp})
    print(f"Status: {status}")
    if status != 201 and status != 200:
        print("Failed to register company, attempting to login with defaults if possible.")
        company_id = str(uuid.uuid4())
    else:
        company_id = resp.get("id", str(uuid.uuid4()))

    
    
    # 2. Auth Service: Register User
    print("\n[Auth] Registering User (HR Role)...")
    email = f"hr_{uuid.uuid4().hex[:6]}@example.com"
    password = "SecurePassword123!"
    user_data = {
        "email": email,
        "password": password,
        "role": "hr",
        "company_id": company_id
    }
    status, resp, duration = make_request(f"{BASE_URLS['auth']}/register", "POST", user_data)
    results.append({"step": "Register User", "status": status, "response": resp})
    print(f"Status: {status}")
    if status != 201 and status != 200:
        print("Failed to register user. Attempting login anyway...")

    # 3. Auth Service: Login
    print("\n[Auth] Logging in...")
    login_data = {
        "email": email,
        "password": password
    }
    status, resp, duration = make_request(f"{BASE_URLS['auth']}/login", "POST", login_data)
    results.append({"step": "Login", "status": status, "response": resp})
    print(f"Status: {status}")
    if status != 200:
        print("Failed to login. Cannot proceed to authenticated routes.")
        return results
        
    token = resp.get("access_token", "")
    print("Received access token successfully.")

    # 4. Employee Service: Get Employees
    print("\n[Employee] Getting Employees...")
    status, resp, duration = make_request(f"{BASE_URLS['employee']}/", "GET", token=token)
    results.append({"step": "Get Employees", "status": status, "response": resp})
    print(f"Status: {status}")

    # 5. Attendance Service: Get Attendance Records
    print("\n[Attendance] Getting Attendance Records...")
    # Checking specific endpoint. Since we don't know the exact routes, we'll try `/record` or just base route
    # Looking at typical HRMS patterns, `/api/v1/attendance` usually lists or clocks in. We'll just try `/` on the app.api.v1.router
    status, resp, duration = make_request(f"{BASE_URLS['attendance']}/attendance/me", "GET", token=token)
    results.append({"step": "Get Attendance", "status": status, "response": resp})
    print(f"Status: {status}")
    
    # 6. Leave Service: Get Leave Types
    print("\n[Leave] Getting Leave Types...")
    status, resp, duration = make_request(f"{BASE_URLS['leave']}/leave-types/", "GET", token=token)
    results.append({"step": "Get Leave Types", "status": status, "response": resp})
    print(f"Status: {status}")

    # 7. Students Service: List Students
    print("\n[Students] Listing Students...")
    status, resp, duration = make_request(f"{BASE_URLS['students']}/", "GET", token=token)
    results.append({"step": "List Students", "status": status, "response": resp})
    print(f"Status: {status}")
    
    # 8. Notification Service: Get Preferences
    print("\n[Notification] Getting Preferences...")
    status, resp, duration = make_request(f"{BASE_URLS['notification']}/", "GET", token=token)
    results.append({"step": "Get Preferences", "status": status, "response": resp})
    print(f"Status: {status}")

    return results

if __name__ == "__main__":
    results = run_tests()
    
    with open("tests_live/functional_test_report.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nDetailed functional test report saved to tests_live/functional_test_report.json")

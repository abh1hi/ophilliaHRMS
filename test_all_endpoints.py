import urllib.request
import urllib.error
import urllib.parse
import json
import time
from datetime import datetime

SERVICES = {
    "auth-service": "http://localhost:8000",
    "employee-service": "http://localhost:8001",
    "attendance-service": "http://localhost:8002",
    "students-service": "http://localhost:8003",
    "payroll-service": "http://localhost:8004",
    "leave-service": "http://localhost:8005",
    "audit-service": "http://localhost:8006",
    "notification-service": "http://localhost:8007",
}

ENDPOINTS_TO_TEST = [
    {"path": "/health", "method": "GET"}
]

def test_service(service_name, base_url):
    results = []
    print(f"Testing {service_name} at {base_url}...")
    for ep in ENDPOINTS_TO_TEST:
        url = f"{base_url}{ep['path']}"
        req = urllib.request.Request(url, method=ep["method"])
        start = time.time()
        result = {
            "service": service_name,
            "endpoint": url,
            "duration": 0
        }
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                result["status_code"] = response.getcode()
                content = response.read()
                try:
                    result["response"] = json.loads(content)
                except json.JSONDecodeError:
                    result["response"] = content.decode('utf-8')
                result["error"] = None
        except urllib.error.HTTPError as e:
            result["status_code"] = e.code
            content = e.read()
            try:
                result["response"] = json.loads(content)
            except json.JSONDecodeError:
                result["response"] = content.decode('utf-8')
            result["error"] = str(e)
        except Exception as e:
            result["status_code"] = None
            result["response"] = None
            result["error"] = str(e)
        result["duration"] = round(time.time() - start, 3)
        results.append(result)
    return results

def main():
    all_results = []
    for service, url in SERVICES.items():
        results = test_service(service, url)
        all_results.extend(results)
    
    report_path = "endpoint_test_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": all_results
        }, f, indent=2)
    
    print(f"\nTesting complete. Report saved to {report_path}")
    
    # Print summary
    successful = sum(1 for r in all_results if r["status_code"] == 200)
    failed = len(all_results) - successful
    print(f"Summary: {successful} passed, {failed} failed.\n")
    
    for r in all_results:
        print(f"[{r['status_code']}] {r['service']} {r['endpoint']} - {r['duration']}s")
        if r["status_code"] != 200:
            print(f"  Error: {r['error']}")

if __name__ == "__main__":
    main()

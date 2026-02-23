# Ophillia HRMS - Frontend API Integration Guide

This document outlines the available REST API endpoints across the completed microservices (`auth-service`, `employee-service`, `attendance-service`) to help frontend developers seamlessly integrate the application logic with the user interface.

## 1. Authentication & Authorization Structure

All services rely on JWT (JSON Web Tokens) for stateless authentication.
- **Login / Token Generation:** Use the Auth service to get an `access_token`.
- **Authorization Header:** Include the token in the headers for all protected requests:
  `Authorization: Bearer <your_access_token>`
- **Role-Based Access Control (RBAC):** Users fall into 4 primary roles: `super_admin`, `hr`, `manager`, `employee`. Certain endpoints will automatically return `403 Forbidden` if the user's role is not authorized.

---

## 2. API Gateway Routing

Assuming the API Gateway is running on `http://localhost:8000` locally, requests are efficiently routed as follows:
- Auth Service: `http://localhost:8000/api/v1/auth`
- Employee Service: `http://localhost:8000/api/v1/employees` & `/api/v1/departments`
- Attendance Service: `http://localhost:8000/api/v1/attendance`

---

## 3. Auth Service Endpoints

### 3.1. Register User (Public)
- **Endpoint:** `POST /api/v1/auth/register`
- **Description:** Register a new user account safely.
- **Body Context:**
  ```json
  {
    "email": "user@example.com",
    "password": "yourpassword123",
    "role": "employee" 
  }
  ```
- *(Valid Roles: `super_admin`, `hr`, `manager`, `employee`)*

### 3.2. Login user
- **Endpoint:** `POST /api/v1/auth/login`
- **Description:** Authenticates a user securely and returns JWTs.
- **Body Context:**
  ```json
  {
    "email": "user@example.com",
    "password": "yourpassword123"
  }
  ```
- **Response Structure:** `200 OK`
  ```json
  {
    "access_token": "eyJhb...",
    "refresh_token": "uuid:secret",
    "token_type": "bearer"
  }
  ```

### 3.3. Get Current User Data
- **Endpoint:** `GET /api/v1/auth/me`
- **Headers:** `Authorization: Bearer <token>`
- **Response:** Returns the current logged-in user's system data (ID UUID, Email, Role Strings, status bool).

---

## 4. Employee Service Endpoints

### 4.1. Get Current Logged-in Employee Profile
- **Endpoint:** `GET /api/v1/employees/profile/me` 
- **Headers:** `Authorization: Bearer <token>`
- **Description:** Fetches the granular employee profile explicitly linked to the authenticated user.

### 4.2. Create Employee Profile (Admin Only)
- **Endpoint:** `POST /api/v1/employees`
- **Headers:** `Authorization: Bearer <token>`
- **RBAC Strict:** `super_admin` only
- **Body Payload Context:**
  ```json
  {
    "user_id": "uuid-from-auth-service-me-response",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "department_id": "uuid-of-department",
    "designation": "Software Engineer",
    "date_of_joining": "2024-01-01"
  }
  ```

### 4.3. List Employee Matrix
- **Endpoint:** `GET /api/v1/employees`
- **Headers:** `Authorization: Bearer <token>`
- **RBAC Strict:** `super_admin`, `hr`, `manager`
- **Query Params:** `skip` (default: 0), `limit` (default: 100), `department_id` (optional).

### 4.4. Manage Departments Strategy
- **Create:** `POST /api/v1/departments` (Role Strict: `super_admin`)
  ```json
  { "name": "Engineering", "description": "Tech team", "manager_id": "optional-uuid" }
  ```
- **List:** `GET /api/v1/departments` (Available to all authenticated users)

---

## 5. Attendance Service Endpoints

### 5.1. Daily Clock-In Action
- **Endpoint:** `POST /api/v1/attendance/clock-in`
- **Headers:** `Authorization: Bearer <token>`
- **Body Payload (Optional Location Data):**
  ```json
  {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "notes": "Working from office"
  }
  ```
- **Response Strategy:** `201 Created`

### 5.2. Daily Clock-Out Action
- **Endpoint:** `POST /api/v1/attendance/clock-out`
- **Headers:** `Authorization: Bearer <token>`
- **Body Payload:** Similar format to Clock In.

### 5.3. Extract My Attendance History Array
- **Endpoint:** `GET /api/v1/attendance`
- **Headers:** `Authorization: Bearer <token>`
- **Query Params:** `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD), `skip`, `limit`.

### 5.4. School Mode (Admin Bulk Attendance Feature)
- **Endpoint:** `POST /api/v1/attendance/school-mode`
- **Headers:** `Authorization: Bearer <token>`
- **RBAC Strict:** `super_admin`, `hr`
- **Description:** Allows an admin/HR to directly mark an employee as present/late/absent for the full day without them actively clocking in.
- **Body Payload Requirement:**
  ```json
  {
    "employee_id": "uuid-of-employee",
    "status": "present",
    "notes": "Marked present locally by HR terminal"
  }
  ```
*(Status options mapping: `present`, `late`, `half_day`, `absent`)*

---

## Expected Error Handling Models

Please wrap components to handle standard HTTP status codes:
- `200/201`: **Success** - (Green Toast UI)
- `400`: **Bad Request** - (Invalid logic error, e.g., already clocked in or email used)
- `401`: **Unauthorized** - (Missing or invalid token, push user to login screen)
- `403`: **Forbidden** - (User lacks the required RBAC role, present a "No Access rights" dialogue)
- `404`: **Not Found** - (Resource entity misdirected)
- `422`: **Unprocessable Entity** - (Pydantic Validation Error - frontend usually failed submitting correct data types under JSON)
- `500`: **Server Architecture Error** - (Backend misfire)

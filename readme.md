# CS432 - Module 3 

This Flask API implements Task 1 (Member Creation) and Task 2 (Role-Based Access Control - RBAC) for the CS432 Module 3 assignment
A short demo is linked [here](https://youtu.be/tmyJm6wDxZ0?si=6SoHsK6UKPl0U3dr).

## Prerequisites

* Python 3.8+
* pip (Python package installer)
* Access to the CS432 CIMS Database (`10.0.116.125`) with Group 2 (`cs432g2`) credentials.

## Setup Instructions

1. **Clone the repository:**

   ```
   cs432_project_g2/
   ├── app/
   │   ├── __init__.py
   │   ├── auth/
   │   │   ├── __init__.py
   │   │   ├── routes.py     # Contains /login
   │   │   └── decorators.py # Contains @token_required
   │   ├── members/
   │   │   ├── __init__.py
   │   │   └── routes.py     # Contains /admin/add_member, /profile/*
   │   └── utils/
   │       ├── __init__.py
   │       └── database.py   # DB connection helper
   ├── logs/                 # Log files stored here
   │   └── app.log
   ├── config.py             # Main configuration
   └── run.py                # Script to start the app
   ```

2. **Navigate to the project root directory:**

   ```bash
   cd /path/to/cs432_project_g2
   ```

3. **Create and activate a virtual environment (highly recommended):**

   ```bash
   python3 -m venv mod3
   ```

   On Windows:

   ```bash
   .\mod3\Scripts\activate
   ```

   On macOS/Linux:

   ```bash
   source mod3/bin/activate
   ```

4. **Install required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Ensure your virtual environment is activated.
2. Make sure you are in the project root directory (`cs432_project_g2/`).
3. Execute the run script:

   ```bash
   python run.py
   ```

4. The Flask development server will start, typically listening on `http://0.0.0.0:5001`. You can access it via `http://localhost:5001` or your machine's local IP address on port 5001.
5. Log messages (including errors) will be printed to the console and saved in the `logs/app.log` file.

## Implemented Features (Tasks 1 & 2)

* **Local Authentication (`/login` - POST):**
  * Authenticates users by directly checking credentials (`user`=`MemberID`, `password`) against the `cs432cims.Login` table.
  * Generates a JWT `session_token` upon successful login, containing the user's ID (`sub`) and `Role`.

* **Task 1: Member Creation (`/admin/add_member` - POST):**
  * Requires a valid JWT Bearer token from an **admin** user (obtained via `/login`).
  * Accepts `{"name": "...", "email": "..."}` in the JSON body.
  * Inserts the new member into the `cs432cims.members` table (using `UserName`, `emailID` columns).
  * Retrieves the new member's `ID`.
  * Hashes the `DEFAULT_PASSWORD`.
  * Inserts a corresponding record into the `cs432cims.Login` table (using `MemberID`, `Password`, `Role='user'` columns).

* **Task 2: Role-Based Access Control (RBAC):**
  * Implemented using the `@token_required` decorator which validates JWTs and extracts user ID and role.
  * Admin-specific routes (`/admin/add_member`, `/admin/profile/<id>`) contain explicit checks to ensure `role == 'admin'`. Non-admins attempting access receive a `403 Forbidden` error.
  * General authenticated routes (`/profile/me`) only require a valid token (any role) via the decorator.

## Testing with `curl`

These commands demonstrate the implemented features.

**Note:**

* Run these commands from your terminal.
* Replace `localhost:5001` if your API server is running on a different address/port.
* Replace `YOUR_ADMIN_TOKEN_HERE` and `YOUR_USER_TOKEN_HERE` with the actual `session_token` values obtained from the corresponding login commands.

### 1. Login as Admin (User 447)  
**Purpose:** Get an Admin Token

```bash
curl -X POST http://localhost:5001/login \
     -H "Content-Type: application/json" \
     -d '{"user": "447", "password": "1234"}'
```

Use `{"user": "1137", "password": "XiLV9wEWdi"}` for non-admin token.  
(Copy the `session_token` from the successful JSON output)

> Replace `YOUR_TOKEN_HERE` with the token from step 1 in the below steps.

### 2. Add New Member (Task 1 Test - Requires Admin Token)  
**Purpose:** Verify admin can create a member.

```bash
curl -X POST http://localhost:5001/admin/add_member \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -d '{"name": "New User via Curl", "email": "new.curl@example.com"}'
```

### 3. Get Own Profile (Task 2 Test - Requires Any Valid Token)  
**Purpose:** Verify any logged-in user can view their own profile.

```bash
curl -X GET http://localhost:5001/profile/me \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Attempt Admin Action as User (Task 2 Test - Expect 403)  
**Purpose:** Verify non-admin cannot access admin-only routes.  
_Attempt to view Admin 447's profile_

```bash
curl -X GET http://localhost:5001/admin/profile/447 \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 5. (Optional) Frontend Setup

If you plan to connect a React frontend to this Flask API, install the following dependencies:

```bash
npm install axios
npm install react-router-dom




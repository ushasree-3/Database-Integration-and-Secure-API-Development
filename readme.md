# CS432 - Module 3 

This Flask API implements Task 1 (Member Creation) and Task 2 (Role-Based Access Control - RBAC) for the CS432 Module 3 assignment

## Prerequisites

*   Python 3.8+
*   pip (Python package installer)
*   Access to the CS432 CIMS Database (`10.0.116.125`) with Group 2 (`cs432g2`) credentials.

## Setup Instructions

1.  **Clone the repository (if applicable) or ensure code structure:**
    Make sure your project follows the modular structure:
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

2.  **Navigate to the project root directory:**
    ```bash
    cd /path/to/cs432_project_g2
    ```

3.  **Create and activate a virtual environment (highly recommended):**
    ```bash
    python3 -m venv mod3
    # On Windows: .\mod3\Scripts\activate
    # On macOS/Linux: source mod3/bin/activate
    ```

4.  **Install required dependencies:**
    ```bash
    # Optional: Create a requirements.txt file: pip freeze > requirements.txt
    # Then install using: pip install -r requirements.txt
    ```

## Configuration (**CRITICAL**)

Before running the application, you **must** configure it correctly:

1.  **Edit `config.py`:**
    *   **`SECRET_KEY`**: Replace the placeholder value with a long, random, and secret string. This is essential for JWT security.
    *   **`DB_PASSWORD`**: Ensure this matches the actual database password for the `cs432g2` user.

2.  **Verify Password Hashing Logic:**
    *   **Examine `cs432cims.Login` Table:** Use phpMyAdmin to check how passwords are *actually* stored for the users you need to log in (especially admins like user 447). Are they plain text, MD5 hashes (32 hex characters), or Bcrypt hashes (starting `$2b$...` or similar)?
    *   **Edit `app/auth/routes.py`:** Find the `local_login` function. Inside the `# --- !!! IMPORTANT: Password Verification Logic !!! ---` section, **ensure the code correctly checks the password based on how it's stored**. The current code prioritizes Bcrypt, then MD5, then Plain Text. Modify or uncomment the correct check if needed. **If this doesn't match, login will fail.**
    *   **Edit `app/members/routes.py`:** Find the `add_member_task1` function. Verify the line `hashed_default_password = hashlib.md5(DEFAULT_PASSWORD.encode()).hexdigest()` correctly reflects how you want to store the `DEFAULT_PASSWORD` for *new* users. (Currently MD5 for consistency, but using Bcrypt is recommended if possible - ensure the login check handles it).

3.  **Verify Database/Table/Column Names:**
    *   Double-check the exact names (including capitalization) used in the SQL queries within `app/auth/routes.py` and `app/members/routes.py` against the actual names in phpMyAdmin (e.g., `Login` vs `login`, `MemberID` vs `memberid`, `Password` vs `password`, `members` vs `Members`, `UserName` vs `username`, `emailID` vs `emailid`). Make sure they match perfectly.

## Running the Application

1.  Ensure your virtual environment is activated.
2.  Make sure you are in the project root directory (`cs432_project_g2/`).
3.  Execute the run script:
    ```bash
    python run.py
    ```
4.  The Flask development server will start, typically listening on `http://0.0.0.0:5001`. You can access it via `http://localhost:5001` or your machine's local IP address on port 5001.
5.  Log messages (including errors) will be printed to the console and saved in the `logs/app.log` file.

## Implemented Features (Tasks 1 & 2)

*   **Local Authentication (`/login` - POST):**
    *   Authenticates users by directly checking credentials (`user`=`MemberID`, `password`) against the `cs432cims.Login` table.
    *   Generates a JWT `session_token` upon successful login, containing the user's ID (`sub`) and `Role`.
*   **Task 1: Member Creation (`/admin/add_member` - POST):**
    *   Requires a valid JWT Bearer token from an **admin** user (obtained via `/login`).
    *   Accepts `{"name": "...", "email": "..."}` in the JSON body.
    *   Inserts the new member into the `cs432cims.members` table (using `UserName`, `emailID` columns).
    *   Retrieves the new member's `ID`.
    *   Hashes the `DEFAULT_PASSWORD`.
    *   Inserts a corresponding record into the `cs432cims.Login` table (using `MemberID`, `Password`, `Role='user'` columns).
*   **Task 2: Role-Based Access Control (RBAC):**
    *   Implemented using the `@token_required` decorator which validates JWTs and extracts user ID and role.
    *   Admin-specific routes (`/admin/add_member`, `/admin/profile/<id>`) contain explicit checks to ensure `role == 'admin'`. Non-admins attempting access receive a `403 Forbidden` error.
    *   General authenticated routes (`/profile/me`) only require a valid token (any role) via the decorator.

## Testing with `curl`

These commands demonstrate the implemented features.

**Note:**
*   Run these commands from your terminal.
*   Replace `localhost:5001` if your API server is running on a different address/port.
*   Replace `YOUR_ADMIN_TOKEN_HERE` and `YOUR_USER_TOKEN_HERE` with the actual `session_token` values obtained from the corresponding login commands.

**1. Login as Admin (User 447):**
   *Purpose: Get an Admin Token*
   ```bash
   curl -X POST http://localhost:5001/login \
        -H "Content-Type: application/json" \
        -d '{"user": "447", "password": "1234"}'
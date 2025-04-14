# app/members/routes.py
from flask import request, jsonify, current_app, Blueprint
import mysql.connector
import hashlib

# Import helpers and decorators
from ..utils.database import get_cims_db_connection
from ..auth.decorators import token_required

# Create the Blueprint instance
members_bp = Blueprint('members', __name__) # 'members' is the blueprint name

# --- Task 1 Endpoint: Add Member (Admin Only) ---
@members_bp.route('/admin/add_member', methods=['POST'])
@token_required
def add_member_task1(current_user_id, current_user_role):
    """Task 1: Adds member/login. Requires LOCAL Admin auth."""
    current_app.logger.info(f"Request: /admin/add_member by user ID: {current_user_id}, Role: {current_user_role}")

    if current_user_role != 'admin':
        current_app.logger.warning(f"Access denied: User {current_user_id} (Role: {current_user_role}) is not admin.")
        return jsonify({"error": "Admin privileges required"}), 403

    current_app.logger.info(f"Admin user {current_user_id} authorized. Adding member.")

    try:
        data = request.get_json()
        if not data or 'name' not in data or 'email' not in data:
            current_app.logger.warning("Missing 'name' or 'email' in add_member request")
            return jsonify({"error": "Missing 'name' or 'email' in request JSON body"}), 400
        new_name = data['name']
        new_email = data['email']
    except Exception as e:
        current_app.logger.error(f"Error parsing add_member request JSON: {e}")
        return jsonify({"error": "Invalid JSON data in request body"}), 400

    conn = None
    cursor = None
    new_member_id = None
    try:
        conn = get_cims_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()

        # Insert into members (Use correct column names: UserName, emailID)
        sql_insert_member = "INSERT INTO members (UserName, emailID) VALUES (%s, %s)"
        cursor.execute(sql_insert_member, (new_name, new_email))
        current_app.logger.info(f"Executed INSERT members for '{new_name}'.")

        new_member_id = cursor.lastrowid
        if not new_member_id:
            raise mysql.connector.Error("Failed to retrieve last inserted ID from members.")
        current_app.logger.info(f"New member ID: {new_member_id}")

        # Hash default password (using MD5 for consistency as decided earlier)
        default_password = current_app.config['DEFAULT_PASSWORD']
        hashed_default_password = hashlib.md5(default_password.encode()).hexdigest()

        # Insert into Login (Use correct table and column names: Login, MemberID, Password, Role)
        sql_insert_login = "INSERT INTO Login (MemberID, Password, Role) VALUES (%s, %s, %s)"
        cursor.execute(sql_insert_login, (new_member_id, hashed_default_password, 'user')) # Default role 'user'
        current_app.logger.info(f"Executed INSERT Login for MemberID {new_member_id}.")

        conn.commit()
        current_app.logger.info(f"DB transaction committed for new member {new_member_id}.")

        return jsonify({
            "message": "Task 1 Success: Member created and login entry added (using local auth).",
            "member_id": new_member_id,
            "MemberID": new_member_id,
        }), 201

    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Database Error during Task 1: {db_err}")
        if conn: conn.rollback(); current_app.logger.info("DB transaction rolled back.")
        # Check specifically for duplicate key error
        if db_err.errno == 1062: # MySQL error code for duplicate entry
             return jsonify({"error": "Duplicate entry detected. MemberID might already exist in Login table.", "details": str(db_err)}), 409 # 409 Conflict
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error during Task 1: {e}", exc_info=True)
        if conn: conn.rollback(); current_app.logger.info("DB transaction rolled back.")
        return jsonify({"error": "An internal server error occurred", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# --- Task 2 Demo: View Own Profile ---
@members_bp.route('/profile/me', methods=['GET'])
@token_required
def get_my_profile(current_user_id, current_user_role):
    """Allows any authenticated user to view their own profile."""
    current_app.logger.info(f"Request: /profile/me by user ID: {current_user_id}, Role: {current_user_role}")
    conn = None
    cursor = None
    try:
        conn = get_cims_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Use correct column names (ID, UserName, emailID, DoB)
        sql_select_me = "SELECT ID, UserName, emailID, DoB FROM members WHERE ID = %s"
        cursor.execute(sql_select_me, (current_user_id,))
        profile_data = cursor.fetchone()

        if not profile_data:
            current_app.logger.warning(f"Profile data not found for user ID: {current_user_id}")
            return jsonify({"error": "Profile data not found"}), 404

        current_app.logger.info(f"Retrieved profile for user ID: {current_user_id}")
        return jsonify(profile_data), 200

    except mysql.connector.Error as db_err:
         current_app.logger.error(f"Database Error in /profile/me: {db_err}")
         return jsonify({"error": "Database error", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in /profile/me: {e}", exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# --- Task 2 Demo: View Any Profile (Admin Only) ---
@members_bp.route('/admin/profile/<int:target_member_id>', methods=['GET'])
@token_required
def get_any_profile(current_user_id, current_user_role, target_member_id):
    """Allows ONLY admins to view any member profile by ID."""
    current_app.logger.info(f"Request: /admin/profile/{target_member_id} by user ID: {current_user_id}, Role: {current_user_role}")

    if current_user_role != 'admin':
        current_app.logger.warning(f"Access denied: User {current_user_id} (Role: {current_user_role}) is not admin for /admin/profile.")
        return jsonify({"error": "Admin privileges required"}), 403

    current_app.logger.info(f"Admin user {current_user_id} authorized. Fetching profile for target: {target_member_id}")
    conn = None
    cursor = None
    try:
        conn = get_cims_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Use correct column names
        sql_select_target = "SELECT ID, UserName, emailID, DoB FROM members WHERE ID = %s"
        cursor.execute(sql_select_target, (target_member_id,))
        profile_data = cursor.fetchone()

        if not profile_data:
            current_app.logger.warning(f"Admin {current_user_id} requested non-existent profile ID: {target_member_id}")
            return jsonify({"error": f"Member with ID {target_member_id} not found"}), 404

        current_app.logger.info(f"Admin {current_user_id} retrieved profile for ID: {target_member_id}")
        return jsonify(profile_data), 200

    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Database Error in /admin/profile: {db_err}")
        return jsonify({"error": "Database error", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in /admin/profile: {e}", exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
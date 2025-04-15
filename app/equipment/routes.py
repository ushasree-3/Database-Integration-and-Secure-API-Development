# app/equipment/routes.py
from flask import Blueprint, request, jsonify, current_app
import mysql.connector
import datetime
import logging

from ..auth.decorators import token_required
from ..utils.database import get_project_db_connection
# Import helpers needed
from ..utils.helpers import check_member_exists, is_equipment_issuable

equipment_bp = Blueprint('equipment', __name__)

# --- EQUIPMENT CRUD ---

# 1. Add Equipment Type (POST /equipment/) - Admin or EqManager
@equipment_bp.route('/', methods=['POST'])
@token_required
def add_equipment(current_user_id, current_user_role):
    """Adds a new type of equipment. Requires Admin or EqManager role."""
    current_app.logger.info(f"Request: Add Equipment by User ID: {current_user_id}")
    # Use correct role name from DB Login table
    allowed_roles = ['admin', 'EqManager']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    try:
        data = request.get_json()
        name = data.get('equipment_name')
        # Note: IsAvailable defaults to TRUE in DB, Condition required
        condition = data.get('condition') # Should be 'Good', 'Fair', or 'Poor'
        last_checked_str = data.get('last_checked_date') # Optional, YYYY-MM-DD

        if not name or not condition:
            return jsonify({"error": "Missing fields: equipment_name, condition"}), 400

        # Validate condition ENUM
        valid_conditions = ['Good', 'Fair', 'Poor']
        if condition not in valid_conditions:
            return jsonify({"error": f"Invalid condition. Must be one of: {valid_conditions}"}), 400

        last_checked = None
        if last_checked_str:
            try: last_checked = datetime.date.fromisoformat(last_checked_str)
            except ValueError: return jsonify({"error": "Invalid date format for last_checked_date"}), 400

    except Exception as e:
        return jsonify({"error": "Invalid JSON data"}), 400

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        # Assumes Equipment(EquipmentID PK AI, EquipmentName, IsAvailable BOOL DEF TRUE, Condition_ ENUM, LastCheckedDate DATE)
        sql = """
            INSERT INTO Equipment (EquipmentName, Condition_, LastCheckedDate)
            VALUES (%s, %s, %s)
        """
        # IsAvailable defaults to TRUE
        cursor.execute(sql, (name, condition, last_checked))
        new_equip_id = cursor.lastrowid
        conn.commit()
        current_app.logger.info(f"User {current_user_id} added Equipment ID: {new_equip_id}")
        return jsonify({"message": "Equipment added", "EquipmentID": new_equip_id}), 201

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        # Handle potential UNIQUE constraint on EquipmentName if defined
        current_app.logger.error(f"DB Error adding equipment: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error adding equipment: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 2. List Equipment (GET /equipment/) - Any Authenticated User
@equipment_bp.route('/', methods=['GET'])
@token_required
def list_equipment(current_user_id, current_user_role):
    """Lists all equipment types."""
    current_app.logger.info(f"Request: List Equipment by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT EquipmentID, EquipmentName, IsAvailable, Condition_,
                   DATE_FORMAT(LastCheckedDate, '%Y-%m-%d') as LastCheckedDate
            FROM Equipment ORDER BY EquipmentName
        """
        cursor.execute(sql)
        equipment = cursor.fetchall()
        # Convert IsAvailable (0/1) to boolean for JSON if needed
        for item in equipment:
            item['IsAvailable'] = bool(item['IsAvailable'])
        return jsonify(equipment), 200
    except Exception as e:
        current_app.logger.error(f"Error listing equipment: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve equipment"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 3. Get Equipment Details (GET /equipment/<id>) - Any Authenticated User
@equipment_bp.route('/<int:equipment_id>', methods=['GET'])
@token_required
def get_equipment(current_user_id, current_user_role, equipment_id):
    """Gets details for a specific equipment item."""
    current_app.logger.info(f"Request: Get Equipment ID: {equipment_id} by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT EquipmentID, EquipmentName, IsAvailable, Condition_,
                   DATE_FORMAT(LastCheckedDate, '%Y-%m-%d') as LastCheckedDate
            FROM Equipment WHERE EquipmentID = %s
        """
        cursor.execute(sql, (equipment_id,))
        item = cursor.fetchone()
        if not item: return jsonify({"error": f"Equipment ID {equipment_id} not found"}), 404
        item['IsAvailable'] = bool(item['IsAvailable'])
        # Enhancement: Could fetch borrow history from EquipmentLog here
        return jsonify(item), 200
    except Exception as e:
        current_app.logger.error(f"Error getting equipment {equipment_id}: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve equipment"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 4. Update Equipment Details (PUT /equipment/<id>) - Admin or EqManager
@equipment_bp.route('/<int:equipment_id>', methods=['PUT'])
@token_required
def update_equipment(current_user_id, current_user_role, equipment_id):
    """Updates equipment details. Requires Admin or EqManager role."""
    current_app.logger.info(f"Request: Update Equipment ID: {equipment_id} by User ID: {current_user_id}")
    allowed_roles = ['admin', 'EqManager']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    try:
        data = request.get_json()
        # Only allow updating condition, availability, and last checked date? Name is usually fixed.
        condition = data.get('condition')
        is_available_val = data.get('is_available') # Expect true/false
        last_checked_str = data.get('last_checked_date')

        if condition is None and is_available_val is None and last_checked_str is None:
             return jsonify({"error": "No update fields provided (condition, is_available, last_checked_date)"}), 400

        # Validate inputs
        if condition is not None and condition not in ['Good', 'Fair', 'Poor']:
             return jsonify({"error": "Invalid condition value"}), 400
        if is_available_val is not None and not isinstance(is_available_val, bool):
             return jsonify({"error": "is_available must be true or false"}), 400

        last_checked = None
        if last_checked_str:
            try: last_checked = datetime.date.fromisoformat(last_checked_str)
            except ValueError: return jsonify({"error": "Invalid date format for last_checked_date"}), 400

    except Exception as e:
        return jsonify({"error": "Invalid JSON data"}), 400

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()

        # Build dynamic update
        update_fields = []
        update_values = []
        if condition is not None:
             update_fields.append("Condition_ = %s")
             update_values.append(condition)
        if is_available_val is not None:
             update_fields.append("IsAvailable = %s")
             update_values.append(is_available_val)
        if last_checked is not None:
             update_fields.append("LastCheckedDate = %s")
             update_values.append(last_checked)

        if not update_fields: return jsonify({"error": "No valid fields to update"}), 400 # Should not happen

        sql = f"UPDATE Equipment SET {', '.join(update_fields)} WHERE EquipmentID = %s"
        update_values.append(equipment_id)

        cursor.execute(sql, tuple(update_values))

        if cursor.rowcount == 0: return jsonify({"error": f"Equipment ID {equipment_id} not found"}), 404

        conn.commit()
        current_app.logger.info(f"User {current_user_id} updated Equipment ID: {equipment_id}")
        return jsonify({"message": "Equipment updated", "EquipmentID": equipment_id}), 200

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        current_app.logger.error(f"DB Error updating equipment {equipment_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error updating equipment {equipment_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 5. Delete Equipment Type (DELETE /equipment/<id>) - Admin or EqManager
@equipment_bp.route('/<int:equipment_id>', methods=['DELETE'])
@token_required
def delete_equipment(current_user_id, current_user_role, equipment_id):
    """Deletes an equipment type. Requires Admin or EqManager role."""
    current_app.logger.info(f"Request: Delete Equipment ID: {equipment_id} by User ID: {current_user_id}")
    allowed_roles = ['admin', 'EqManager']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        sql = "DELETE FROM Equipment WHERE EquipmentID = %s"
        cursor.execute(sql, (equipment_id,))
        if cursor.rowcount == 0: return jsonify({"error": f"Equipment ID {equipment_id} not found"}), 404
        conn.commit()
        current_app.logger.info(f"User {current_user_id} deleted Equipment ID: {equipment_id}")
        return jsonify({"message": "Equipment deleted", "EquipmentID": equipment_id}), 200
    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        if db_err.errno == 1451: # FK constraint (Logs might reference it)
             current_app.logger.warning(f"FK constraint fail delete equipment {equipment_id}: {db_err}")
             return jsonify({"error": "Cannot delete equipment, related logs exist."}), 409
        current_app.logger.error(f"DB Error deleting equipment {equipment_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error deleting equipment {equipment_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# --- EQUIPMENT LOG Routes ---

# 6. Borrow Equipment (POST /equipment/logs/borrow) - Many roles
@equipment_bp.route('/logs/borrow', methods=['POST'])
@token_required
def borrow_equipment(current_user_id, current_user_role):
    """Logs borrowing of equipment. Allowed by Admin, EqManager, Coach, Player."""
    current_app.logger.info(f"Request: Borrow Equipment by User ID: {current_user_id}")
    # Define roles allowed to borrow - adjust as needed
    allowed_roles = ['admin', 'EqManager', 'Coach', 'Player', 'Organizer']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"Your role ({current_user_role}) cannot borrow equipment"}), 403

    try:
        data = request.get_json()
        equipment_id = data.get('equipment_id')
        issued_to_id = data.get('issued_to') # MemberID borrowing
        if not equipment_id or not issued_to_id:
            return jsonify({"error": "Missing fields: equipment_id, issued_to"}), 400
        equipment_id = int(equipment_id)
        issued_to_id = int(issued_to_id)
        # Use current time for IssueDate
        issue_date = datetime.datetime.now(datetime.timezone.utc)

    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid JSON data or non-integer ID"}), 400

    # --- Validation ---
    if not check_member_exists(issued_to_id): return jsonify({"error": f"Member {issued_to_id} not found"}), 404
    # Check equipment issuability (availability + condition)
    issuable, reason = is_equipment_issuable(equipment_id)
    if not issuable:
        current_app.logger.info(f"Equipment {equipment_id} not issuable: {reason}")
        return jsonify({"error": reason}), 409
        
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        # --- Use Transaction ---
        # conn.start_transaction() # Explicit transaction needed for multi-step
        cursor = conn.cursor()
        # Assumes EquipmentLog(LogID PK AI, EquipmentID FK, IssuedTo FK(cims), IssueDate DT, ReturnDate DT NULL)
        sql_log = "INSERT INTO EquipmentLog (EquipmentID, IssuedTo, IssueDate) VALUES (%s, %s, %s)"
        cursor.execute(sql_log, (equipment_id, issued_to_id, issue_date))
        new_log_id = cursor.lastrowid

        # Trigger mark_equipment_unavailable should handle setting IsAvailable = FALSE
        # If trigger doesn't exist or fails, uncomment below:
        # sql_update_equip = "UPDATE Equipment SET IsAvailable = FALSE WHERE EquipmentID = %s"
        # cursor.execute(sql_update_equip, (equipment_id,))

        conn.commit()
        current_app.logger.info(f"User {current_user_id} logged borrow for EquipID {equipment_id} to MemberID {issued_to_id} (LogID: {new_log_id})")
        return jsonify({"message": "Equipment issued", "LogID": new_log_id}), 201

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        # Trigger check_equipment_before_issue might raise SQLSTATE 45000
        # Check db_err.sqlstate and db_err.msg for trigger errors
        if db_err.sqlstate == '45000':
             current_app.logger.warning(f"Borrow rejected by DB trigger for EquipID {equipment_id}: {db_err.msg}")
             return jsonify({"error": f"Borrow failed: {db_err.msg}"}), 409 # Conflict based on trigger
        current_app.logger.error(f"DB Error borrowing equipment {equipment_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error borrowing equipment {equipment_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 7. Return Equipment (PUT /equipment/logs/<log_id>/return) - Many roles
@equipment_bp.route('/logs/<int:log_id>/return', methods=['PUT'])
@token_required
def return_equipment(current_user_id, current_user_role, log_id):
    """Logs the return of equipment. Allowed by Admin, EqManager, Coach, Player."""
    current_app.logger.info(f"Request: Return Equipment LogID: {log_id} by User ID: {current_user_id}")
    # Adjust allowed roles if needed
    allowed_roles = ['admin', 'EqManager', 'Coach', 'Player', 'Organizer']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"Your role ({current_user_role}) cannot process returns"}), 403

    # Get condition on return (optional)
    condition_on_return = request.json.get('condition') if request.is_json else None
    if condition_on_return and condition_on_return not in ['Good', 'Fair', 'Poor']:
         return jsonify({"error": "Invalid condition value on return"}), 400

    # Use current time for ReturnDate
    return_date = datetime.datetime.now(datetime.timezone.utc)

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500

        # --- Check if already returned ---
        cursor_check = conn.cursor(dictionary=True)
        cursor_check.execute("SELECT EquipmentID, ReturnDate FROM EquipmentLog WHERE LogID = %s", (log_id,))
        log_data = cursor_check.fetchone()
        if not log_data: return jsonify({"error": f"Log ID {log_id} not found"}), 404
        if log_data['ReturnDate'] is not None:
             return jsonify({"error": "This item has already been returned"}), 409
        equipment_id = log_data['EquipmentID'] # Get equipment ID for later update
        cursor_check.close()
        # --- End Check ---

        # --- Use Transaction ---
        # conn.start_transaction()
        cursor = conn.cursor()

        # Update the log entry
        sql_log = "UPDATE EquipmentLog SET ReturnDate = %s WHERE LogID = %s"
        cursor.execute(sql_log, (return_date, log_id))
        if cursor.rowcount == 0: # Should be caught above, safety check
             raise Exception("Log entry disappeared during transaction")

        # Update the Equipment table: Mark as available, optionally update condition
        update_fields = ["IsAvailable = TRUE"]
        update_values = []
        if condition_on_return:
             update_fields.append("Condition_ = %s")
             update_values.append(condition_on_return)
        update_values.append(equipment_id) # For WHERE clause

        sql_equip = f"UPDATE Equipment SET {', '.join(update_fields)} WHERE EquipmentID = %s"
        cursor.execute(sql_equip, tuple(update_values))
        # Check rowcount? Maybe not critical if equipment was just marked unavailable

        conn.commit()
        current_app.logger.info(f"User {current_user_id} logged return for LogID {log_id} (EquipID: {equipment_id})")
        return jsonify({"message": "Equipment returned", "LogID": log_id}), 200

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        current_app.logger.error(f"DB Error returning equipment log {log_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error returning equipment log {log_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 8. Get Equipment Log History (GET /equipment/logs/) - Admin, EqManager
@equipment_bp.route('/logs/', methods=['GET'])
@token_required
def get_equipment_logs(current_user_id, current_user_role):
    """Gets equipment borrow/return history. Requires Admin or EqManager."""
    current_app.logger.info(f"Request: Get Equipment Logs by User ID: {current_user_id}")
    allowed_roles = ['admin', 'EqManager']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    # Optional filters
    equipment_id_filter = request.args.get('equipment_id', type=int)
    member_id_filter = request.args.get('member_id', type=int) # IssuedTo ID
    only_issued = request.args.get('issued', type=bool) # Filter for items not yet returned

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Join log with equipment and member names
        sql = """
            SELECT el.LogID, el.EquipmentID, eq.EquipmentName, el.IssuedTo, m.UserName as IssuedToName,
                   el.IssueDate, el.ReturnDate
            FROM EquipmentLog el
            JOIN Equipment eq ON el.EquipmentID = eq.EquipmentID
            JOIN cs432cims.members m ON el.IssuedTo = m.ID
        """
        filters = []
        params = []
        if equipment_id_filter:
            filters.append("el.EquipmentID = %s")
            params.append(equipment_id_filter)
        if member_id_filter:
            filters.append("el.IssuedTo = %s")
            params.append(member_id_filter)
        if only_issued is True:
            filters.append("el.ReturnDate IS NULL")

        if filters:
            sql += " WHERE " + " AND ".join(filters)

        sql += " ORDER BY el.IssueDate DESC" # Show most recent first

        cursor.execute(sql, tuple(params))
        logs = cursor.fetchall()

        # Format dates for JSON
        for log in logs:
            log['IssueDate'] = log['IssueDate'].isoformat() if log.get('IssueDate') else None
            log['ReturnDate'] = log['ReturnDate'].isoformat() if log.get('ReturnDate') else None

        return jsonify(logs), 200

    except mysql.connector.Error as db_err:
         # Handle permissions error on JOIN
         if "SELECT command denied" in str(db_err):
              current_app.logger.error(f"DB Error listing logs - permission issue accessing cims.members?: {db_err}")
              return jsonify({"error": "Failed to retrieve full log details due to permissions."}), 500
         else:
             current_app.logger.error(f"DB Error listing equipment logs: {db_err}")
             return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Error listing equipment logs: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

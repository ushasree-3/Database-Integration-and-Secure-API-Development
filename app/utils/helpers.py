# app/utils/helpers.py
import mysql.connector
from flask import current_app # Need app context for config and logger
# Import the specific DB connection functions
from .database import get_cims_db_connection, get_project_db_connection

def check_member_exists(member_id):
    """Checks if a MemberID exists in the CIMS members table."""
    conn = None; cursor = None; exists = False
    try:
        conn = get_cims_db_connection()
        if not conn: return False
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM members WHERE ID = %s", (member_id,))
        exists = cursor.fetchone() is not None
    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Error checking CIMS member existence for ID {member_id}: {db_err}")
        exists = False
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return exists

def check_team_exists(team_id):
    """Checks if a TeamID exists in the project Team table."""
    conn = None; cursor = None; exists = False
    try:
        conn = get_project_db_connection()
        if not conn: return False
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Team WHERE TeamID = %s", (team_id,))
        exists = cursor.fetchone() is not None
    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Error checking project team existence for ID {team_id}: {db_err}")
        exists = False
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return exists

def check_event_exists(event_id):
    """Checks if an EventID exists in the project Event_ table."""
    conn = None; cursor = None; exists = False
    try:
        conn = get_project_db_connection()
        if not conn: return False
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Event_ WHERE EventID = %s", (event_id,))
        exists = cursor.fetchone() is not None
    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Error checking project event existence for ID {event_id}: {db_err}")
        exists = False
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return exists

def check_venue_exists(venue_id):
    """Checks if a VenueID exists in the project Venue table."""
    conn = None; cursor = None; exists = False
    try:
        conn = get_project_db_connection()
        if not conn: return False
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Venue WHERE VenueID = %s", (venue_id,))
        exists = cursor.fetchone() is not None
    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Error checking project venue existence for ID {venue_id}: {db_err}")
        exists = False
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return exists

def is_equipment_issuable(equipment_id):
    """
    Checks if the equipment is available and in good/fair condition.
    Returns (True, "") if issuable, else (False, error_message)
    """
    conn = None
    cursor = None
    try:
        conn = get_project_db_connection()
        if not conn:
            return False, "Database connection failed"
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT IsAvailable, Condition_ FROM Equipment WHERE EquipmentID = %s", (equipment_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Equipment not found"

        if not row["IsAvailable"]:
            return False, "Equipment is not available for issue"

        if row["Condition_"] == "Poor":
            return False, "Equipment is in poor condition and cannot be issued"

        return True, ""
    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Error checking equipment status for EquipmentID {equipment_id}: {db_err}")
        return False, "Database error occurred"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


def check_member_role(member_id, allowed_roles):
    """Checks if a MemberID has one of the allowed roles in CIMS Login."""
    # ... (Keep implementation from previous code if you created it) ...
    # Remember to import get_cims_db_connection if needed
    if not isinstance(allowed_roles, list): allowed_roles = [allowed_roles]
    conn = None; cursor = None; has_role = False
    try:
        conn = get_cims_db_connection()
        if not conn: return False
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT Role FROM Login WHERE MemberID = %s", (member_id,))
        login_data = cursor.fetchone()
        if login_data and login_data.get('Role') in allowed_roles:
            has_role = True
    except mysql.connector.Error as db_err:
         current_app.logger.error(f"Error checking CIMS role for MemberID {member_id}: {db_err}")
         has_role = False
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return has_role


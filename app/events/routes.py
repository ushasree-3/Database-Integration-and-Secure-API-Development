# app/events/routes.py
from flask import Blueprint, request, jsonify, current_app
import mysql.connector
import datetime # Needed for date comparisons

# Import helpers and decorators
from ..auth.decorators import token_required
# Need both DB connections: project for events/regs, cims for member checks
from ..utils.database import get_project_db_connection, get_cims_db_connection
from ..utils.helpers import check_member_exists, check_team_exists, check_event_exists,is_event_open

# Create the Blueprint instance for events
events_bp = Blueprint('events', __name__)

# ==============================================================================
# == EVENT CRUD Routes (/events/)
# ==============================================================================

# 1. Create Event (POST /events/) - Admin or Organizer
@events_bp.route('/', methods=['POST'])
@token_required
def create_event(current_user_id, current_user_role):
    """Creates a new event. Requires Admin or Organizer role."""
    current_app.logger.info(f"Request: Create Event by User ID: {current_user_id}, Role: {current_user_role}")

    # RBAC Check
    allowed_roles = ['admin', 'Organizer'] 
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    try:
        data = request.get_json()
        event_name = data.get('event_name')
        start_date_str = data.get('start_date') # Expect YYYY-MM-DD format
        end_date_str = data.get('end_date')     # Expect YYYY-MM-DD format
        location = data.get('location')
        organizer_id = data.get('organizer_id')
        description = data.get('description') # Optional

        if not all([event_name, start_date_str, end_date_str, location, organizer_id]):
            return jsonify({"error": "Missing fields: event_name, start_date, end_date, location, organizer_id"}), 400

        # Validate and convert dates
        try:
            start_date = datetime.date.fromisoformat(start_date_str)
            end_date = datetime.date.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Constraint Check: Start date must be before end date
        if start_date >= end_date:
            return jsonify({"error": "Event start date must be before the end date."}), 400

        organizer_id = int(organizer_id)

    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid JSON data or non-integer organizer_id"}), 400

    # --- Validation Checks ---
    if not check_member_exists(organizer_id):
        return jsonify({"error": f"Organizer MemberID {organizer_id} not found."}), 400
    # Optional: Check if organizer_id has 'Organizer' role in CIMS
    # from ..teams.routes import check_member_role # Can reuse if check_member_role exists
    # if not check_member_role(organizer_id, 'Organizer'): return jsonify({"error":"Assigned organizer doesn't have role"}), 400
    # --- End Validation ---

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        # Assumes Event_(EventID PK AI, EventName, EventStartDate, EventEndDate, Location, Description_, OrganizerID FK)
        sql = """
            INSERT INTO Event_ (EventName, EventStartDate, EventEndDate, Location, Description_, OrganizerID)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (event_name, start_date, end_date, location, description, organizer_id))
        new_event_id = cursor.lastrowid
        conn.commit()
        current_app.logger.info(f"User {current_user_id} created Event ID: {new_event_id}")
        return jsonify({"message": "Event created", "event_id": new_event_id}), 201

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        # Handle specific errors if needed (e.g., unique EventName?)
        current_app.logger.error(f"DB Error creating event: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error creating event: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 2. Get All Events (GET /events/) - Any Authenticated User
@events_bp.route('/', methods=['GET'])
@token_required
def get_all_events(current_user_id, current_user_role):
    """Retrieves a list of all events."""
    current_app.logger.info(f"Request: Get All Events by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        # Convert dates to ISO format strings for JSON compatibility
        sql = """
            SELECT EventID, EventName, DATE_FORMAT(EventStartDate, '%Y-%m-%d') as EventStartDate,
                   DATE_FORMAT(EventEndDate, '%Y-%m-%d') as EventEndDate, Location, Description_, OrganizerID
            FROM Event_
            ORDER BY EventStartDate DESC
        """
        cursor.execute(sql)
        events = cursor.fetchall()
        # Enhancement: Add Organizer names via CIMS lookup
        return jsonify(events), 200
    except Exception as e:
        current_app.logger.error(f"Error getting all events: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve events"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 3. Get Single Event (GET /events/<id>) - Any Authenticated User
@events_bp.route('/<int:event_id>', methods=['GET'])
@token_required
def get_event_by_id(current_user_id, current_user_role, event_id):
    """Retrieves details for a specific event."""
    current_app.logger.info(f"Request: Get Event ID: {event_id} by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT EventID, EventName, DATE_FORMAT(EventStartDate, '%Y-%m-%d') as EventStartDate,
                   DATE_FORMAT(EventEndDate, '%Y-%m-%d') as EventEndDate, Location, Description_, OrganizerID
            FROM Event_ WHERE EventID = %s
        """
        cursor.execute(sql, (event_id,))
        event = cursor.fetchone()
        if not event: return jsonify({"error": f"Event ID {event_id} not found"}), 404
        return jsonify(event), 200
    except Exception as e:
        current_app.logger.error(f"Error getting event {event_id}: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve event details"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 4. Update Event (PUT /events/<id>) - Admin OR Assigned Organizer
@events_bp.route('/<int:event_id>', methods=['PUT'])
@token_required
def update_event(current_user_id, current_user_role, event_id):
    """Updates an existing event. Requires Admin OR the assigned Organizer."""
    current_app.logger.info(f"Request: Update Event ID: {event_id} by User ID: {current_user_id}")

    try:
        data = request.get_json()
        event_name = data.get('event_name')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        location = data.get('location')
        organizer_id = data.get('organizer_id')
        description = data.get('description')

        # Basic validation - ensure at least something is being updated
        if not any([event_name, start_date_str, end_date_str, location, organizer_id is not None, description is not None]):
             return jsonify({"error": "No update fields provided"}), 400

        # Validate dates if provided
        start_date = None; end_date = None
        if start_date_str: start_date = datetime.date.fromisoformat(start_date_str)
        if end_date_str: end_date = datetime.date.fromisoformat(end_date_str)

        # Validate date order if both provided
        temp_start = start_date if start_date else None # Need original start date if only end is updated
        temp_end = end_date if end_date else None       # Need original end date if only start is updated
        # If one is provided, we need the other from DB to validate order (more complex)
        # Simple check if BOTH are provided in the request:
        if start_date and end_date and start_date >= end_date:
             return jsonify({"error": "Event start date must be before end date."}), 400

        if organizer_id is not None:
            organizer_id = int(organizer_id)
            if not check_member_exists(organizer_id):
                return jsonify({"error": f"Organizer MemberID {organizer_id} not found."}), 400
            # Optional: Check role for organizer_id
    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid JSON data or data types"}), 400

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # --- Authorization Check: Admin or Assigned Organizer ---
        is_authorized = False
        if current_user_role == 'admin':
            is_authorized = True
        else:
            cursor.execute("SELECT OrganizerID FROM Event_ WHERE EventID = %s", (event_id,))
            event_data = cursor.fetchone()
            if not event_data: return jsonify({"error": f"Event ID {event_id} not found"}), 404
            if current_user_role == 'Organizer' and int(current_user_id) == event_data['OrganizerID']:
                is_authorized = True

        if not is_authorized:
            return jsonify({"error": "Admin or assigned Organizer privileges required"}), 403
        # --- End Authorization Check ---

        # Build UPDATE statement dynamically based on provided fields (more robust)
        update_fields = []
        update_values = []
        if event_name is not None:
            update_fields.append("EventName = %s")
            update_values.append(event_name)
        if start_date is not None:
            update_fields.append("EventStartDate = %s")
            update_values.append(start_date)
        if end_date is not None:
            update_fields.append("EventEndDate = %s")
            update_values.append(end_date)
        if location is not None:
            update_fields.append("Location = %s")
            update_values.append(location)
        if description is not None: # Allow setting description to empty string
            update_fields.append("Description_ = %s")
            update_values.append(description)
        if organizer_id is not None:
            update_fields.append("OrganizerID = %s")
            update_values.append(organizer_id)

        if not update_fields: # Should be caught earlier, but safety check
            return jsonify({"error": "No valid fields provided for update"}), 400

        sql_update = f"UPDATE Event_ SET {', '.join(update_fields)} WHERE EventID = %s"
        update_values.append(event_id) # Add event_id for WHERE clause

        cursor_update = conn.cursor()
        cursor_update.execute(sql_update, tuple(update_values))

        if cursor_update.rowcount == 0:
             return jsonify({"error": f"Event ID {event_id} not found during update"}), 404 # Should be caught earlier

        conn.commit()
        current_app.logger.info(f"User {current_user_id} updated Event ID: {event_id}")
        return jsonify({"message": "Event updated successfully", "event_id": event_id}), 200

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        current_app.logger.error(f"DB Error updating event {event_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error updating event {event_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if 'cursor_update' in locals() and cursor_update: cursor_update.close()
        if conn and conn.is_connected(): conn.close()


# 5. Delete Event (DELETE /events/<id>) - Admin OR Assigned Organizer
@events_bp.route('/<int:event_id>', methods=['DELETE'])
@token_required
def delete_event(current_user_id, current_user_role, event_id):
    """Deletes an event. Requires Admin OR the assigned Organizer."""
    current_app.logger.info(f"Request: Delete Event ID: {event_id} by User ID: {current_user_id}")

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # --- Authorization Check: Admin or Assigned Organizer ---
        is_authorized = False
        if current_user_role == 'admin':
            is_authorized = True
        else:
            cursor.execute("SELECT OrganizerID FROM Event_ WHERE EventID = %s", (event_id,))
            event_data = cursor.fetchone()
            if not event_data: return jsonify({"error": f"Event ID {event_id} not found"}), 404
            if current_user_role == 'Organizer' and int(current_user_id) == event_data['OrganizerID']:
                is_authorized = True

        if not is_authorized:
            return jsonify({"error": "Admin or assigned Organizer privileges required"}), 403
        # --- End Authorization Check ---

        cursor_delete = conn.cursor()
        # Assumes table Event_
        sql_delete = "DELETE FROM Event_ WHERE EventID = %s"
        cursor_delete.execute(sql_delete, (event_id,))

        if cursor_delete.rowcount == 0:
            return jsonify({"error": f"Event ID {event_id} not found during delete"}), 404

        conn.commit()
        current_app.logger.info(f"User {current_user_id} deleted Event ID: {event_id}")
        return jsonify({"message": f"Event ID {event_id} deleted"}), 200

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        if db_err.errno == 1451: # FK constraint (e.g., Matches, Registrations depend on it)
             current_app.logger.warning(f"FK Constraint fail delete event {event_id}: {db_err}")
             return jsonify({"error": "Cannot delete event, related records exist (matches, registrations)."}), 409
        current_app.logger.error(f"DB Error deleting event {event_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error deleting event {event_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if 'cursor_delete' in locals() and cursor_delete: cursor_delete.close()
        if conn and conn.is_connected(): conn.close()


# ==============================================================================
# == EVENT REGISTRATION Routes (/events/<id>/registrations)
# ==============================================================================

# 6. Register Team for Event (POST /events/<event_id>/registrations) - Admin, Coach, Player?
@events_bp.route('/<int:event_id>/registrations', methods=['POST'])
@token_required
def register_team_for_event(current_user_id, current_user_role, event_id):
    """Registers a team for an event. Requires Admin, Coach role."""
    current_app.logger.info(f"Request: Register team for Event ID: {event_id} by User ID: {current_user_id}")

    # RBAC Check - Allow multiple roles, adjust as needed
    allowed_roles = ['admin', 'Coach']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    try:
        data = request.get_json()
        team_id = data.get('team_id')
        if not team_id:
            return jsonify({"error": "Missing required field: team_id"}), 400
        team_id = int(team_id)
    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid JSON data or non-integer team_id"}), 400

    # --- Validation Checks ---
    if not check_event_exists(event_id): return jsonify({"error": f"Event ID {event_id} not found."}), 404
    if not check_team_exists(team_id): return jsonify({"error": f"Team ID {team_id} not found."}), 404
    
    # --- Check if event start date is in the future ---
    is_open, error_message = is_event_open(event_id)
    if not is_open:
        return jsonify({"error": error_message}), 400
    # --- End Validation ---

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        # Assumes EventRegistration(RegistrationID PK AI, EventID FK, TeamID FK, UNIQUE(EventID, TeamID))
        sql = "INSERT INTO EventRegistration (EventID, TeamID) VALUES (%s, %s)"
        cursor.execute(sql, (event_id, team_id))
        new_reg_id = cursor.lastrowid
        conn.commit()
        current_app.logger.info(f"User {current_user_id} registered Team {team_id} for Event {event_id}")
        return jsonify({"message": "Team registered successfully", "registration_id": new_reg_id}), 201

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        if db_err.errno == 1062: # Duplicate registration
            return jsonify({"error": "This team is already registered for this event"}), 409
        if db_err.errno == 1452: # EventID or TeamID FK violation
             return jsonify({"error": "Invalid EventID or TeamID provided."}), 400 # Or use 404 if checks failed
        current_app.logger.error(f"DB Error registering team {team_id} for event {event_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error registering team {team_id} for event {event_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 7. Unregister Team from Event (DELETE /events/<event_id>/registrations/<team_id>) - Admin, Coach
@events_bp.route('/<int:event_id>/registrations/<int:team_id>', methods=['DELETE'])
@token_required
def unregister_team_from_event(current_user_id, current_user_role, event_id, team_id):
    """Unregisters a team from an event. Requires Admin, Coach, or Player role."""
    current_app.logger.info(f"Request: Unregister Team {team_id} from Event {event_id} by User {current_user_id}")

    allowed_roles = ['admin', 'Coach']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403
    # Optional: Check if user belongs to the team being unregistered

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        # Assumes EventRegistration table
        sql = "DELETE FROM EventRegistration WHERE EventID = %s AND TeamID = %s"
        cursor.execute(sql, (event_id, team_id))

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Unregister failed: Team {team_id} was not registered for Event {event_id}.")
            return jsonify({"error": "Registration not found"}), 404

        conn.commit()
        current_app.logger.info(f"User {current_user_id} unregistered Team {team_id} from Event {event_id}")
        return jsonify({"message": "Team unregistered successfully"}), 200

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        # Handle FK constraint errors if other tables depend on RegistrationID? Unlikely.
        current_app.logger.error(f"DB Error unregistering team {team_id} from event {event_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error unregistering team {team_id} from event {event_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 8. List Registered Teams for Event (GET /events/<event_id>/registrations) - Any Auth User
@events_bp.route('/<int:event_id>/registrations', methods=['GET'])
@token_required
def list_registered_teams(current_user_id, current_user_role, event_id):
    """Lists all teams registered for a specific event."""
    current_app.logger.info(f"Request: List registrations for Event {event_id} by User {current_user_id}")

    # Check if event exists first for better 404 message
    if not check_event_exists(event_id):
        return jsonify({"error": f"Event with ID {event_id} not found"}), 404

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Join EventRegistration with Team to get team names
        sql = """
            SELECT er.RegistrationID, er.TeamID, t.TeamName, t.CaptainID, t.CoachID
            FROM EventRegistration er
            JOIN Team t ON er.TeamID = t.TeamID
            WHERE er.EventID = %s
            ORDER BY t.TeamName
        """
        cursor.execute(sql, (event_id,))
        registrations = cursor.fetchall()

        return jsonify(registrations), 200
    except Exception as e:
        current_app.logger.error(f"Error listing registrations for event {event_id}: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve registrations"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

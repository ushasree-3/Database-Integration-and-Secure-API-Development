# app/teams/routes.py
from flask import Blueprint, request, jsonify, current_app
import mysql.connector
import hashlib
import logging

# Import helpers and decorators
from ..auth.decorators import token_required
from ..utils.database import get_project_db_connection, get_cims_db_connection
from ..utils.helpers import check_member_exists, check_team_exists, is_event_valid

# Create the Blueprint instance for teams
teams_bp = Blueprint('teams', __name__)

# ==============================================================================
# == TEAM CRUD Routes (/teams/)
# ==============================================================================

# 1. Create Team (POST /teams/) - Admin, Coach
@teams_bp.route('/', methods=['POST'])
@token_required
def create_team(current_user_id, current_user_role):
    """Creates a new team. Requires Admin, Coach role."""
    current_app.logger.info(f"Request: Create Team by User ID: {current_user_id}, Role: {current_user_role}")

    allowed_roles = ['admin', 'Coach']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    try:
        data = request.get_json()
        team_name = data.get('team_name')
        captain_id = data.get('captain_id')
        coach_id = data.get('coach_id')
        if not all([team_name, captain_id, coach_id]):
            return jsonify({"error": "Missing fields: team_name, captain_id, coach_id"}), 400
        captain_id = int(captain_id)
        coach_id = int(coach_id)
    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid JSON data or non-integer ID"}), 400

    if not check_member_exists(captain_id): return jsonify({"error": f"Captain MemberID {captain_id} not found."}), 400
    if not check_member_exists(coach_id): return jsonify({"error": f"Coach MemberID {coach_id} not found."}), 400

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        # Schema: Team(TeamID PK AI, TeamName UQ, CaptainID UQ FK(ref members), CoachID UQ FK(ref members))
        sql = "INSERT INTO Team (TeamName, CaptainID, CoachID) VALUES (%s, %s, %s)"
        cursor.execute(sql, (team_name, captain_id, coach_id))
        new_team_id = cursor.lastrowid
        conn.commit()
        current_app.logger.info(f"User {current_user_id} created Team ID: {new_team_id} CoachID {coach_id} CaptainID {captain_id}")
        return jsonify({"message": "Team created", "TeamID": new_team_id, "CoachID": coach_id, "CaptainID": captain_id}), 201 
    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        if db_err.errno == 1062: # Handle UNIQUE constraints
             # Check the specific key name from the detailed error message if needed
             if 'TeamName' in db_err.msg: return jsonify({"error": "Team name already exists"}), 409
             if 'CaptainID' in db_err.msg: return jsonify({"error": "This member is already a captain"}), 409
             if 'CoachID' in db_err.msg: return jsonify({"error": "This member is already a coach"}), 409
        current_app.logger.error(f"DB Error creating team: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error creating team: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 2. Get All Teams (GET /teams/) - Any Authenticated User
@teams_bp.route('/', methods=['GET'])
@token_required
def get_all_teams(current_user_id, current_user_role):
    """Retrieves a list of all teams."""
    current_app.logger.info(f"Request: Get All Teams by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT TeamID, TeamName, CaptainID, CoachID FROM Team ORDER BY TeamName")
        teams = cursor.fetchall()
        return jsonify(teams), 200
    except Exception as e:
        current_app.logger.error(f"Error getting all teams: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve teams"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 3. Get Single Team (GET /teams/<id>) - Any Authenticated User
@teams_bp.route('/<int:team_id>', methods=['GET'])
@token_required
def get_team_by_id(current_user_id, current_user_role, team_id):
    """Retrieves details for a specific team."""
    current_app.logger.info(f"Request: Get Team ID: {team_id} by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT TeamID, TeamName, CaptainID, CoachID FROM Team WHERE TeamID = %s", (team_id,))
        team = cursor.fetchone()
        if not team: return jsonify({"error": f"Team ID {team_id} not found"}), 404
        return jsonify(team), 200
    except Exception as e:
        current_app.logger.error(f"Error getting team {team_id}: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve team details"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 4. Update Team (PUT /teams/<id>) - Admin OR Assigned Coach
@teams_bp.route('/<int:team_id>', methods=['PUT'])
@token_required
def update_team(current_user_id, current_user_role, team_id):
    """Updates an existing team. Requires Admin OR the assigned Coach."""
    current_app.logger.info(f"Request: Update Team ID: {team_id} by User ID: {current_user_id}")

    try:
        data = request.get_json()
        team_name = data.get('team_name')
        captain_id = data.get('captain_id')
        coach_id = data.get('coach_id')
        if not all([team_name, captain_id, coach_id]):
            return jsonify({"error": "Missing fields: team_name, captain_id, coach_id"}), 400
        captain_id = int(captain_id)
        coach_id = int(coach_id)
    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid JSON data or non-integer ID"}), 400

    if not check_member_exists(captain_id): return jsonify({"error": f"Captain MemberID {captain_id} not found."}), 400
    if not check_member_exists(coach_id): return jsonify({"error": f"Coach MemberID {coach_id} not found."}), 400

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # --- Authorization Check: Admin or Assigned Coach ---
        is_authorized = False
        if current_user_role == 'admin':
            is_authorized = True
        else:
            cursor.execute("SELECT CoachID FROM Team WHERE TeamID = %s", (team_id,))
            team_data = cursor.fetchone()
            if not team_data: return jsonify({"error": f"Team ID {team_id} not found"}), 404
            if current_user_role == 'Coach' and int(current_user_id) == team_data['CoachID']:
                is_authorized = True

        if not is_authorized:
            return jsonify({"error": "Admin or assigned Coach privileges required"}), 403
        # --- End Authorization Check ---

        cursor_update = conn.cursor()
        sql_update = "UPDATE Team SET TeamName = %s, CaptainID = %s, CoachID = %s WHERE TeamID = %s"
        cursor_update.execute(sql_update, (team_name, captain_id, coach_id, team_id))

        if cursor_update.rowcount == 0:
             return jsonify({"error": f"Team ID {team_id} not found during update"}), 404

        conn.commit()
        current_app.logger.info(f"User {current_user_id} updated Team ID: {team_id}")
        return jsonify({"message": "Team updated", "TeamID": team_id}), 200 # Return TeamID

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        if db_err.errno == 1062: # Handle UNIQUE constraints
             if 'TeamName' in db_err.msg: return jsonify({"error": "Team name already exists"}), 409
             if 'CaptainID' in db_err.msg: return jsonify({"error": "Member already captain"}), 409
             if 'CoachID' in db_err.msg: return jsonify({"error": "Member already coach"}), 409
        current_app.logger.error(f"DB Error updating team {team_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error updating team {team_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if 'cursor_update' in locals() and cursor_update: cursor_update.close()
        if conn and conn.is_connected(): conn.close()


# 5. Delete Team (DELETE /teams/<id>) - Admin OR Assigned Coach
@teams_bp.route('/<int:team_id>', methods=['DELETE'])
@token_required
def delete_team(current_user_id, current_user_role, team_id):
    """Deletes a team. Requires Admin OR the assigned Coach."""
    # ... (Authorization logic remains the same) ...
    current_app.logger.info(f"Request: Delete Team ID: {team_id} by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        is_authorized = False
        if current_user_role == 'admin': is_authorized = True
        else:
            cursor.execute("SELECT CoachID FROM Team WHERE TeamID = %s", (team_id,))
            team_data = cursor.fetchone();
            if not team_data: return jsonify({"error": f"Team ID {team_id} not found"}), 404
            if current_user_role == 'Coach' and int(current_user_id) == team_data['CoachID']: is_authorized = True
        if not is_authorized: return jsonify({"error": "Admin or assigned Coach privileges required"}), 403

        cursor_delete = conn.cursor()
        sql_delete = "DELETE FROM Team WHERE TeamID = %s"
        cursor_delete.execute(sql_delete, (team_id,))
        if cursor_delete.rowcount == 0: return jsonify({"error": f"Team ID {team_id} not found during delete"}), 404
        conn.commit()
        current_app.logger.info(f"User {current_user_id} deleted Team ID: {team_id}")
        return jsonify({"message": f"Team ID {team_id} deleted"}), 200
    except mysql.connector.Error as db_err:
        # ... (Keep FK error handling 1451) ...
        if conn: conn.rollback()
        if db_err.errno == 1451:
             current_app.logger.warning(f"FK Constraint fail delete team {team_id}: {db_err}")
             return jsonify({"error": "Cannot delete team, related records exist (players, etc)."}), 409
        current_app.logger.error(f"DB Error deleting team {team_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        # ... (Keep general error handling) ...
        if conn: conn.rollback()
        current_app.logger.error(f"Error deleting team {team_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if 'cursor_delete' in locals() and cursor_delete: cursor_delete.close()
        if conn and conn.is_connected(): conn.close()

# ==============================================================================
# == Player Management Routes (Now Event Specific)
# ==============================================================================
# These routes now need Event context because a player is tied to a team *for an event*

# 6. Add Player to Team FOR A SPECIFIC EVENT (POST /events/<event_id>/teams/<team_id>/players) - NEW ROUTE STRUCTURE
@teams_bp.route('/<int:team_id>/events/<int:event_id>/players', methods=['POST'])
@token_required
def add_player_to_team_for_event(current_user_id, current_user_role, team_id, event_id):
    """Adds a player (MemberID) to a specific team FOR a specific event.
       Requires Admin OR the assigned Coach of the team."""
    current_app.logger.info(f"Request: Add player to Team ID: {team_id} for Event ID {event_id} by User ID: {current_user_id}")

    # --- Initial Validation ---
    if not check_team_exists(team_id): return jsonify({"error": f"Team ID {team_id} not found"}), 404
    is_valid, error_message = is_event_valid(event_id)
    if not is_valid:
        return jsonify({"error": error_message}), 400


    conn = None; cursor = None
    try:
        data = request.get_json()
        member_id = data.get('member_id')
        position = data.get('position') # Position is optional
        if not member_id: return jsonify({"error": "Missing required field: member_id"}), 400
        member_id = int(member_id)
    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid JSON data or non-integer member_id"}), 400

    if not check_member_exists(member_id): return jsonify({"error": f"Player MemberID {member_id} not found."}), 400
    # Optional: Check CIMS role compatibility

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # --- Authorization Check: Admin or Assigned Coach ---
        is_authorized = False
        if current_user_role == 'admin':
            is_authorized = True
        else:
            cursor.execute("SELECT CoachID FROM Team WHERE TeamID = %s", (team_id,))
            team_data = cursor.fetchone()
            # Team existence already checked, but double-check fetchone result
            if not team_data: return jsonify({"error": f"Team ID {team_id} check failed unexpectedly"}), 500
            if current_user_role == 'Coach' and int(current_user_id) == team_data['CoachID']:
                is_authorized = True

        if not is_authorized:
            return jsonify({"error": "Admin or assigned Coach privileges required"}), 403
        # --- End Authorization Check ---

        # --- Constraint Check: Team Size Limit FOR THIS EVENT ---
        # Note: Team size might be event-specific or general. Assuming general for now.
        max_players = current_app.config.get('TEAM_MAX_PLAYERS', 12)
        cursor.execute("SELECT COUNT(*) as playerCount FROM Player WHERE TeamID = %s AND EventID = %s", (team_id, event_id))
        count_result = cursor.fetchone()
        if count_result and count_result['playerCount'] >= max_players:
            return jsonify({"error": f"Team {team_id} cannot exceed {max_players} players for Event {event_id}"}), 409
        # --- End Constraint Check ---

        cursor_insert = conn.cursor()
        # Assumes Player(PlayerID PK AI, MemberID, TeamID FK, EventID FK, Position_, UQ(MemberID, EventID))
        sql_add = "INSERT INTO Player (MemberID, TeamID, EventID, Position_) VALUES (%s, %s, %s, %s)"
        cursor_insert.execute(sql_add, (member_id, team_id, event_id, position))
        new_player_id = cursor_insert.lastrowid
        conn.commit()

        current_app.logger.info(f"User {current_user_id} added MemberID {member_id} to TeamID {team_id} for Event {event_id}")
        return jsonify({"message": "Player added to team for event", "PlayerID": new_player_id}), 201

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        if db_err.errno == 1062: # Duplicate MemberID for this event (UNIQUE constraint)
             return jsonify({"error": "This member is already registered as a player for this event (possibly on another team)."}), 409
        # Note: FK error on team_id/event_id should be caught by earlier checks
        current_app.logger.error(f"DB Error adding player to team {team_id}/event {event_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error adding player to team {team_id}/event {event_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if 'cursor_insert' in locals() and cursor_insert: cursor_insert.close()
        if conn and conn.is_connected(): conn.close()

# 7. List Players in Team FOR A SPECIFIC EVENT (GET /teams/<team_id>/events/<event_id>/players) - NEW ROUTE STRUCTURE
@teams_bp.route('/<int:team_id>/events/<int:event_id>/players', methods=['GET'])
@token_required
def list_players_in_team_for_event(current_user_id, current_user_role, team_id, event_id):
    """Lists all players associated with a specific team FOR a specific event."""
    current_app.logger.info(f"Request: List players for Team ID: {team_id}, Event ID: {event_id} by User ID: {current_user_id}")

    # Check existence for better error messages
    if not check_team_exists(team_id): return jsonify({"error": f"Team {team_id} not found"}), 404
    is_valid, error_message = is_event_valid(event_id)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Assumes Player table columns: PlayerID, MemberID, Position_
        # Assumes cims.members columns: ID, UserName, emailID
        # Verify SELECT permission for cs432g2 user on cs432cims.members
        sql = """
            SELECT p.PlayerID, p.MemberID, p.Position_, m.UserName, m.emailID
            FROM Player p
            JOIN cs432cims.members m ON p.MemberID = m.ID
            WHERE p.TeamID = %s AND p.EventID = %s
        """
        # Fallback if JOIN fails/not allowed:
        # sql = "SELECT PlayerID, MemberID, Position_ FROM Player WHERE TeamID = %s AND EventID = %s"

        cursor.execute(sql, (team_id, event_id))
        players = cursor.fetchall()

        return jsonify(players), 200
    except mysql.connector.Error as db_err:
         # Handle permission error for JOIN
         if "SELECT command denied" in str(db_err):
              # ... (Add fallback logic as in previous code) ...
              current_app.logger.error(f"DB permission error listing players: {db_err}")
              return jsonify({"error": "Failed to retrieve full player details due to permissions."}), 500
         else:
             current_app.logger.error(f"DB Error listing players for team {team_id}/event {event_id}: {db_err}")
             return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Error listing players {team_id}/event {event_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 8. Remove Player from Team FOR A SPECIFIC EVENT (DELETE /teams/<team_id>/events/<event_id>/players/<member_id>) - NEW ROUTE STRUCTURE
@teams_bp.route('/<int:team_id>/events/<int:event_id>/players/<int:member_id>', methods=['DELETE'])
@token_required
def remove_player_from_team_for_event(current_user_id, current_user_role, team_id, event_id, member_id):
    """Removes a player (MemberID) from a team FOR a specific event. Requires Admin OR the assigned Coach."""
    current_app.logger.info(f"Request: Remove MemberID {member_id} from Team ID: {team_id} for Event {event_id} by User ID: {current_user_id}")

    # --- Initial validation ---
    # Don't strictly need to check team/event existence if FKs handle it, but good for clarity
    # if not check_team_exists(team_id): return jsonify({"error": f"Team ID {team_id} not found"}), 404
    # is_valid, error_message = is_event_valid(event_id)
    # if not is_valid:
    #     return jsonify({"error": error_message}), 400


    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # --- Authorization Check: Admin or Assigned Coach ---
        is_authorized = False
        if current_user_role == 'admin':
            is_authorized = True
        else:
            # Need to fetch team data to check coach only if user is not admin
            cursor.execute("SELECT CoachID FROM Team WHERE TeamID = %s", (team_id,))
            team_data = cursor.fetchone()
            if not team_data: return jsonify({"error": f"Team ID {team_id} not found"}), 404
            if current_user_role == 'Coach' and int(current_user_id) == team_data['CoachID']:
                is_authorized = True

        if not is_authorized:
            return jsonify({"error": "Admin or assigned Coach privileges required"}), 403
        # --- End Authorization Check ---

        cursor_delete = conn.cursor()
        # Delete based on MemberID, TeamID, AND EventID
        sql_remove = "DELETE FROM Player WHERE MemberID = %s AND TeamID = %s AND EventID = %s"
        cursor_delete.execute(sql_remove, (member_id, team_id, event_id))

        if cursor_delete.rowcount == 0:
            current_app.logger.warning(f"Remove failed: Player {member_id} not found on Team {team_id} for Event {event_id}.")
            return jsonify({"error": f"Player MemberID {member_id} not found on Team ID {team_id} for Event ID {event_id}"}), 404

        conn.commit()
        current_app.logger.info(f"User {current_user_id} removed MemberID {member_id} from TeamID {team_id} for Event {event_id}")
        return jsonify({"message": "Player removed from team for this event"}), 200

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        current_app.logger.error(f"DB Error removing player {member_id} from team {team_id}/event {event_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error removing player {member_id} from team {team_id}/event {event_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if 'cursor_delete' in locals() and cursor_delete: cursor_delete.close()
        if conn and conn.is_connected(): conn.close()
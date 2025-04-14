# app/teams/routes.py
from flask import Blueprint, request, jsonify, current_app
import mysql.connector
import logging # Import logging if not already implicitly available via current_app

# Import helpers and decorators from other modules
# Assuming these files exist and are correctly structured:
from ..auth.decorators import token_required
from ..utils.database import get_project_db_connection, get_cims_db_connection # Need both potentially

# Create the Blueprint instance for teams
teams_bp = Blueprint('teams', __name__)

# --- Helper Function to Check if Member Exists in CIMS ---
# (Good practice to avoid FK errors proactively)
def check_member_exists(member_id):
    """Checks if a MemberID exists in the CIMS members table."""
    conn = None
    cursor = None
    exists = False
    try:
        conn = get_cims_db_connection() # Connect to CENTRAL DB
        if not conn: return False # Return False on connection error
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM members WHERE ID = %s", (member_id,))
        exists = cursor.fetchone() is not None # True if a row is found
    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Error checking CIMS member existence for ID {member_id}: {db_err}")
        exists = False # Assume false on error
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return exists

# --- Task 5: Team CRUD Operations ---

# 1. Create Team (POST /teams/)
@teams_bp.route('/', methods=['POST'])
@token_required
def create_team(current_user_id, current_user_role):
    """Creates a new team. Requires Admin role."""
    current_app.logger.info(f"Request: Create Team by User ID: {current_user_id}, Role: {current_user_role}")

    # RBAC Check: Only Admins can create teams
    if current_user_role not in ['admin', 'Coach']:
        current_app.logger.warning(f"User {current_user_id} (Role: {current_user_role}) unauthorized to create team.")
        return jsonify({"error": "Admin privileges required to create teams"}), 403

    try:
        data = request.get_json()
        if not data or not data.get('team_name') or not data.get('captain_id') or not data.get('coach_id'):
            return jsonify({"error": "Missing required fields: team_name, captain_id, coach_id"}), 400
        team_name = data['team_name']
        captain_id = int(data['captain_id']) # Ensure integer
        coach_id = int(data['coach_id'])     # Ensure integer
    except (ValueError, TypeError, Exception) as e:
        current_app.logger.error(f"Error parsing create team request JSON or casting IDs: {e}")
        return jsonify({"error": "Invalid JSON data or non-integer ID provided"}), 400

    # --- Optional: Validate Captain/Coach exist in CIMS members ---
    if not check_member_exists(captain_id):
        return jsonify({"error": f"Captain with MemberID {captain_id} does not exist in CIMS."}), 400
    if not check_member_exists(coach_id):
        return jsonify({"error": f"Coach with MemberID {coach_id} does not exist in CIMS."}), 400
    # --- End Validation ---

    conn = None
    cursor = None
    try:
        conn = get_project_db_connection() # Connect to YOUR project DB
        if not conn: return jsonify({"error": "Project database connection failed"}), 500
        cursor = conn.cursor()

        # Assumes table `Team` with columns `TeamName`, `CaptainID`, `CoachID`
        sql_insert_team = "INSERT INTO Team (TeamName, CaptainID, CoachID) VALUES (%s, %s, %s)"
        cursor.execute(sql_insert_team, (team_name, captain_id, coach_id))
        new_team_id = cursor.lastrowid
        conn.commit()

        current_app.logger.info(f"Admin {current_user_id} created Team ID: {new_team_id} Name: '{team_name}'")
        return jsonify({ "message": "Team created successfully", "TeamID": new_team_id, "TeamName": team_name, "CaptainID":captain_id , "CoachID": coach_id }), 201

    except mysql.connector.Error as db_err:
        current_app.logger.error(f"Database Error creating team: {db_err}")
        if conn: conn.rollback()
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error creating team: {e}", exc_info=True)
        if conn: conn.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 2. Get All Teams (GET /teams/)
@teams_bp.route('/', methods=['GET'])
@token_required
def get_all_teams(current_user_id, current_user_role):
    """Retrieves a list of all teams. Accessible by any authenticated user."""
    current_app.logger.info(f"Request: Get All Teams by User ID: {current_user_id}, Role: {current_user_role}")
    # No specific RBAC needed beyond authentication

    conn = None
    cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "Project database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Assumes table `Team` with columns `TeamID`, `TeamName`, `CaptainID`, `CoachID`
        cursor.execute("SELECT TeamID, TeamName, CaptainID, CoachID FROM Team ORDER BY TeamName")
        teams = cursor.fetchall()

        current_app.logger.info(f"Retrieved {len(teams)} teams.")
        return jsonify(teams), 200

    except mysql.connector.Error as db_err:
        # ... (standard error handling) ...
        current_app.logger.error(f"Database Error getting all teams: {db_err}")
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error getting all teams: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 3. Get Single Team (GET /teams/<id>)
@teams_bp.route('/<int:team_id>', methods=['GET'])
@token_required
def get_team_by_id(current_user_id, current_user_role, team_id):
    """Retrieves details for a specific team by ID. Accessible by any authenticated user."""
    current_app.logger.info(f"Request: Get Team ID: {team_id} by User ID: {current_user_id}")
    # No specific RBAC needed beyond authentication

    conn = None
    cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "Project database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Assumes table `Team` with relevant columns
        cursor.execute("SELECT TeamID, TeamName, CaptainID, CoachID FROM Team WHERE TeamID = %s", (team_id,))
        team = cursor.fetchone()

        if team:
            current_app.logger.info(f"Retrieved Team ID: {team_id}")
            return jsonify(team), 200
        else:
            current_app.logger.warning(f"Team ID: {team_id} not found.")
            return jsonify({"error": f"Team with ID {team_id} not found"}), 404

    except mysql.connector.Error as db_err:
        # ... (standard error handling) ...
        current_app.logger.error(f"Database Error getting team {team_id}: {db_err}")
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error getting team {team_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 4. Update Team (PUT /teams/<id>)
@teams_bp.route('/<int:team_id>', methods=['PUT'])
@token_required
def update_team(current_user_id, current_user_role, team_id):
    """Updates an existing team. Requires Admin role (or specific Coach - TBD)."""
    current_app.logger.info(f"Request: Update Team ID: {team_id} by User ID: {current_user_id}, Role: {current_user_role}")

    # RBAC Check: Start with Admin only, can be refined
    if current_user_role not in ['admin', 'Coach']:
        current_app.logger.warning(f"User {current_user_id} (Role: {current_user_role}) unauthorized to update team {team_id}.")
        return jsonify({"error": "Admin privileges required to update teams"}), 403

    try:
        data = request.get_json()
        if not data or not data.get('team_name') or not data.get('captain_id') or not data.get('coach_id'):
            return jsonify({"error": "Missing required fields: team_name, captain_id, coach_id"}), 400
        team_name = data['team_name']
        captain_id = int(data['captain_id'])
        coach_id = int(data['coach_id'])
    except (ValueError, TypeError, Exception) as e:
        current_app.logger.error(f"Error parsing update team request JSON or casting IDs: {e}")
        return jsonify({"error": "Invalid JSON data or non-integer ID provided"}), 400

    # --- Optional: Validate Captain/Coach exist ---
    if not check_member_exists(captain_id):
        return jsonify({"error": f"Captain with MemberID {captain_id} does not exist in CIMS."}), 400
    if not check_member_exists(coach_id):
        return jsonify({"error": f"Coach with MemberID {coach_id} does not exist in CIMS."}), 400
    # --- End Validation ---

    conn = None
    cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "Project database connection failed"}), 500
        cursor = conn.cursor()

        sql_update_team = """
            UPDATE Team SET TeamName = %s, CaptainID = %s, CoachID = %s WHERE TeamID = %s
        """
        cursor.execute(sql_update_team, (team_name, captain_id, coach_id, team_id))

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Update failed: Team ID: {team_id} not found.")
            return jsonify({"error": f"Team with ID {team_id} not found, update failed."}), 404

        conn.commit()
        current_app.logger.info(f"Admin {current_user_id} updated Team ID: {team_id}")
        return jsonify({"message": "Team updated successfully", "team_id": team_id }), 200

    except mysql.connector.Error as db_err:
        # ... (standard error handling, could check FK 1452 again) ...
        current_app.logger.error(f"Database Error updating team {team_id}: {db_err}")
        if conn: conn.rollback()
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error updating team {team_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 5. Delete Team (DELETE /teams/<id>)
@teams_bp.route('/<int:team_id>', methods=['DELETE'])
@token_required
def delete_team(current_user_id, current_user_role, team_id):
    """Deletes a team. Requires Admin role."""
    current_app.logger.info(f"Request: Delete Team ID: {team_id} by User ID: {current_user_id}")

    # RBAC Check
    if current_user_role not in ['admin', 'Coach']:
        current_app.logger.warning(f"User {current_user_id} (Role: {current_user_role}) unauthorized to delete team {team_id}.")
        return jsonify({"error": "Admin privileges required to delete teams"}), 403

    conn = None
    cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "Project database connection failed"}), 500
        cursor = conn.cursor()

        # Assumes table `Team`
        sql_delete_team = "DELETE FROM Team WHERE TeamID = %s"
        cursor.execute(sql_delete_team, (team_id,))

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Delete failed: Team ID: {team_id} not found.")
            return jsonify({"error": f"Team with ID {team_id} not found, delete failed."}), 404

        conn.commit()
        current_app.logger.info(f"Admin {current_user_id} deleted Team ID: {team_id}")
        return jsonify({"message": f"Team ID {team_id} deleted successfully"}), 200

    except mysql.connector.Error as db_err:
        # Handle foreign key constraints (e.g., if Players, Matches, EventRegistrations still reference this Team)
        if db_err.errno == 1451: # FK constraint fails on DELETE
             current_app.logger.warning(f"FK Constraint failed deleting team {team_id} (dependent records exist): {db_err}")
             return jsonify({
                 "error": "Cannot delete team because related records exist (e.g., players, match records, event registrations). Please remove dependencies first.",
                 "details": str(db_err)
             }), 409 # Conflict
        current_app.logger.error(f"Database Error deleting team {team_id}: {db_err}")
        if conn: conn.rollback()
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error deleting team {team_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# --- Player Management within Teams ---

# 6. Add Player to Team (POST /teams/<team_id>/players)
@teams_bp.route('/<int:team_id>/players', methods=['POST'])
@token_required
def add_player_to_team(current_user_id, current_user_role, team_id):
    """Adds a player (MemberID) to a specific team. Requires Admin or Coach role."""
    current_app.logger.info(f"Request: Add player to Team ID: {team_id} by User ID: {current_user_id}, Role: {current_user_role}")

    # RBAC Check: Allow Admin or Coach (adjust if needed)
    # You might need more complex logic to check if the coach is the *correct* coach for this team
    if current_user_role not in ['admin', 'Coach']:
        current_app.logger.warning(f"User {current_user_id} (Role: {current_user_role}) unauthorized to add player to team {team_id}.")
        return jsonify({"error": "Admin or Coach privileges required"}), 403

    try:
        data = request.get_json()
        if not data or not data.get('member_id'):
            return jsonify({"error": "Missing required field: member_id"}), 400
        member_id = int(data['member_id'])
        position = data.get('position') # Optional position
        # Note: PerformanceStatistics might be calculated or updated elsewhere
    except (ValueError, TypeError, Exception) as e:
        current_app.logger.error(f"Error parsing add player request JSON or casting IDs: {e}")
        return jsonify({"error": "Invalid JSON data or non-integer member_id"}), 400

    # --- Validate Member exists in CIMS ---
    if not check_member_exists(member_id):
        return jsonify({"error": f"Player with MemberID {member_id} does not exist in CIMS."}), 400
    # --- End Validation ---

    conn = None
    cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "Project database connection failed"}), 500
        cursor = conn.cursor()

        # Assumes table `Player` with columns `MemberID`, `TeamID`, `Position_`
        sql_add_player = "INSERT INTO Player (MemberID, TeamID, Position_) VALUES (%s, %s, %s)"
        cursor.execute(sql_add_player, (member_id, team_id, position))
        new_player_entry_id = cursor.lastrowid # Or PlayerID if that's the PK
        conn.commit()

        current_app.logger.info(f"User {current_user_id} added MemberID {member_id} to TeamID {team_id} (Player Entry ID: {new_player_entry_id})")
        return jsonify({"message": "Player added to team successfully", "player_entry_id": new_player_entry_id}), 201

    except mysql.connector.Error as db_err:
        # Handle FK error if team_id doesn't exist (1452)
        # Handle duplicate error if (MemberID, TeamID) must be unique (1062)
        if db_err.errno == 1452:
             return jsonify({"error": "Team ID does not exist.", "details": str(db_err)}), 404
        elif db_err.errno == 1062:
             return jsonify({"error": "This member is already on this team.", "details": str(db_err)}), 409 # Conflict
        current_app.logger.error(f"Database Error adding player to team {team_id}: {db_err}")
        if conn: conn.rollback()
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error adding player to team {team_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 7. List Players in Team (GET /teams/<team_id>/players)
@teams_bp.route('/<int:team_id>/players', methods=['GET'])
@token_required
def list_players_in_team(current_user_id, current_user_role, team_id):
    """Lists all players (MemberIDs) associated with a specific team."""
    current_app.logger.info(f"Request: List players for Team ID: {team_id} by User ID: {current_user_id}")
    # No specific RBAC needed beyond authentication

    conn = None
    cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "Project database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Assumes table `Player` with columns `MemberID`, `TeamID`, `Position_`, `PlayerID`
        # Optional: JOIN with members table in CIMS DB to get names (more complex)
        sql_list_players = "SELECT PlayerID, MemberID, Position_ FROM Player WHERE TeamID = %s"
        cursor.execute(sql_list_players, (team_id,))
        players = cursor.fetchall()

        # Check if team exists implicitly (query returns no rows if team_id is invalid)
        # Add explicit check if needed

        current_app.logger.info(f"Retrieved {len(players)} players for Team ID: {team_id}")
        return jsonify(players), 200

    except mysql.connector.Error as db_err:
        # ... (standard error handling) ...
        current_app.logger.error(f"Database Error listing players for team {team_id}: {db_err}")
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error listing players {team_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 8. Remove Player from Team (DELETE /teams/<team_id>/players/<member_id>)
@teams_bp.route('/<int:team_id>/players/<int:member_id>', methods=['DELETE'])
@token_required
def remove_player_from_team(current_user_id, current_user_role, team_id, member_id):
    """Removes a player (MemberID) from a specific team. Requires Admin or Coach role."""
    current_app.logger.info(f"Request: Remove MemberID {member_id} from Team ID: {team_id} by User ID: {current_user_id}")

    # RBAC Check: Allow Admin or Coach (adjust if needed)
    if current_user_role not in ['admin', 'Coach']:
        current_app.logger.warning(f"User {current_user_id} (Role: {current_user_role}) unauthorized to remove player from team {team_id}.")
        return jsonify({"error": "Admin or Coach privileges required"}), 403

    conn = None
    cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "Project database connection failed"}), 500
        cursor = conn.cursor()

        # Assumes table `Player` with columns `MemberID`, `TeamID`
        sql_remove_player = "DELETE FROM Player WHERE MemberID = %s AND TeamID = %s"
        cursor.execute(sql_remove_player, (member_id, team_id))

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Delete failed: Player MemberID {member_id} not found on Team ID {team_id}.")
            return jsonify({"error": f"Player MemberID {member_id} not found on Team ID {team_id}"}), 404

        conn.commit()
        current_app.logger.info(f"User {current_user_id} removed MemberID {member_id} from TeamID {team_id}")
        return jsonify({"message": "Player removed from team successfully"}), 200

    except mysql.connector.Error as db_err:
        # ... (standard error handling) ...
        current_app.logger.error(f"Database Error removing player {member_id} from team {team_id}: {db_err}")
        if conn: conn.rollback()
        return jsonify({"error": "Database error occurred", "details": str(db_err)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error removing player {member_id} from team {team_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
# app/matches/routes.py
from flask import Blueprint, request, jsonify, current_app
import mysql.connector
import datetime
import logging

from ..auth.decorators import token_required
from ..utils.database import get_project_db_connection
# Import helpers needed
from ..utils.helpers import is_event_valid, check_team_exists, check_venue_exists

matches_bp = Blueprint('matches', __name__)

# --- Helper Function to Check Match Scheduling Conflicts ---
def check_scheduling_conflict(event_id, match_date, slot, venue_id, team1_id, team2_id, exclude_match_id=None):
    """Checks for venue/slot conflicts AND team double-booking."""
    conn = None; cursor = None
    conflict = None # None = no conflict, otherwise string description
    try:
        conn = get_project_db_connection()
        if not conn: return "Database connection failed during check"
        cursor = conn.cursor(dictionary=True)

        # 1. Check Venue/Slot conflict
        sql_venue = """
            SELECT MatchID FROM Match_
            WHERE EventID = %s AND MatchDate = %s AND Slot = %s AND VenueID = %s
        """
        params_venue = [event_id, match_date, slot, venue_id]
        if exclude_match_id:
            sql_venue += " AND MatchID != %s"
            params_venue.append(exclude_match_id)
        cursor.execute(sql_venue, tuple(params_venue))
        if cursor.fetchone():
            return f"Venue conflict: Venue {venue_id} is already booked for slot {slot} on {match_date}."

        # 2. Check Team 1 conflict
        sql_team1 = """
            SELECT MatchID FROM Match_
            WHERE EventID = %s AND MatchDate = %s AND Slot = %s AND (Team1ID = %s OR Team2ID = %s)
        """
        params_team1 = [event_id, match_date, slot, team1_id, team1_id]
        if exclude_match_id:
            sql_team1 += " AND MatchID != %s"
            params_team1.append(exclude_match_id)
        cursor.execute(sql_team1, tuple(params_team1))
        if cursor.fetchone():
            return f"Team conflict: Team {team1_id} already has a match in slot {slot} on {match_date}."

        # 3. Check Team 2 conflict
        sql_team2 = """
            SELECT MatchID FROM Match_
            WHERE EventID = %s AND MatchDate = %s AND Slot = %s AND (Team1ID = %s OR Team2ID = %s)
        """
        params_team2 = [event_id, match_date, slot, team2_id, team2_id]
        if exclude_match_id:
            sql_team2 += " AND MatchID != %s"
            params_team2.append(exclude_match_id)
        cursor.execute(sql_team2, tuple(params_team2))
        if cursor.fetchone():
            return f"Team conflict: Team {team2_id} already has a match in slot {slot} on {match_date}."

    except mysql.connector.Error as db_err:
        current_app.logger.error(f"DB Error checking schedule conflict: {db_err}")
        conflict = "Database error during conflict check"
    except Exception as e:
        current_app.logger.error(f"Error checking schedule conflict: {e}", exc_info=True)
        conflict = "Server error during conflict check"
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
    return conflict


# --- MATCH CRUD & Logic ---

# 1. Schedule Match (POST /matches/) - Admin or Organizer
@matches_bp.route('/', methods=['POST'])
@token_required
def schedule_match(current_user_id, current_user_role):
    """Schedules a new match. Requires Admin or Organizer role."""
    current_app.logger.info(f"Request: Schedule Match by User ID: {current_user_id}")
    allowed_roles = ['admin', 'Organizer']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    try:
        data = request.get_json()
        event_id = data.get('event_id')
        team1_id = data.get('team1_id')
        team2_id = data.get('team2_id')
        match_date_str = data.get('match_date') # YYYY-MM-DD
        slot = data.get('slot') # Must match ENUM value
        venue_id = data.get('venue_id')

        if not all([event_id, team1_id, team2_id, match_date_str, slot, venue_id]):
            return jsonify({"error": "Missing fields: event_id, team1_id, team2_id, match_date, slot, venue_id"}), 400

        event_id = int(event_id)
        team1_id = int(team1_id)
        team2_id = int(team2_id)
        venue_id = int(venue_id)
        match_date = datetime.date.fromisoformat(match_date_str)

        # --- Basic Constraint Checks ---
        if team1_id == team2_id: return jsonify({"error": "Team cannot play against itself"}), 400
        # Add check for valid ENUM slot value? Connector might handle, or check here.
        # --- End Basic Checks ---

    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid JSON data or data types (check IDs, date format)"}), 400

    # --- Existence Checks ---
    is_valid, error_message = is_event_valid(event_id)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    if not check_team_exists(team1_id): return jsonify({"error": f"Team1 {team1_id} not found"}), 404
    if not check_team_exists(team2_id): return jsonify({"error": f"Team2 {team2_id} not found"}), 404
    if not check_venue_exists(venue_id): return jsonify({"error": f"Venue {venue_id} not found"}), 404
    # Optional: Check minimum players per team? Check teams registered for event?

    # --- Scheduling Conflict Check ---
    conflict = check_scheduling_conflict(event_id, match_date, slot, venue_id, team1_id, team2_id)
    if conflict:
        current_app.logger.warning(f"Scheduling conflict detected: {conflict}")
        return jsonify({"error": f"Scheduling conflict: {conflict}"}), 409
    # --- End Conflict Check ---

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        # Assumes Match_(MatchID PK AI, EventID FK, Team1ID FK, Team2ID FK, MatchDate, Slot ENUM, VenueID FK, Team1Score INT default 0?, Team2Score INT default 0?, WinnerID INT null FK)
        # Set initial scores to 0
        sql = """
            INSERT INTO Match_ (EventID, Team1ID, Team2ID, MatchDate, Slot, VenueID, Team1Score, Team2Score, WinnerID)
            VALUES (%s, %s, %s, %s, %s, %s, 0, 0, NULL)
        """
        cursor.execute(sql, (event_id, team1_id, team2_id, match_date, slot, venue_id))
        new_match_id = cursor.lastrowid
        conn.commit()
        current_app.logger.info(f"User {current_user_id} scheduled Match ID: {new_match_id}")
        return jsonify({"message": "Match scheduled", "MatchID": new_match_id}), 201

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        # Handle potential errors like invalid ENUM value for slot, FK violations if checks missed
        current_app.logger.error(f"DB Error scheduling match: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error scheduling match: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 2. List Matches (GET /matches/) - Any Authenticated User
@matches_bp.route('/', methods=['GET'])
@token_required
def list_matches(current_user_id, current_user_role):
    """Lists matches, optionally filtered by event, team, venue, date."""
    current_app.logger.info(f"Request: List Matches by User ID: {current_user_id}")
    # Get query parameters for filtering
    event_id_filter = request.args.get('event_id', type=int)
    team_id_filter = request.args.get('team_id', type=int)
    venue_id_filter = request.args.get('venue_id', type=int)
    date_filter = request.args.get('date') # YYYY-MM-DD string

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Base query - JOINs for more context
        sql = """
            SELECT m.MatchID, m.EventID, e.EventName, m.Team1ID, t1.TeamName as Team1Name,
                   m.Team2ID, t2.TeamName as Team2Name, DATE_FORMAT(m.MatchDate, '%Y-%m-%d') as MatchDate,
                   m.Slot, m.VenueID, v.VenueName, m.Team1Score, m.Team2Score, m.WinnerID,
                   win.TeamName as WinnerName
            FROM Match_ m
            JOIN Event_ e ON m.EventID = e.EventID
            JOIN Team t1 ON m.Team1ID = t1.TeamID
            JOIN Team t2 ON m.Team2ID = t2.TeamID
            JOIN Venue v ON m.VenueID = v.VenueID
            LEFT JOIN Team win ON m.WinnerID = win.TeamID
        """
        filters = []
        params = []

        if event_id_filter:
            filters.append("m.EventID = %s")
            params.append(event_id_filter)
        if team_id_filter:
            filters.append("(m.Team1ID = %s OR m.Team2ID = %s)")
            params.extend([team_id_filter, team_id_filter])
        if venue_id_filter:
            filters.append("m.VenueID = %s")
            params.append(venue_id_filter)
        if date_filter:
            try:
                datetime.date.fromisoformat(date_filter) # Validate date format
                filters.append("m.MatchDate = %s")
                params.append(date_filter)
            except ValueError:
                return jsonify({"error": "Invalid date format for filter. Use YYYY-MM-DD."}), 400

        if filters:
            sql += " WHERE " + " AND ".join(filters)

        sql += " ORDER BY m.MatchDate, m.Slot"

        cursor.execute(sql, tuple(params))
        matches = cursor.fetchall()
        return jsonify(matches), 200

    except Exception as e:
        current_app.logger.error(f"Error listing matches: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve matches"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# 3. Get Match Details (GET /matches/<id>) - Any Authenticated User
@matches_bp.route('/<int:match_id>', methods=['GET'])
@token_required
def get_match_details(current_user_id, current_user_role, match_id):
    """Gets full details for a specific match."""
    current_app.logger.info(f"Request: Get Match ID: {match_id} by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        # Same JOINed query as list, but for specific ID
        sql = """
            SELECT m.MatchID, m.EventID, e.EventName, m.Team1ID, t1.TeamName as Team1Name,
                   m.Team2ID, t2.TeamName as Team2Name, DATE_FORMAT(m.MatchDate, '%Y-%m-%d') as MatchDate,
                   m.Slot, m.VenueID, v.VenueName, m.Team1Score, m.Team2Score, m.WinnerID,
                   win.TeamName as WinnerName
            FROM Match_ m
            JOIN Event_ e ON m.EventID = e.EventID
            JOIN Team t1 ON m.Team1ID = t1.TeamID
            JOIN Team t2 ON m.Team2ID = t2.TeamID
            JOIN Venue v ON m.VenueID = v.VenueID
            LEFT JOIN Team win ON m.WinnerID = win.TeamID
            WHERE m.MatchID = %s
        """
        cursor.execute(sql, (match_id,))
        match = cursor.fetchone()
        if not match: return jsonify({"error": f"Match ID {match_id} not found"}), 404
        return jsonify(match), 200
    except Exception as e:
        current_app.logger.error(f"Error getting match {match_id}: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve match details"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 4. Submit/Update Match Results (PUT /matches/<id>/score) - Admin or Referee
@matches_bp.route('/<int:match_id>/score', methods=['PUT'])
@token_required
def update_match_score(current_user_id, current_user_role, match_id):
    """Updates the score and winner for a match. Requires Admin or Referee role."""
    current_app.logger.info(f"Request: Update score for Match ID: {match_id} by User ID: {current_user_id}")

    allowed_roles = ['admin', 'Referee'] # Use exact role name from DB
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403
    # Enhancement: Could add check if this Referee is assigned to this match/event

    try:
        data = request.get_json()
        team1_score = data.get('team1_score')
        team2_score = data.get('team2_score')
        winner_id = data.get('winner_id') # Can be None/null if it's a draw or undecided

        if team1_score is None or team2_score is None:
             return jsonify({"error": "Missing fields: team1_score, team2_score"}), 400

        team1_score = int(team1_score)
        team2_score = int(team2_score)
        if team1_score < 0 or team2_score < 0:
             return jsonify({"error": "Scores cannot be negative"}), 400

        # Validate winner_id if provided
        winner_id_to_set = None
        if winner_id is not None:
             winner_id = int(winner_id)
             # Check if winner_id is one of the playing teams (DB trigger also checks)
             conn_check = None; cursor_check = None
             try:
                 conn_check = get_project_db_connection()
                 cursor_check = conn_check.cursor(dictionary=True)
                 cursor_check.execute("SELECT Team1ID, Team2ID FROM Match_ WHERE MatchID = %s", (match_id,))
                 match_teams = cursor_check.fetchone()
                 if not match_teams: return jsonify({"error": f"Match ID {match_id} not found"}), 404
                 if winner_id not in [match_teams['Team1ID'], match_teams['Team2ID']]:
                      return jsonify({"error": "Winner ID must be one of the participating teams"}), 400
                 winner_id_to_set = winner_id # Set to integer ID if valid
             finally:
                 if cursor_check: cursor_check.close()
                 if conn_check and conn_check.is_connected(): conn_check.close()
        # else: winner_id_to_set remains None

    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid JSON data or non-integer score/winner ID"}), 400

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()

        sql = "UPDATE Match_ SET Team1Score = %s, Team2Score = %s, WinnerID = %s WHERE MatchID = %s"
        cursor.execute(sql, (team1_score, team2_score, winner_id_to_set, match_id))

        if cursor.rowcount == 0: return jsonify({"error": f"Match ID {match_id} not found during update"}), 404

        conn.commit()
        current_app.logger.info(f"User {current_user_id} updated score for Match ID: {match_id}")
        return jsonify({"message": "Match score updated", "MatchID": match_id}), 200

    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        # DB Trigger might raise generic 45000 state, check message?
        current_app.logger.error(f"DB Error updating score for match {match_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error updating score for match {match_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 5. Cancel/Delete Match (DELETE /matches/<id>) - Admin or Organizer
@matches_bp.route('/<int:match_id>', methods=['DELETE'])
@token_required
def delete_match(current_user_id, current_user_role, match_id):
    """Deletes/cancels a scheduled match. Requires Admin or Organizer role."""
    current_app.logger.info(f"Request: Delete Match ID: {match_id} by User ID: {current_user_id}")
    allowed_roles = ['admin', 'Organizer']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        sql = "DELETE FROM Match_ WHERE MatchID = %s"
        cursor.execute(sql, (match_id,))

        if cursor.rowcount == 0: return jsonify({"error": f"Match ID {match_id} not found"}), 404

        conn.commit()
        current_app.logger.info(f"User {current_user_id} deleted Match ID: {match_id}")
        return jsonify({"message": "Match deleted successfully", "MatchID": match_id}), 200
    except mysql.connector.Error as db_err:
        # No obvious FK constraints pointing *from* Match_, but handle errors
        if conn: conn.rollback()
        current_app.logger.error(f"DB Error deleting match {match_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error deleting match {match_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
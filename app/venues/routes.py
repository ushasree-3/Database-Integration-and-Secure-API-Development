# app/venues/routes.py
from flask import Blueprint, request, jsonify, current_app
import mysql.connector
import logging

from ..auth.decorators import token_required
from ..utils.database import get_project_db_connection
from ..utils.helpers import check_venue_exists # Import new helper

venues_bp = Blueprint('venues', __name__)

# --- VENUE CRUD ---

# 1. Add Venue (POST /venues/) - Admin or Organizer
@venues_bp.route('/', methods=['POST'])
@token_required
def add_venue(current_user_id, current_user_role):
    """Adds a new venue. Requires Admin or Organizer role."""
    current_app.logger.info(f"Request: Add Venue by User ID: {current_user_id}")
    allowed_roles = ['admin', 'Organizer']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    try:
        data = request.get_json()
        venue_name = data.get('venue_name')
        location = data.get('location')
        if not all([venue_name, location]):
            return jsonify({"error": "Missing fields: venue_name, location"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid JSON data"}), 400

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        # Assumes Venue(VenueID PK AI, VenueName, Location)
        sql = "INSERT INTO Venue (VenueName, Location) VALUES (%s, %s)"
        cursor.execute(sql, (venue_name, location))
        new_venue_id = cursor.lastrowid
        conn.commit()
        current_app.logger.info(f"User {current_user_id} added Venue ID: {new_venue_id}")
        return jsonify({"message": "Venue added", "VenueID": new_venue_id}), 201
    except mysql.connector.Error as db_err:
        # Handle potential UNIQUE constraint on VenueName/Location if defined
        if conn: conn.rollback()
        current_app.logger.error(f"DB Error adding venue: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error adding venue: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 2. List Venues (GET /venues/) - Any Authenticated User
@venues_bp.route('/', methods=['GET'])
@token_required
def list_venues(current_user_id, current_user_role):
    """Lists all venues."""
    current_app.logger.info(f"Request: List Venues by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT VenueID, VenueName, Location FROM Venue ORDER BY VenueName")
        venues = cursor.fetchall()
        return jsonify(venues), 200
    except Exception as e:
        current_app.logger.error(f"Error listing venues: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve venues"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 3. Get Venue (GET /venues/<id>) - Any Authenticated User
@venues_bp.route('/<int:venue_id>', methods=['GET'])
@token_required
def get_venue(current_user_id, current_user_role, venue_id):
    """Gets details for a specific venue."""
    current_app.logger.info(f"Request: Get Venue ID: {venue_id} by User ID: {current_user_id}")
    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT VenueID, VenueName, Location FROM Venue WHERE VenueID = %s", (venue_id,))
        venue = cursor.fetchone()
        if not venue: return jsonify({"error": f"Venue ID {venue_id} not found"}), 404
        return jsonify(venue), 200
    except Exception as e:
        current_app.logger.error(f"Error getting venue {venue_id}: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve venue"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 4. Update Venue (PUT /venues/<id>) - Admin or Organizer
@venues_bp.route('/<int:venue_id>', methods=['PUT'])
@token_required
def update_venue(current_user_id, current_user_role, venue_id):
    """Updates a venue. Requires Admin or Organizer role."""
    current_app.logger.info(f"Request: Update Venue ID: {venue_id} by User ID: {current_user_id}")
    allowed_roles = ['admin', 'Organizer']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    try:
        data = request.get_json()
        venue_name = data.get('venue_name')
        location = data.get('location')
        if not all([venue_name, location]):
            return jsonify({"error": "Missing fields: venue_name, location"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid JSON data"}), 400

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        sql = "UPDATE Venue SET VenueName = %s, Location = %s WHERE VenueID = %s"
        cursor.execute(sql, (venue_name, location, venue_id))
        if cursor.rowcount == 0: return jsonify({"error": f"Venue ID {venue_id} not found"}), 404
        conn.commit()
        current_app.logger.info(f"User {current_user_id} updated Venue ID: {venue_id}")
        return jsonify({"message": "Venue updated", "VenueID": venue_id}), 200
    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        current_app.logger.error(f"DB Error updating venue {venue_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error updating venue {venue_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# 5. Delete Venue (DELETE /venues/<id>) - Admin or Organizer
@venues_bp.route('/<int:venue_id>', methods=['DELETE'])
@token_required
def delete_venue(current_user_id, current_user_role, venue_id):
    """Deletes a venue. Requires Admin or Organizer role."""
    current_app.logger.info(f"Request: Delete Venue ID: {venue_id} by User ID: {current_user_id}")
    allowed_roles = ['admin', 'Organizer']
    if current_user_role not in allowed_roles:
        return jsonify({"error": f"One of {allowed_roles} privileges required"}), 403

    conn = None; cursor = None
    try:
        conn = get_project_db_connection()
        if not conn: return jsonify({"error": "DB connection failed"}), 500
        cursor = conn.cursor()
        sql = "DELETE FROM Venue WHERE VenueID = %s"
        cursor.execute(sql, (venue_id,))
        if cursor.rowcount == 0: return jsonify({"error": f"Venue ID {venue_id} not found"}), 404
        conn.commit()
        current_app.logger.info(f"User {current_user_id} deleted Venue ID: {venue_id}")
        return jsonify({"message": "Venue deleted", "VenueID": venue_id}), 200
    except mysql.connector.Error as db_err:
        if conn: conn.rollback()
        if db_err.errno == 1451: # FK constraint (Matches might use this venue)
            current_app.logger.warning(f"FK constraint fail delete venue {venue_id}: {db_err}")
            return jsonify({"error": "Cannot delete venue, it is used in scheduled matches."}), 409
        current_app.logger.error(f"DB Error deleting venue {venue_id}: {db_err}")
        return jsonify({"error": "DB error", "details": str(db_err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        current_app.logger.error(f"Error deleting venue {venue_id}: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
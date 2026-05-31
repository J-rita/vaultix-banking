from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..database import execute_query

bp = Blueprint('notifications', __name__)

@bp.route('/list', methods=['GET'])
@jwt_required()
def get_notifications():
    """Retrieve all notifications for the user."""
    try:
        username = get_jwt_identity()
        user_res = execute_query("SELECT USER_ID FROM USERS WHERE USERNAME = :1", [username])
        user_id = user_res[0]['USER_ID']
        
        notifs = execute_query("SELECT * FROM NOTIFICATIONS WHERE USER_ID = :1 ORDER BY CREATED_AT DESC", [user_id])
        return jsonify({"status": "success", "notifications": notifs})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@bp.route('/read/<int:notif_id>', methods=['POST'])
@jwt_required()
def mark_as_read(notif_id):
    """Mark a notification as read."""
    try:
        execute_query("UPDATE NOTIFICATIONS SET IS_READ = 1 WHERE NOTIFICATION_ID = :1", [notif_id], commit=True)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

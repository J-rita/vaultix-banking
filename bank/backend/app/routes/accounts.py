from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..database_manager import db
import traceback

bp = Blueprint('accounts', __name__)

@bp.route('/my-accounts', methods=['GET'])
@jwt_required()
def get_my_accounts():
    try:
        username = get_jwt_identity()
        user_res = db.execute_query("SELECT * FROM Customers WHERE username = :1", [username])
        if not user_res:
            return jsonify({"status": "error", "detail": "User not found"}), 404
        user_id = user_res[0]['customer_id']
        accounts = db.execute_query("SELECT * FROM Accounts WHERE customer_id = :1", [user_id])
        # Return properly mapped response for UI
        formatted_accounts = []
        for acc in accounts:
            formatted_accounts.append({
                "ACCOUNT_ID": acc.get('account_id'),
                "ACCOUNT_NUMBER": acc.get('account_number'),
                "ACCOUNT_TYPE": acc.get('account_type'),
                "BALANCE": acc.get('balance'),
                "STATUS": acc.get('status')
            })
        return jsonify({"status": "success", "accounts": formatted_accounts}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_account():
    try:
        account_number = request.args.get('account_number', '').strip()
        if not account_number:
            return jsonify({"status": "error", "detail": "Account number required"}), 400

        accounts = db.execute_query("SELECT * FROM Accounts WHERE account_number = :1", [account_number])
        if not accounts:
            return jsonify({"status": "error", "detail": "Account not found"}), 404

        account = accounts[0]
        user_res = db.execute_query("SELECT * FROM Customers WHERE customer_id = :1", [account['customer_id']])
        if not user_res:
            return jsonify({"status": "error", "detail": "Account holder not found"}), 404

        user = user_res[0]
        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        return jsonify({"status": "success", "account_name": full_name}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@bp.route('/summary', methods=['GET'])
@jwt_required()
def get_account_summary():
    try:
        username = get_jwt_identity()
        user_res = db.execute_query("SELECT * FROM Customers WHERE username = :1", [username])
        user_id = user_res[0]['customer_id']
        accounts = db.execute_query("SELECT * FROM Accounts WHERE customer_id = :1", [user_id])
        total_balance = sum(acc['balance'] for acc in accounts)
        return jsonify({
            "status": "success", 
            "total_balance": total_balance, 
            "account_count": len(accounts), 
            "user_name": f"{user_res[0]['first_name']} {user_res[0]['last_name']}"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        username = get_jwt_identity()
        user_res = db.execute_query("SELECT * FROM Customers WHERE username = :1", [username])
        if not user_res:
            return jsonify({"status": "error", "detail": "User not found"}), 404
        user = user_res[0]
        user.pop('password_hash', None)
        # Format for UI expectations
        formatted_user = {
            "FIRST_NAME": user.get('first_name'),
            "LAST_NAME": user.get('last_name'),
            "EMAIL": user.get('email'),
            "USERNAME": user.get('username'),
            "PHONE": user.get('phone_number'),
            "ADDRESS": user.get('address')
        }
        return jsonify({"status": "success", "profile": formatted_user}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import traceback
from ..database_manager import db
from ..auth.security import get_password_hash, verify_password

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        phone_number = data.get('phone_number', '').strip()
        password = data.get('password', '').strip()
        transaction_pin = data.get('transaction_pin', '').strip()

        if not all([username, email, password, transaction_pin]):
            return jsonify({"status": "error", "detail": "Missing fields"}), 400
            
        if '@' not in email:
            return jsonify({"status": "error", "detail": "Invalid email address format"}), 400
            
        if phone_number and (not phone_number.isdigit() or len(phone_number) != 11):
            return jsonify({"status": "error", "detail": "Phone number must be exactly 11 digits"}), 400

        if not transaction_pin.isdigit() or len(transaction_pin) != 4:
            return jsonify({"status": "error", "detail": "Transaction PIN must be exactly 4 digits"}), 400

        check_query = "SELECT * FROM Customers WHERE username = :1 OR email = :2"
        existing_user = db.execute_query(check_query, [username, email])
        
        if existing_user and len(existing_user) > 0:
            return jsonify({"status": "error", "detail": "Username or email already exists"}), 409
        
        hashed_pw = get_password_hash(password)
        hashed_pin = get_password_hash(transaction_pin)
        insert_query = "INSERT INTO Customers (username, email, password_hash, first_name, last_name, phone_number, transaction_pin_hash) VALUES (:1, :2, :3, :4, :5, :6, :7)"
        db.execute_query(insert_query, [username, email, hashed_pw, first_name, last_name, phone_number, hashed_pin], commit=True)

        new_customer = db.execute_query("SELECT * FROM Customers WHERE username = :1", [username])
        if new_customer:
            cust_id = int(new_customer[0].get('customer_id'))
            savings_num = f"214{cust_id:07d}"
            current_num = f"224{cust_id:07d}"
            db.execute_query(
                "INSERT INTO Accounts (customer_id, account_number, account_type, balance, interest_rate, overdraft_limit, status) VALUES (:1, :2, :3, :4, :5, :6, :7)",
                [cust_id, savings_num, 'Savings', 0.0, 0.05, 0.0, 'Active'], commit=True
            )
            db.execute_query(
                "INSERT INTO Accounts (customer_id, account_number, account_type, balance, interest_rate, overdraft_limit, status) VALUES (:1, :2, :3, :4, :5, :6, :7)",
                [cust_id, current_num, 'Current', 0.0, 0.0, 50000.0, 'Active'], commit=True
            )

        return jsonify({"status": "success", "message": "Account created"}), 201
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({"status": "error", "detail": "Missing credentials"}), 400

        staff = db.execute_query("SELECT * FROM BankStaff WHERE username = :1", [username])
        if staff and len(staff) > 0:
            user = staff[0]
            if verify_password(password, user['password_hash']):
                token = create_access_token(identity=user['username'], additional_claims={"role": user['role']})
                return jsonify({"status": "success", "access_token": token, "role": user['role'], "username": user['username']}), 200

        customer = db.execute_query("SELECT * FROM Customers WHERE username = :1 OR email = :2 OR phone_number = :3", [username, username, username])
        if customer and len(customer) > 0:
            user = customer[0]
            if verify_password(password, user['password_hash']):
                token = create_access_token(identity=user['username'], additional_claims={"role": "Customer"})
                return jsonify({"status": "success", "access_token": token, "role": "Customer", "username": user['username']}), 200

        return jsonify({"status": "error", "detail": "Invalid username or password"}), 401

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "detail": "Internal server error"}), 500

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        username = get_jwt_identity()
        data = request.get_json()
        current_pw = data.get('current_password')
        new_pw = data.get('new_password')
        
        user_res = db.execute_query("SELECT * FROM Customers WHERE username = :1", [username])
        if user_res:
            user = user_res[0]
            if not verify_password(current_pw, user['password_hash']):
                return jsonify({"status": "error", "detail": "Incorrect current password"}), 401
            new_hash = get_password_hash(new_pw)
            db.execute_query("UPDATE Customers SET password_hash = :1 WHERE username = :2", [new_hash, username], commit=True)
            return jsonify({"status": "success", "message": "Password updated successfully"}), 200
            
        return jsonify({"status": "error", "detail": "User not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

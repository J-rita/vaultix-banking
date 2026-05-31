from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..database_manager import db
import traceback

bp = Blueprint('admin', __name__)

def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'Admin':
            return jsonify({"status": "error", "detail": "Administration access required"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    users = db.execute_query("SELECT * FROM Customers")
    formatted_users = []
    for u in users:
        formatted_users.append({
            "USER_ID": u.get('customer_id'),
            "USERNAME": u.get('username'),
            "EMAIL": u.get('email'),
            "FIRST_NAME": u.get('first_name'),
            "LAST_NAME": u.get('last_name'),
            "ROLE": "Customer",
            "STATUS": u.get('status'),
            "CREATED_AT": u.get('created_at')
        })
    return jsonify({"status": "success", "users": formatted_users})

@bp.route('/transactions', methods=['GET'])
@admin_required
def get_all_transactions():
    txs = db.execute_query("SELECT * FROM Transactions ORDER BY created_at DESC")
    formatted_txs = []
    for t in txs:
        formatted_txs.append({
            "TRANSACTION_ID": t.get('transaction_id'),
            "SENDER_ACCOUNT_ID": t.get('account_id'),
            "AMOUNT": t.get('amount'),
            "TRANSACTION_TYPE": t.get('transaction_type'),
            "CREATED_AT": t.get('created_at')
        })
    return jsonify({"status": "success", "transactions": formatted_txs})

@bp.route('/audit-logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """Enterprise Audit Log viewing endpoint."""
    logs = db.execute_query("SELECT * FROM AuditLogs ORDER BY log_timestamp DESC")
    formatted_logs = []
    for l in (logs or []):
        formatted_logs.append({
            "LOG_ID": l.get('log_id'),
            "ACTION_TYPE": l.get('action_type'),
            "TABLE_NAME": l.get('table_name'),
            "RECORD_ID": l.get('record_id'),
            "OLD_VALUE": l.get('old_value'),
            "NEW_VALUE": l.get('new_value'),
            "PERFORMED_BY": l.get('performed_by'),
            "TIMESTAMP": l.get('log_timestamp')
        })
    return jsonify({"status": "success", "logs": formatted_logs})

@bp.route('/loans', methods=['GET'])
@admin_required
def get_all_loans():
    """Return all loan applications system-wide for admin review."""
    loans = db.execute_query("SELECT * FROM Loans ORDER BY created_at DESC")
    formatted = []
    for l in (loans or []):
        formatted.append({
            "LOAN_ID": l.get('loan_id'),
            "USER_ID": l.get('customer_id'),
            "AMOUNT": l.get('amount'),
            "INTEREST_RATE": l.get('interest_rate'),
            "TERM_MONTHS": l.get('term_months'),
            "STATUS": l.get('status'),
            "CREATED_AT": l.get('created_at')
        })
    return jsonify({"status": "success", "loans": formatted})

@bp.route('/user/status', methods=['POST'])
@admin_required
def update_user_status():
    """Freeze or activate a customer account."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        status = data.get('status')
        if status not in ('Active', 'Suspended', 'Frozen'):
            return jsonify({"status": "error", "detail": "Invalid status value"}), 400
        db.execute_query(
            "UPDATE Customers SET status = :1 WHERE customer_id = :2",
            [status, user_id], commit=True
        )
        return jsonify({"status": "success", "message": f"User status updated to {status}"}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "detail": str(e)}), 500

@bp.route('/loan/review', methods=['POST'])
@admin_required
def review_loan():
    """Approve or reject a pending loan. If approved, credit funds to the applicant."""
    try:
        data = request.get_json()
        loan_id = data.get('loan_id')
        decision = data.get('decision')  # 'Approved' or 'Rejected'

        if decision not in ('Approved', 'Rejected'):
            return jsonify({"status": "error", "detail": "Decision must be Approved or Rejected"}), 400

        loan_res = db.execute_query("SELECT * FROM Loans WHERE loan_id = :1", [loan_id])
        if not loan_res:
            return jsonify({"status": "error", "detail": "Loan not found"}), 404
        loan = loan_res[0]

        # Update loan status
        db.execute_query("UPDATE Loans SET status = :1 WHERE loan_id = :2", [decision, loan_id], commit=True)

        if decision == 'Approved':
            # Credit funds to customer's primary account
            accounts = db.execute_query(
                "SELECT * FROM Accounts WHERE customer_id = :1 AND account_type = 'Savings'",
                [loan['customer_id']]
            )
            if accounts:
                acc_id = accounts[0]['account_id']
                amount = loan['amount']
                db.execute_query(
                    "UPDATE Accounts SET balance = balance + :1 WHERE account_id = :2",
                    [amount, acc_id], commit=True
                )
                db.execute_query(
                    "INSERT INTO Transactions (account_id, amount, transaction_type, description, status) VALUES (:1, :2, :3, :4, :5)",
                    [acc_id, amount, 'Deposit', f'Loan #{loan_id} approved & disbursed', 'Completed'], commit=True
                )

        return jsonify({"status": "success", "message": f"Loan #{loan_id} has been {decision}."}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "detail": str(e)}), 500


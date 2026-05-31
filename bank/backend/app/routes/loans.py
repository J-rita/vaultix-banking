from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..database_manager import db
import traceback

bp = Blueprint('loans', __name__)

@bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_loan():
    """
    Submit a new loan application.
    Instantly approved — funds credited to primary account immediately.
    Expects JSON: {amount, term_months}
    """
    try:
        username = get_jwt_identity()
        data = request.get_json()

        amount = float(data.get('amount', 0))
        term = int(data.get('term_months', 12))

        if amount < 1000:
            return jsonify({"status": "error", "detail": "Minimum loan amount is ₦1,000"}), 400

        # Get User from Customers table
        user_res = db.execute_query("SELECT * FROM Customers WHERE username = :1", [username])
        if not user_res:
            return jsonify({"status": "error", "detail": "User not found"}), 404
        user_id = int(user_res[0]['customer_id'])

        # Get user's primary (savings) account
        accounts = db.execute_query("SELECT * FROM Accounts WHERE customer_id = :1", [user_id])
        if not accounts:
            return jsonify({"status": "error", "detail": "No account found to disburse funds"}), 404
        primary_account = accounts[0]
        account_id = primary_account['account_id']

        # Fixed interest rate of 5%
        interest_rate = 5.0

        # Save loan record as Pending (for admin review)
        db.execute_query(
            "INSERT INTO Loans (customer_id, amount, interest_rate, term_months, status) VALUES (:1, :2, :3, :4, :5)",
            [user_id, amount, interest_rate, term, 'Pending'],
            commit=True
        )

        return jsonify({
            "status": "success",
            "message": f"Loan application of ₦{amount:,.2f} submitted successfully! Awaiting admin review."
        }), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "detail": str(e)}), 500


@bp.route('/my-loans', methods=['GET'])
@jwt_required()
def get_my_loans():
    """List all loans for the current user."""
    try:
        username = get_jwt_identity()
        user_res = db.execute_query("SELECT * FROM Customers WHERE username = :1", [username])
        if not user_res:
            return jsonify({"status": "error", "detail": "User not found"}), 404
        user_id = int(user_res[0]['customer_id'])

        loans = db.execute_query("SELECT * FROM Loans WHERE customer_id = :1 ORDER BY created_at DESC", [user_id])
        formatted = []
        for l in (loans or []):
            formatted.append({
                "LOAN_ID": l.get('loan_id'),
                "AMOUNT": l.get('amount'),
                "INTEREST_RATE": l.get('interest_rate'),
                "TERM_MONTHS": l.get('term_months'),
                "STATUS": l.get('status'),
                "CREATED_AT": l.get('created_at')
            })
        return jsonify({"status": "success", "loans": formatted})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "detail": str(e)}), 500

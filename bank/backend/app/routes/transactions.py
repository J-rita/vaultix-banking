from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..database_manager import db
from ..services.transfer_service import TransferService
from ..models.exceptions import BankingException
import traceback

bp = Blueprint('transactions', __name__)

@bp.route('/deposit', methods=['POST'])
@jwt_required()
def deposit():
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        amount = float(data.get('amount', 0))
        description = data.get('description', 'ATM/Cash Deposit')
        
        TransferService.process_deposit(account_id, amount, description)
        
        return jsonify({"status": "success", "message": f"Successfully deposited {amount}"}), 200
    except BankingException as be:
        return jsonify({"status": "error", "detail": str(be)}), 400
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@bp.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw():
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        amount = float(data.get('amount', 0))
        description = data.get('description', 'ATM Withdrawal')
        
        TransferService.process_withdrawal(account_id, amount, description)
        
        return jsonify({"status": "success", "message": f"Successfully withdrawn {amount}"}), 200
    except BankingException as be:
        return jsonify({"status": "error", "detail": str(be)}), 400
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@bp.route('/transfer', methods=['POST'])
@jwt_required()
def transfer():
    try:
        data = request.get_json()
        sender_acc_id = data.get('sender_account_id')
        receiver_acc_num = data.get('receiver_account_number')
        amount = float(data.get('amount', 0))
        description = data.get('description', 'Funds Transfer')
        
        receiver_res = db.execute_query("SELECT * FROM Accounts WHERE account_number = :1", [receiver_acc_num])
        if not receiver_res:
            return jsonify({"status": "error", "detail": "Recipient account not found"}), 404
            
        receiver_id = receiver_res[0]['account_id']
        
        TransferService.process_transfer(sender_acc_id, receiver_id, amount, description)
        
        return jsonify({"status": "success", "message": "Funds transferred successfully"}), 200
    except BankingException as be:
        return jsonify({"status": "error", "detail": str(be)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "detail": "Internal transaction failure"}), 500

@bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    try:
        username = get_jwt_identity()
        user_res = db.execute_query("SELECT * FROM Customers WHERE username = :1", [username])
        if not user_res:
            return jsonify({"status": "error", "detail": "User not found"}), 404

        user_id = user_res[0]['customer_id']
        accounts = db.execute_query("SELECT account_id FROM Accounts WHERE customer_id = :1", [user_id])
        if not accounts:
            return jsonify({"status": "success", "transactions": []}), 200

        account_ids = [str(a['account_id']) for a in accounts]
        
        all_txs = []
        for acc_id in account_ids:
            rows = db.execute_query(
                "SELECT * FROM Transactions WHERE account_id = :1 ORDER BY created_at DESC", [acc_id]
            )
            if rows:
                for row in rows:
                    if not any(t.get('transaction_id') == row.get('transaction_id') for t in all_txs):
                        all_txs.append(row)

        formatted_txs = []
        for tx in all_txs:
            formatted_txs.append({
                "TRANSACTION_ID": tx.get('transaction_id'),
                "AMOUNT": tx.get('amount'),
                "TRANSACTION_TYPE": tx.get('transaction_type'),
                "DESCRIPTION": tx.get('description'),
                "CREATED_AT": tx.get('created_at'),
                "STATUS": tx.get('status')
            })

        return jsonify({"status": "success", "transactions": formatted_txs}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "detail": str(e)}), 500

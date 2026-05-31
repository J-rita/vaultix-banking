import datetime
from ..database_manager import db
from ..models.exceptions import InsufficientFundsException, InvalidAccountException

class TransferService:
    """Service class for handling core banking transactions using Oracle PL/SQL or mock DB fallback."""
    
    @staticmethod
    def process_deposit(account_id: int, amount: float, description: str = "Deposit"):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
            
        if db.use_oracle:
            status = db.execute_procedure("PROCESS_DEPOSIT", [account_id, amount, description])
            if status != 'SUCCESS':
                raise Exception(status)
        else:
            # Mock DB: update balance and log transaction
            accounts = db.execute_query("SELECT * FROM Accounts WHERE account_id = :1", [account_id])
            if not accounts:
                raise InvalidAccountException("Account not found.")
            db.execute_query("UPDATE Accounts SET balance = balance + :1 WHERE account_id = :2", [amount, account_id], commit=True)
            db.execute_query("INSERT INTO Transactions (account_id, amount, transaction_type, description, status) VALUES (:1, :2, :3, :4, :5)",
                             [account_id, amount, "Deposit", description, "Completed"], commit=True)
        return True

    @staticmethod
    def process_withdrawal(account_id: int, amount: float, description: str = "Withdrawal"):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
            
        if db.use_oracle:
            status = db.execute_procedure("PROCESS_WITHDRAWAL", [account_id, amount, description])
            if status != 'SUCCESS':
                if 'Insufficient funds' in status:
                    raise InsufficientFundsException(status)
                raise Exception(status)
        else:
            # Mock DB: check balance then deduct
            accounts = db.execute_query("SELECT * FROM Accounts WHERE account_id = :1", [account_id])
            if not accounts:
                raise InvalidAccountException("Account not found.")
            if accounts[0]['balance'] < amount:
                raise InsufficientFundsException("Insufficient funds.")
            db.execute_query("UPDATE Accounts SET balance = balance - :1 WHERE account_id = :2", [amount, account_id], commit=True)
            db.execute_query("INSERT INTO Transactions (account_id, amount, transaction_type, description, status) VALUES (:1, :2, :3, :4, :5)",
                             [account_id, amount, "Withdrawal", description, "Completed"], commit=True)
        return True
            
    @staticmethod
    def process_transfer(sender_account_id: int, receiver_account_id: int, amount: float, description: str = "Funds Transfer"):
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")
        if sender_account_id == receiver_account_id:
            raise ValueError("Cannot transfer to the same account.")
            
        if db.use_oracle:
            status = db.execute_procedure("PROCESS_TRANSFER", [sender_account_id, receiver_account_id, amount, description])
            if status != 'SUCCESS':
                if 'Insufficient funds' in status:
                    raise InsufficientFundsException(status)
                raise Exception(status)
        else:
            # Mock DB: validate, deduct sender, credit receiver, log both
            sender = db.execute_query("SELECT * FROM Accounts WHERE account_id = :1", [sender_account_id])
            if not sender:
                raise InvalidAccountException("Sender account not found.")
            if sender[0]['balance'] < amount:
                raise InsufficientFundsException("Insufficient funds.")
            receiver = db.execute_query("SELECT * FROM Accounts WHERE account_id = :1", [receiver_account_id])
            if not receiver:
                raise InvalidAccountException("Receiver account not found.")
            
            db.execute_query("UPDATE Accounts SET balance = balance - :1 WHERE account_id = :2", [amount, sender_account_id], commit=True)
            db.execute_query("UPDATE Accounts SET balance = balance + :1 WHERE account_id = :2", [amount, receiver_account_id], commit=True)
            db.execute_query("INSERT INTO Transactions (account_id, amount, transaction_type, description, status) VALUES (:1, :2, :3, :4, :5)",
                             [sender_account_id, amount, "Transfer_Out", description, "Completed"], commit=True)
            db.execute_query("INSERT INTO Transactions (account_id, amount, transaction_type, description, status) VALUES (:1, :2, :3, :4, :5)",
                             [receiver_account_id, amount, "Transfer_In", description, "Completed"], commit=True)
        return True

from datetime import datetime

class Transaction:
    """Represents a transaction record in the application logic."""
    def __init__(self, transaction_id: int, account_id: int, amount: float, tx_type: str, status: str, description: str, created_at: datetime):
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.amount = amount
        self.tx_type = tx_type
        self.status = status
        self.description = description
        self.created_at = created_at

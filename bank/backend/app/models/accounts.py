from .base_account import Account
from .exceptions import InsufficientFundsException

class SavingsAccount(Account):
    """Savings account implementing specific withdrawal rules and interest."""
    
    def __init__(self, account_id: int, account_number: str, balance: float, interest_rate: float = 0.05):
        super().__init__(account_id, account_number, balance)
        self.interest_rate = interest_rate

    def withdraw(self, amount: float) -> None:
        """Polymorphic implementation of withdraw for Savings."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.balance < amount:
            raise InsufficientFundsException("Insufficient funds in Savings Account.")
        self._set_balance(self.balance - amount)

    def apply_interest(self) -> None:
        interest = self.balance * self.interest_rate
        self.deposit(interest)

class CurrentAccount(Account):
    """Current (Checking) account implementing specific withdrawal rules including overdraft."""
    
    def __init__(self, account_id: int, account_number: str, balance: float, overdraft_limit: float = 50000.0):
        super().__init__(account_id, account_number, balance)
        self.overdraft_limit = overdraft_limit

    def withdraw(self, amount: float) -> None:
        """Polymorphic implementation of withdraw allowing overdrafts."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        # Check against balance + overdraft limit
        if (self.balance + self.overdraft_limit) < amount:
            raise InsufficientFundsException("Overdraft limit exceeded.")
        self._set_balance(self.balance - amount)

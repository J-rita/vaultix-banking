class BankingException(Exception):
    """Base exception for all banking operations."""
    pass

class InsufficientFundsException(BankingException):
    """Raised when an account does not have enough funds."""
    pass

class InvalidAccountException(BankingException):
    """Raised when an account is not found or is invalid."""
    pass

class DatabaseConnectionException(BankingException):
    """Raised when the database connection fails."""
    pass

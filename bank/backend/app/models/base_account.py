from abc import ABC, abstractmethod
from .exceptions import InsufficientFundsException

class Account(ABC):
    """Abstract base class representing a generic bank account."""
    
    def __init__(self, account_id: int, account_number: str, balance: float):
        # Encapsulation: protect properties
        self._account_id = account_id
        self.__account_number = account_number
        self.__balance = balance
        
    @property
    def account_id(self) -> int:
        return self._account_id

    @property
    def account_number(self) -> str:
        return self.__account_number

    @property
    def balance(self) -> float:
        return self.__balance

    def deposit(self, amount: float) -> None:
        if amount > 0:
            self.__balance += amount
        else:
            raise ValueError("Deposit amount must be positive.")

    @abstractmethod
    def withdraw(self, amount: float) -> None:
        """Abstract method to withdraw funds, must be overridden by subclasses."""
        pass

    def get_balance(self) -> float:
        return self.__balance
        
    # Protected method to allow subclasses to update balance after validation
    def _set_balance(self, amount: float) -> None:
        self.__balance = amount

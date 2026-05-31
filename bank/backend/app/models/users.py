from abc import ABC

class User(ABC):
    """Abstract user class demonstrating common properties."""
    def __init__(self, user_id: int, username: str, email: str, first_name: str, last_name: str):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Customer(User):
    """Concrete class representing a banking customer."""
    def __init__(self, user_id: int, username: str, email: str, first_name: str, last_name: str, status: str = 'Active'):
        super().__init__(user_id, username, email, first_name, last_name)
        self.status = status
        self.accounts = []

    def add_account(self, account):
        self.accounts.append(account)


class BankStaff(User):
    """Concrete class representing a bank employee/admin."""
    def __init__(self, user_id: int, username: str, email: str, first_name: str, last_name: str, role: str):
        super().__init__(user_id, username, email, first_name, last_name)
        self.role = role

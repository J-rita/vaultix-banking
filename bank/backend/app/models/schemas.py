from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserResponse(UserBase):
    user_id: int
    role: str
    status: str
    created_at: str

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AccountBase(BaseModel):
    account_type: str
    balance: float = 0.0

class AccountResponse(AccountBase):
    account_id: int
    user_id: int
    account_number: str
    status: str

class TransactionBase(BaseModel):
    amount: float
    description: Optional[str] = None

class TransferRequest(TransactionBase):
    receiver_account_number: str
    sender_account_id: int

class TransactionResponse(TransactionBase):
    tx_id: int
    sender_account_id: int
    receiver_account_id: Optional[int]
    tx_type: str
    created_at: str

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .auth.security_fastapi import create_access_token, verify_password, get_password_hash
from .models.schemas import UserCreate, UserResponse, LoginRequest, Token
from .database import execute_query

app = FastAPI(title="KAY BANK API", version="2.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTH ROUTES ---
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    # Check if user exists
    existing = execute_query("SELECT * FROM USERS WHERE USERNAME = :1 OR EMAIL = :2", [user.username, user.email])
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    hashed_password = get_password_hash(user.password)
    execute_query(
        "INSERT INTO USERS (USERNAME, EMAIL, PASSWORD_HASH, FIRST_NAME, LAST_NAME) VALUES (:1, :2, :3, :4, :5)",
        [user.username, user.email, hashed_password, user.first_name, user.last_name],
        commit=True
    )
    
    # Get created user
    new_user = execute_query("SELECT * FROM USERS WHERE USERNAME = :1", [user.username])[0]
    return new_user

@app.post("/api/auth/login", response_model=Token)
async def login(login_data: LoginRequest):
    users = execute_query("SELECT * FROM USERS WHERE USERNAME = :1", [login_data.username])
    if not users or not verify_password(login_data.password, users[0]["PASSWORD_HASH"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": users[0]["USERNAME"], "role": users[0]["ROLE"], "uid": users[0]["USER_ID"]})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ACCOUNTS ROUTES ---
@app.get("/api/accounts/my-accounts")
async def get_my_accounts(user: dict = Depends(get_current_user)):
    accounts = execute_query("SELECT * FROM ACCOUNTS WHERE USER_ID = :1", [user["uid"]])
    return accounts

# --- TRANSACTIONS ROUTES ---
@app.get("/api/transactions/history/{account_id}")
async def get_history(account_id: int, user: dict = Depends(get_current_user)):
    acc = execute_query("SELECT * FROM ACCOUNTS WHERE ACCOUNT_ID = :1 AND USER_ID = :2", [account_id, user["uid"]])
    if not acc:
        raise HTTPException(status_code=403, detail="Account not found or access denied")
    history = execute_query("SELECT * FROM TRANSACTIONS WHERE SENDER_ACCOUNT_ID = :1 OR RECEIVER_ACCOUNT_ID = :1", [account_id])
    return history

@app.post("/api/transactions/transfer")
async def transfer_funds(data: dict, user: dict = Depends(get_current_user)):
    # data: { sender_id, receiver_acc_num, amount, description }
    # 1. Validate sender
    sender = execute_query("SELECT * FROM ACCOUNTS WHERE ACCOUNT_ID = :1 AND USER_ID = :2", [data["sender_id"], user["uid"]])
    if not sender or sender[0]["BALANCE"] < data["amount"]:
        raise HTTPException(status_code=400, detail="Insufficient funds or invalid account")
    
    # 2. Find receiver
    receiver = execute_query("SELECT * FROM ACCOUNTS WHERE ACCOUNT_NUMBER = :1", [data["receiver_acc_num"]])
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver account not found")
    
    # 3. Perform transfer (Atomic)
    execute_query("UPDATE ACCOUNTS SET BALANCE = BALANCE - :1 WHERE ACCOUNT_ID = :2", [data["amount"], data["sender_id"]], commit=True)
    execute_query("UPDATE ACCOUNTS SET BALANCE = BALANCE + :1 WHERE ACCOUNT_ID = :2", [data["amount"], receiver[0]["ACCOUNT_ID"]], commit=True)
    execute_query("INSERT INTO TRANSACTIONS (SENDER_ACCOUNT_ID, RECEIVER_ACCOUNT_ID, AMOUNT, TX_TYPE, DESCRIPTION) VALUES (:1, :2, :3, 'Transfer', :4)",
                  [data["sender_id"], receiver[0]["ACCOUNT_ID"], data["amount"], data.get("description", "")], commit=True)
    
    return {"status": "success"}

# --- ADMIN ROUTES ---
@app.get("/api/admin/users")
async def get_all_users(user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return execute_query("SELECT * FROM USERS")

@app.post("/api/admin/flag-user/{user_id}")
async def flag_user(user_id: int, user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin only")
    execute_query("UPDATE USERS SET STATUS = 'Flagged' WHERE USER_ID = :1", [user_id], commit=True)
    return {"status": "user flagged"}

# Serving React Build (Placeholder for now)
# app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    # This will be used once the React app is built
    return {"message": "API is running. Frontend build not found yet."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

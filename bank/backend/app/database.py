import os
import json
import datetime
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False

DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "password123")
DB_DSN = os.getenv("DB_DSN", "localhost:1521/xe")
DB_FILE = "db.json"

def init_mock_db():
    defaults = {"USERS": [], "ACCOUNTS": [], "TRANSACTIONS": [], "LOANS": [], "NOTIFICATIONS": [], "AUDIT_LOGS": []}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
                for key in defaults:
                    if key not in data: data[key] = defaults[key]
                return data
            except: return defaults
    return defaults

MOCK_DB = init_mock_db()

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(MOCK_DB, f, indent=4)

def execute_query(query, params=None, commit=False):
    if ORACLE_AVAILABLE and os.getenv("USE_ORACLE") == "true":
        return _execute_oracle(query, params, commit)
    else:
        return _execute_simulator(query, params, commit)

def _execute_oracle(query, params, commit):
    try:
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        if commit:
            conn.commit()
            return True
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return results
        return True
    except Exception as e:
        print(f"Oracle Error: {e}")
        return False

def _execute_simulator(query, params, commit):
    q = query.upper().strip()
    p = params or []

    # --- SELECT FROM USERS ---
    if "SELECT" in q and "FROM USERS" in q:
        if "WHERE USERNAME =" in q or "WHERE EMAIL =" in q:
            val = p[0].lower()
            return [u for u in MOCK_DB["USERS"] if u["USERNAME"].lower() == val or u["EMAIL"].lower() == val]
        if "WHERE USER_ID =" in q:
            return [u for u in MOCK_DB["USERS"] if str(u["USER_ID"]) == str(p[0])]
        return MOCK_DB["USERS"]

    # --- SELECT FROM ACCOUNTS ---
    if "SELECT" in q and "FROM ACCOUNTS" in q:
        if "WHERE ACCOUNT_ID =" in q:
            return [a for a in MOCK_DB["ACCOUNTS"] if str(a["ACCOUNT_ID"]) == str(p[0])]
        if "WHERE ACCOUNT_NUMBER =" in q:
            return [a for a in MOCK_DB["ACCOUNTS"] if str(a.get("ACCOUNT_NUMBER", "")).strip() == str(p[0]).strip()]
        if "WHERE USER_ID =" in q:
            return [a for a in MOCK_DB["ACCOUNTS"] if str(a["USER_ID"]) == str(p[0])]
        return MOCK_DB["ACCOUNTS"]

    # --- UPDATE ACCOUNTS (Balance) ---
    if "UPDATE ACCOUNTS SET BALANCE =" in q:
        # Simple parser for "UPDATE ACCOUNTS SET BALANCE = BALANCE + :1 WHERE ACCOUNT_ID = :2"
        # and "UPDATE ACCOUNTS SET BALANCE = BALANCE - :1 WHERE ACCOUNT_ID = :2"
        amount = float(p[0])
        acc_id = str(p[1])
        for acc in MOCK_DB["ACCOUNTS"]:
            if str(acc["ACCOUNT_ID"]) == acc_id:
                if "BALANCE +" in q: acc["BALANCE"] += amount
                elif "BALANCE -" in q: acc["BALANCE"] -= amount
                else: acc["BALANCE"] = amount # Direct set
        if commit: save_db()
        return True

    # --- INSERT INTO USERS ---
    if "INSERT INTO USERS" in q:
        user_id = len(MOCK_DB["USERS"]) + 1
        MOCK_DB["USERS"].append({
            "USER_ID": user_id, "USERNAME": p[0], "EMAIL": p[1], "PASSWORD_HASH": p[2],
            "FIRST_NAME": p[3], "LAST_NAME": p[4], "ROLE": "Customer", "STATUS": "Active",
            "CREATED_AT": datetime.datetime.now().isoformat()
        })
        # Create default accounts
        MOCK_DB["ACCOUNTS"].append({"ACCOUNT_ID": len(MOCK_DB["ACCOUNTS"]) + 1, "USER_ID": user_id, "ACCOUNT_NUMBER": f"214{user_id:07d}", "ACCOUNT_TYPE": "Savings", "BALANCE": 0.0, "STATUS": "Active"})
        MOCK_DB["ACCOUNTS"].append({"ACCOUNT_ID": len(MOCK_DB["ACCOUNTS"]) + 1, "USER_ID": user_id, "ACCOUNT_NUMBER": f"224{user_id:07d}", "ACCOUNT_TYPE": "Current", "BALANCE": 0.0, "STATUS": "Active"})
        if commit: save_db()
        return True

    # --- INSERT INTO TRANSACTIONS ---
    if "INSERT INTO TRANSACTIONS" in q:
        # Params: [sender_id, receiver_id, amount, type, description]
        MOCK_DB["TRANSACTIONS"].append({
            "TRANSACTION_ID": len(MOCK_DB["TRANSACTIONS"]) + 1,
            "SENDER_ACCOUNT_ID": p[0],
            "RECEIVER_ACCOUNT_ID": p[1],
            "AMOUNT": float(p[2]),
            "TRANSACTION_TYPE": p[3],
            "DESCRIPTION": p[4],
            "CREATED_AT": datetime.datetime.now().isoformat()
        })
        if commit: save_db()
        return True

    # --- SELECT FROM TRANSACTIONS ---
    if "SELECT * FROM TRANSACTIONS" in q:
        if "WHERE SENDER_ACCOUNT_ID =" in q or "WHERE RECEIVER_ACCOUNT_ID =" in q:
            aid = str(p[0])
            return [t for t in MOCK_DB["TRANSACTIONS"] if str(t["SENDER_ACCOUNT_ID"]) == aid or str(t["RECEIVER_ACCOUNT_ID"]) == aid]
        return MOCK_DB["TRANSACTIONS"]

    # --- INSERT INTO LOANS ---
    if "INSERT INTO LOANS" in q:
        # Params: [user_id, amount, interest_rate, term_months, status]
        MOCK_DB["LOANS"].append({
            "LOAN_ID": len(MOCK_DB["LOANS"]) + 1,
            "USER_ID": p[0],
            "AMOUNT": float(p[1]),
            "INTEREST_RATE": float(p[2]),
            "TERM_MONTHS": int(p[3]),
            "STATUS": p[4],
            "CREATED_AT": datetime.datetime.now().isoformat()
        })
        if commit: save_db()
        return True

    # --- SELECT FROM LOANS ---
    if "SELECT" in q and "FROM LOANS" in q:
        if "WHERE USER_ID =" in q:
            return [l for l in MOCK_DB["LOANS"] if str(l["USER_ID"]) == str(p[0])]
        return MOCK_DB["LOANS"]

    # --- UPDATE USERS ---
    if "UPDATE USERS" in q:
        # Expected params: [first_name, last_name, phone, address, avatar, username]
        for u in MOCK_DB["USERS"]:
            if u["USERNAME"] == p[5]:
                u["FIRST_NAME"] = p[0]
                u["LAST_NAME"] = p[1]
                u["PHONE"] = p[2]
                u["ADDRESS"] = p[3]
                u["AVATAR"] = p[4]
                break
        if commit: save_db()
        return True

    if commit:
        save_db()
        return True

    return []

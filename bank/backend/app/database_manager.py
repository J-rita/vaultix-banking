import os
import json
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False

from .models.exceptions import DatabaseConnectionException

class DatabaseManager:
    """
    Singleton Database Manager class for enterprise database connection.
    Implements the Singleton pattern to maintain a single connection state.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.db_user = os.getenv("DB_USER", "admin")
        self.db_pass = os.getenv("DB_PASS", "password123")
        self.db_dsn = os.getenv("DB_DSN", "localhost:1521/xe")
        self.use_oracle = ORACLE_AVAILABLE and os.getenv("USE_ORACLE") == "true"
        
        if not self.use_oracle:
            print("WARNING: Oracle not available or USE_ORACLE not true. Using fallback JSON simulation.")
            self.db_file = "db.json"
            self.mock_db = self._init_mock_db()

    def _init_mock_db(self):
        defaults = {"Customers": [], "BankStaff": [], "Accounts": [], "Transactions": [], "Transfers": [], "AuditLogs": [], "Loans": []}
        if os.path.exists(self.db_file):
            with open(self.db_file, "r") as f:
                try:
                    data = json.load(f)
                    for key in defaults:
                        if key not in data: data[key] = defaults[key]
                    return data
                except: return defaults
        return defaults

    def save_mock_db(self):
        if not self.use_oracle:
            with open(self.db_file, "w") as f:
                json.dump(self.mock_db, f, indent=4)

    def execute_query(self, query: str, params: list = None, commit: bool = False):
        if self.use_oracle:
            return self._execute_oracle(query, params, commit)
        else:
            return self._execute_simulator(query, params, commit)

    def execute_procedure(self, proc_name: str, params: list):
        if self.use_oracle:
            try:
                conn = oracledb.connect(user=self.db_user, password=self.db_pass, dsn=self.db_dsn)
                cursor = conn.cursor()
                
                # Add OUT parameter dynamically
                out_status = cursor.var(str)
                params.append(out_status)
                
                cursor.callproc(proc_name, params)
                status = out_status.getvalue()
                
                cursor.close()
                conn.close()
                return status
            except Exception as e:
                raise DatabaseConnectionException(f"Oracle Procedure Error: {e}")
        else:
            return "SUCCESS" # Simulator fallback

    def _execute_oracle(self, query: str, params: list, commit: bool):
        try:
            conn = oracledb.connect(user=self.db_user, password=self.db_pass, dsn=self.db_dsn)
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            if commit:
                conn.commit()
                return True
            if cursor.description:
                columns = [col[0].lower() for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
                conn.close()
                return results
            return True
        except Exception as e:
            raise DatabaseConnectionException(f"Oracle Error: {e}")

    def _execute_simulator(self, query: str, params: list, commit: bool):
        # Fallback simulator logic
        q = query.upper().strip()
        p = params or []
        
        if "SELECT" in q and "FROM CUSTOMERS" in q:
             if "WHERE USERNAME =" in q and "OR EMAIL =" in q:
                 # Registration duplicate check: username OR email
                 return [c for c in self.mock_db.get("Customers", []) if c.get("username", "").lower() == str(p[0]).lower() or c.get("email", "").lower() == str(p[1]).lower()]
             if "WHERE USERNAME =" in q:
                 return [c for c in self.mock_db.get("Customers", []) if c.get("username", "").lower() == str(p[0]).lower()]
             if "WHERE CUSTOMER_ID =" in q:
                 return [c for c in self.mock_db.get("Customers", []) if str(c.get("customer_id")) == str(p[0])]
             return self.mock_db.get("Customers", [])
             
        if "SELECT" in q and "FROM BANKSTAFF" in q:
             if "WHERE USERNAME =" in q:
                 return [c for c in self.mock_db.get("BankStaff", []) if c.get("username").lower() == str(p[0]).lower()]
             return self.mock_db.get("BankStaff", [])

        if "SELECT" in q and "FROM ACCOUNTS" in q:
             if "WHERE CUSTOMER_ID =" in q:
                 return [a for a in self.mock_db.get("Accounts", []) if str(a.get("customer_id")) == str(p[0])]
             if "WHERE ACCOUNT_NUMBER =" in q:
                 return [a for a in self.mock_db.get("Accounts", []) if str(a.get("account_number")) == str(p[0])]
             if "WHERE ACCOUNT_ID =" in q:
                 return [a for a in self.mock_db.get("Accounts", []) if str(a.get("account_id")) == str(p[0])]
             return self.mock_db.get("Accounts", [])

        if "INSERT INTO CUSTOMERS" in q:
            # Params: [username, email, password_hash, first_name, last_name]
            cust_id = len(self.mock_db.get("Customers", [])) + 1
            self.mock_db.setdefault("Customers", []).append({
                "customer_id": cust_id,
                "username": p[0], "email": p[1], "password_hash": p[2],
                "first_name": p[3], "last_name": p[4],
                "status": "Active", "created_at": __import__('datetime').datetime.now().isoformat()
            })
            # Auto-create Savings and Current accounts
            acc_list = self.mock_db.setdefault("Accounts", [])
            acc_list.append({"account_id": len(acc_list)+1, "customer_id": cust_id, "account_number": f"214{cust_id:07d}", "account_type": "Savings", "balance": 0.0, "status": "Active", "interest_rate": 0.05, "overdraft_limit": 0.0})
            acc_list.append({"account_id": len(acc_list)+1, "customer_id": cust_id, "account_number": f"224{cust_id:07d}", "account_type": "Current", "balance": 0.0, "status": "Active", "interest_rate": 0.0, "overdraft_limit": 0.0})
            if commit: self.save_mock_db()
            return True

        if "SELECT" in q and "FROM TRANSACTIONS" in q:
            tx_list = self.mock_db.get("Transactions", [])
            if "WHERE ACCOUNT_ID =" in q:
                return [t for t in tx_list if str(t.get("account_id")) == str(p[0])]
            return sorted(tx_list, key=lambda x: x.get("created_at", ""), reverse=True)

        if "INSERT INTO TRANSACTIONS" in q:
            # Params: [account_id, amount, transaction_type, description, status]
            import datetime
            tx_list = self.mock_db.setdefault("Transactions", [])
            tx_list.append({
                "transaction_id": len(tx_list) + 1,
                "account_id": p[0],
                "amount": float(p[1]),
                "transaction_type": p[2],
                "description": p[3],
                "status": p[4] if len(p) > 4 else "Completed",
                "created_at": datetime.datetime.now().isoformat()
            })
            if commit: self.save_mock_db()
            return True

        if "UPDATE ACCOUNTS SET BALANCE" in q:
            amount = float(p[0])
            acc_id = str(p[1])
            for acc in self.mock_db.get("Accounts", []):
                if str(acc.get("account_id")) == acc_id:
                    if "BALANCE + :1" in q or "BALANCE +:1" in q:
                        acc["balance"] = round(acc["balance"] + amount, 2)
                    elif "BALANCE - :1" in q or "BALANCE -:1" in q:
                        acc["balance"] = round(acc["balance"] - amount, 2)
                    else:
                        acc["balance"] = round(amount, 2)
                    break
            if commit: self.save_mock_db()
            return True

        if "UPDATE CUSTOMERS SET PASSWORD_HASH" in q:
            new_hash, username = p[0], p[1]
            for c in self.mock_db.get("Customers", []):
                if c.get("username", "").lower() == username.lower():
                    c["password_hash"] = new_hash
                    break
            if commit: self.save_mock_db()
            return True

        if "SELECT" in q and "FROM AUDITLOGS" in q:
            return self.mock_db.get("AuditLogs", [])

        if commit:
            self.save_mock_db()
            return True

        return []

# Expose singleton instance
db = DatabaseManager()

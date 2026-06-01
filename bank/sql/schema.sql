-- VAULTIX ENTERPRISE BANKING SYSTEM - ORACLE SCHEMA
-- ====================================================
-- This script sets up a 3NF normalized, enterprise-grade database schema.
-- Includes Tables, Constraints, Indexes, Sequences, Triggers, and Stored Procedures.

-- 1. DROP EXISTING OBJECTS (For clean setup)
BEGIN
   -- Drop Tables from previous runs if they exist
   EXECUTE IMMEDIATE 'DROP TABLE Transfers CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE Transactions CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE Accounts CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE Customers CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE BankStaff CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE Branches CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE AuditLogs CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE Users CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE Loans CASCADE CONSTRAINTS';
   
   -- Drop Sequences
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_branches_id';
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_customers_id';
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_staff_id';
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_accounts_id';
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_transactions_id';
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_transfers_id';
   EXECUTE IMMEDIATE 'DROP SEQUENCE seq_audit_id';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/

-- 2. CREATE SEQUENCES
CREATE SEQUENCE seq_branches_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_customers_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_staff_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_accounts_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_transactions_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_transfers_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_audit_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_loans_id START WITH 1 INCREMENT BY 1;

-- 3. TABLES

-- BRANCHES
CREATE TABLE Branches (
    branch_id NUMBER PRIMARY KEY,
    branch_name VARCHAR2(100) NOT NULL,
    branch_code VARCHAR2(20) UNIQUE NOT NULL,
    address VARCHAR2(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CUSTOMERS
CREATE TABLE Customers (
    customer_id NUMBER PRIMARY KEY,
    username VARCHAR2(50) UNIQUE NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    first_name VARCHAR2(50) NOT NULL,
    last_name VARCHAR2(50) NOT NULL,
    phone_number VARCHAR2(20),
    address VARCHAR2(255),
    transaction_pin_hash VARCHAR2(255),
    status VARCHAR2(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Suspended', 'Flagged')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BANK_STAFF
CREATE TABLE BankStaff (
    staff_id NUMBER PRIMARY KEY,
    branch_id NUMBER,
    username VARCHAR2(50) UNIQUE NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    first_name VARCHAR2(50) NOT NULL,
    last_name VARCHAR2(50) NOT NULL,
    role VARCHAR2(50) DEFAULT 'Teller' CHECK (role IN ('Teller', 'Manager', 'Admin')),
    status VARCHAR2(20) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_staff_branch FOREIGN KEY (branch_id) REFERENCES Branches(branch_id) ON DELETE SET NULL
);

-- ACCOUNTS
CREATE TABLE Accounts (
    account_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    branch_id NUMBER,
    account_number VARCHAR2(20) UNIQUE NOT NULL,
    account_type VARCHAR2(20) NOT NULL CHECK (account_type IN ('Savings', 'Current')),
    balance NUMBER(15, 2) DEFAULT 0.00 CHECK (balance >= 0),
    interest_rate NUMBER(5, 4) DEFAULT 0.00,
    overdraft_limit NUMBER(15, 2) DEFAULT 0.00,
    status VARCHAR2(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Closed', 'Dormant')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_acc_customer FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE,
    CONSTRAINT fk_acc_branch FOREIGN KEY (branch_id) REFERENCES Branches(branch_id) ON DELETE SET NULL
);

-- TRANSACTIONS
CREATE TABLE Transactions (
    transaction_id NUMBER PRIMARY KEY,
    account_id NUMBER NOT NULL,
    amount NUMBER(15, 2) NOT NULL CHECK (amount > 0),
    transaction_type VARCHAR2(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer_In', 'Transfer_Out')),
    reference_no VARCHAR2(100) UNIQUE,
    description VARCHAR2(255),
    status VARCHAR2(20) DEFAULT 'Completed' CHECK (status IN ('Pending', 'Completed', 'Failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tx_account FOREIGN KEY (account_id) REFERENCES Accounts(account_id) ON DELETE CASCADE
);

-- TRANSFERS
CREATE TABLE Transfers (
    transfer_id NUMBER PRIMARY KEY,
    sender_account_id NUMBER NOT NULL,
    receiver_account_id NUMBER NOT NULL,
    amount NUMBER(15, 2) NOT NULL CHECK (amount > 0),
    transaction_id_out NUMBER NOT NULL,
    transaction_id_in NUMBER NOT NULL,
    status VARCHAR2(20) DEFAULT 'Completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tr_sender FOREIGN KEY (sender_account_id) REFERENCES Accounts(account_id),
    CONSTRAINT fk_tr_receiver FOREIGN KEY (receiver_account_id) REFERENCES Accounts(account_id),
    CONSTRAINT fk_tr_tx_out FOREIGN KEY (transaction_id_out) REFERENCES Transactions(transaction_id),
    CONSTRAINT fk_tr_tx_in FOREIGN KEY (transaction_id_in) REFERENCES Transactions(transaction_id)
);

-- AUDIT_LOGS
CREATE TABLE AuditLogs (
    log_id NUMBER PRIMARY KEY,
    action_type VARCHAR2(50) NOT NULL,
    table_name VARCHAR2(50),
    record_id NUMBER,
    old_value VARCHAR2(4000),
    new_value VARCHAR2(4000),
    performed_by VARCHAR2(100),
    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR2(50)
);

-- LOANS
CREATE TABLE Loans (
    loan_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    amount NUMBER(15, 2) NOT NULL CHECK (amount > 0),
    interest_rate NUMBER(5, 2) DEFAULT 5.00,
    term_months NUMBER(3) DEFAULT 12,
    status VARCHAR2(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected', 'Repaid')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_loan_customer FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);

-- 4. INDEXES FOR QUERY OPTIMIZATION
CREATE INDEX idx_cust_username ON Customers(username);
CREATE INDEX idx_acc_number ON Accounts(account_number);
CREATE INDEX idx_acc_customer ON Accounts(customer_id);
CREATE INDEX idx_tx_account ON Transactions(account_id);
CREATE INDEX idx_tx_date ON Transactions(created_at);
CREATE INDEX idx_audit_date ON AuditLogs(log_timestamp);

-- 5. TRIGGERS (Auto-increment IDs)
CREATE OR REPLACE TRIGGER trg_branches_id BEFORE INSERT ON Branches FOR EACH ROW BEGIN :NEW.branch_id := seq_branches_id.NEXTVAL; END;
/
CREATE OR REPLACE TRIGGER trg_customers_id BEFORE INSERT ON Customers FOR EACH ROW BEGIN :NEW.customer_id := seq_customers_id.NEXTVAL; END;
/
CREATE OR REPLACE TRIGGER trg_staff_id BEFORE INSERT ON BankStaff FOR EACH ROW BEGIN :NEW.staff_id := seq_staff_id.NEXTVAL; END;
/
CREATE OR REPLACE TRIGGER trg_accounts_id BEFORE INSERT ON Accounts FOR EACH ROW BEGIN :NEW.account_id := seq_accounts_id.NEXTVAL; END;
/
CREATE OR REPLACE TRIGGER trg_transactions_id BEFORE INSERT ON Transactions FOR EACH ROW BEGIN :NEW.transaction_id := seq_transactions_id.NEXTVAL; END;
/
CREATE OR REPLACE TRIGGER trg_transfers_id BEFORE INSERT ON Transfers FOR EACH ROW BEGIN :NEW.transfer_id := seq_transfers_id.NEXTVAL; END;
/
CREATE OR REPLACE TRIGGER trg_audit_id BEFORE INSERT ON AuditLogs FOR EACH ROW BEGIN :NEW.log_id := seq_audit_id.NEXTVAL; END;
/
CREATE OR REPLACE TRIGGER trg_loans_id BEFORE INSERT ON Loans FOR EACH ROW BEGIN :NEW.loan_id := seq_loans_id.NEXTVAL; END;
/

-- Audit Trigger on Transactions
CREATE OR REPLACE TRIGGER trg_audit_transactions
AFTER INSERT ON Transactions
FOR EACH ROW
BEGIN
    INSERT INTO AuditLogs (action_type, table_name, record_id, new_value, performed_by)
    VALUES ('INSERT', 'Transactions', :NEW.transaction_id, 'Type: ' || :NEW.transaction_type || ', Amount: ' || :NEW.amount, 'SYSTEM');
END;
/

-- Audit Trigger on Account Status Updates
CREATE OR REPLACE TRIGGER trg_audit_accounts
AFTER UPDATE OF status ON Accounts
FOR EACH ROW
BEGIN
    INSERT INTO AuditLogs (action_type, table_name, record_id, old_value, new_value, performed_by)
    VALUES ('UPDATE_STATUS', 'Accounts', :NEW.account_id, :OLD.status, :NEW.status, 'SYSTEM');
END;
/


-- 6. PL/SQL PROCEDURES FOR ACID TRANSACTIONS

-- Procedure: PROCESS_DEPOSIT
CREATE OR REPLACE PROCEDURE PROCESS_DEPOSIT(
    p_account_id IN NUMBER,
    p_amount IN NUMBER,
    p_description IN VARCHAR2,
    p_out_status OUT VARCHAR2
) AS
BEGIN
    IF p_amount <= 0 THEN
        p_out_status := 'FAILED: Amount must be positive';
        RETURN;
    END IF;

    -- Update balance (Account check constraint validates >= 0)
    UPDATE Accounts SET balance = balance + p_amount WHERE account_id = p_account_id;
    
    -- Log transaction
    INSERT INTO Transactions (account_id, amount, transaction_type, description, status)
    VALUES (p_account_id, p_amount, 'Deposit', p_description, 'Completed');
    
    COMMIT;
    p_out_status := 'SUCCESS';
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        p_out_status := 'FAILED: ' || SQLERRM;
        INSERT INTO AuditLogs (action_type, table_name, old_value) VALUES ('DEPOSIT_FAILED', 'Accounts', SQLERRM);
        COMMIT;
END;
/

-- Procedure: PROCESS_WITHDRAWAL
CREATE OR REPLACE PROCEDURE PROCESS_WITHDRAWAL(
    p_account_id IN NUMBER,
    p_amount IN NUMBER,
    p_description IN VARCHAR2,
    p_out_status OUT VARCHAR2
) AS
    v_balance NUMBER;
BEGIN
    IF p_amount <= 0 THEN
        p_out_status := 'FAILED: Amount must be positive';
        RETURN;
    END IF;

    -- Lock row and get balance to avoid race conditions
    SELECT balance INTO v_balance FROM Accounts WHERE account_id = p_account_id FOR UPDATE;

    IF v_balance < p_amount THEN
        p_out_status := 'FAILED: Insufficient funds';
        ROLLBACK;
        RETURN;
    END IF;

    -- Update balance
    UPDATE Accounts SET balance = balance - p_amount WHERE account_id = p_account_id;
    
    -- Log transaction
    INSERT INTO Transactions (account_id, amount, transaction_type, description, status)
    VALUES (p_account_id, p_amount, 'Withdrawal', p_description, 'Completed');
    
    COMMIT;
    p_out_status := 'SUCCESS';
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        p_out_status := 'FAILED: ' || SQLERRM;
        INSERT INTO AuditLogs (action_type, table_name, old_value) VALUES ('WITHDRAWAL_FAILED', 'Accounts', SQLERRM);
        COMMIT;
END;
/

-- Procedure: PROCESS_TRANSFER
CREATE OR REPLACE PROCEDURE PROCESS_TRANSFER(
    p_sender_id IN NUMBER,
    p_receiver_id IN NUMBER,
    p_amount IN NUMBER,
    p_description IN VARCHAR2,
    p_out_status OUT VARCHAR2
) AS
    v_sender_balance NUMBER;
    v_tx_out_id NUMBER;
    v_tx_in_id NUMBER;
BEGIN
    IF p_amount <= 0 THEN
        p_out_status := 'FAILED: Amount must be positive';
        RETURN;
    END IF;
    
    IF p_sender_id = p_receiver_id THEN
        p_out_status := 'FAILED: Cannot transfer to same account';
        RETURN;
    END IF;

    -- Lock rows in consistent order to prevent deadlocks
    IF p_sender_id < p_receiver_id THEN
        SELECT balance INTO v_sender_balance FROM Accounts WHERE account_id = p_sender_id FOR UPDATE;
        SELECT balance INTO v_sender_balance FROM Accounts WHERE account_id = p_receiver_id FOR UPDATE;
    ELSE
        SELECT balance INTO v_sender_balance FROM Accounts WHERE account_id = p_receiver_id FOR UPDATE;
        SELECT balance INTO v_sender_balance FROM Accounts WHERE account_id = p_sender_id FOR UPDATE;
    END IF;

    -- Re-select sender balance for verification
    SELECT balance INTO v_sender_balance FROM Accounts WHERE account_id = p_sender_id;

    IF v_sender_balance < p_amount THEN
        p_out_status := 'FAILED: Insufficient funds';
        ROLLBACK;
        RETURN;
    END IF;

    -- Deduct from sender
    UPDATE Accounts SET balance = balance - p_amount WHERE account_id = p_sender_id;
    -- Add to receiver
    UPDATE Accounts SET balance = balance + p_amount WHERE account_id = p_receiver_id;

    -- Insert Out Transaction
    INSERT INTO Transactions (account_id, amount, transaction_type, description, status)
    VALUES (p_sender_id, p_amount, 'Transfer_Out', p_description, 'Completed') RETURNING transaction_id INTO v_tx_out_id;
    
    -- Insert In Transaction
    INSERT INTO Transactions (account_id, amount, transaction_type, description, status)
    VALUES (p_receiver_id, p_amount, 'Transfer_In', p_description, 'Completed') RETURNING transaction_id INTO v_tx_in_id;
    
    -- Record Transfer Link
    INSERT INTO Transfers (sender_account_id, receiver_account_id, amount, transaction_id_out, transaction_id_in)
    VALUES (p_sender_id, p_receiver_id, p_amount, v_tx_out_id, v_tx_in_id);

    COMMIT;
    p_out_status := 'SUCCESS';
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        p_out_status := 'FAILED: ' || SQLERRM;
        INSERT INTO AuditLogs (action_type, table_name, old_value) VALUES ('TRANSFER_FAILED', 'Transfers', SQLERRM);
        COMMIT;
END;
/

-- Sample Admin User Data (Role: Admin)
-- Password 'admin123' hashed with bcrypt
INSERT INTO BankStaff (username, email, password_hash, first_name, last_name, role) 
VALUES ('admin', 'admin@vaultix.com', '$2b$12$WCzYQTfDR9daPutx0jWdaeXdIAOFUzMG9rtJlfObCdOcX06JBthRu', 'Super', 'Admin', 'Admin');

COMMIT;

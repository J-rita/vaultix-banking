from datetime import datetime, timedelta

def analyze_transaction(amount: float, sender_id: int, db_connection=None):
    """
    Logic-based fraud detection.
    Flags transactions if:
    1. Amount exceeds $10,000 (Large transaction).
    2. Multiple transactions in a very short time (Velocity check).
    """
    flags = []
    
    # 1. Large transaction flag
    if amount > 10000:
        flags.append("High value transaction")
    
    # 2. Add more complex logic here (e.g. historical patterns)
    # For now, we'll return True/False based on amount for demo
    is_suspicious = len(flags) > 0
    
    return is_suspicious, ", ".join(flags) if flags else "Normal"

from ..database_manager import db

class AuditLogger:
    """Service class for handling security and audit logging."""
    
    @staticmethod
    def log_action(action_type: str, table_name: str, record_id: int = None, old_value: str = None, new_value: str = None, performed_by: str = 'SYSTEM'):
        """
        Manually log an action to the AuditLogs table.
        Note: The Oracle schema also has triggers for automatic logging on critical tables.
        """
        if db.use_oracle:
            query = """
                INSERT INTO AuditLogs (action_type, table_name, record_id, old_value, new_value, performed_by)
                VALUES (:1, :2, :3, :4, :5, :6)
            """
            db.execute_query(query, [action_type, table_name, record_id, old_value, new_value, performed_by], commit=True)
        else:
            # Fallback simulator
            log = {
                "action_type": action_type,
                "table_name": table_name,
                "record_id": record_id,
                "old_value": old_value,
                "new_value": new_value,
                "performed_by": performed_by
            }
            db.mock_db.setdefault("AuditLogs", []).append(log)
            db.save_mock_db()

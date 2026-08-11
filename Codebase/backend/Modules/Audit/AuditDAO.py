from Db_utils import DatabaseConnectionManager
from Modules.Audit.AuditModel import AuditLog

class AuditDAO:
    def __init__(self):
        self.db = DatabaseConnectionManager()
        
    def insert(self, audit_log):
        query = """
            INSERT INTO audit_logs (table_name, record_id, action, changed_by)
            VALUES (?, ?, ?, ?)
        """
        cursor = self.db.execute(
            query,
            (audit_log.table_name, audit_log.record_id, audit_log.action.value, audit_log.changed_by)
        )
        self.db.commit()
        return cursor.lastrowid

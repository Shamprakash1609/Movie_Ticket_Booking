from Modules.Audit.AuditDAO import AuditDAO
from Modules.Audit.AuditModel import AuditLog
from Modules.Common.Enums import AuditAction


class AuditService:
    def __init__(self):
        self.audit_dao = AuditDAO()
        
    def log_action(self, table_name, record_id, action, changed_by= None):
        """Centralized system change audit logger"""
        audit_log = AuditLog(
            log_id=None,
            table_name=table_name,
            record_id=record_id,
            action=action,
            changed_by=changed_by
        )
        self.audit_dao.insert(audit_log)

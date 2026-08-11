from Modules.Common.Enums import AuditAction


class AuditLog:
    def __init__(
        self, log_id, table_name, record_id, action, changed_by, changed_at=None
    ):
        self.log_id = log_id
        self.table_name = table_name
        self.record_id = record_id
        self.action = action
        self.changed_by = changed_by
        self.changed_at = changed_at

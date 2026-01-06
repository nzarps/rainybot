import logging
import time
import asyncio
from services.db_manager import db

logger = logging.getLogger("AuditService")

class AuditService:
    def log_action(self, action, user_id, target_id=None, details=None):
        """
        Log an action to the database asynchronously (fire and forget wrapper).
        """
        try:
            # Since we are likely in an async context, ideally we run this in an executor or use asyncpg.
            # However, our DBManager is sync. For now, running sync in the main thread for simplicity 
            # as these are quick inserts. If performance suffers, we move to a thread.
            self._log_sync(action, user_id, target_id, details)
        except Exception as e:
            logger.error(f"Failed to log action {action}: {e}")

    def _log_sync(self, action, user_id, target_id, details):
        try:
            with db.session() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(f"""
                        INSERT INTO audit_logs (action, user_id, target_id, details, timestamp)
                        VALUES ({db.p}, {db.p}, {db.p}, {db.p}, {db.p})
                    """, (action, str(user_id), str(target_id) if target_id else None, details, time.time()))
                finally:
                    cursor.close()
        except Exception as e:
            logger.error(f"DB Error logging action: {e}")

audit_service = AuditService()

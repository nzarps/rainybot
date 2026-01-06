import time
from services.db_manager import db

class AlertService:
    def add_alert(self, user_id, currency, target_price, condition, fiat='usd'):
        """Add a new price alert."""
        with db.session() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO price_alerts (user_id, currency, target_price, condition, fiat, created_at)
                VALUES ({db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p})
            """, (str(user_id), currency.lower(), float(target_price), condition, fiat.lower(), time.time()))

    def get_user_alerts(self, user_id):
        """Fetch all alerts for a specific user."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT id, currency, target_price, condition, fiat FROM price_alerts WHERE user_id = {db.p}", (str(user_id),))
            rows = cursor.fetchall()
            if db.db_type == "sqlite":
                cursor.close()
            
            alerts = []
            for r in rows:
                alerts.append({
                    "id": r[0],
                    "currency": r[1],
                    "target_price": r[2],
                    "condition": r[3],
                    "fiat": r[4]
                })
            return alerts

    def delete_alert(self, alert_id, user_id=None):
        """Remove an alert. user_id is optional but recommended for safety."""
        with db.session() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute(f"DELETE FROM price_alerts WHERE id = {db.p} AND user_id = {db.p}", (alert_id, str(user_id)))
            else:
                cursor.execute(f"DELETE FROM price_alerts WHERE id = {db.p}", (alert_id,))

    def get_all_alerts(self):
        """Fetch all pending alerts for the background task."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, currency, target_price, condition, fiat FROM price_alerts")
            rows = cursor.fetchall()
            if db.db_type == "sqlite":
                cursor.close()
            
            alerts = []
            for r in rows:
                alerts.append({
                    "id": r[0],
                    "user_id": r[1],
                    "currency": r[2],
                    "target_price": r[3],
                    "condition": r[4],
                    "fiat": r[5]
                })
            return alerts

alert_service = AlertService()

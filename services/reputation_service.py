from services.db_manager import db
from database import load_user_stats

class ReputationService:
    def get_badges(self, user_id):
        stats = self._get_user_stats(user_id)
        if not stats:
            return []

        deals = stats.get("deals_completed", 0)
        volume = stats.get("volume_usd", 0.0)
        
        badges = []
        
        if deals >= 100 or volume >= 20000:
            badges.append("💎 Diamond")
        elif deals >= 50 or volume >= 5000:
            badges.append("🥇 Gold")
        elif deals >= 10 or volume >= 500:
            badges.append("🥈 Silver")
        elif deals >= 1:
            badges.append("🥉 Bronze")
            
        return badges

    def _get_user_stats(self, user_id):
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(f"SELECT deals_completed, volume_usd FROM users WHERE user_id = {db.p}", (str(user_id),))
                    row = cursor.fetchone()
                    if row:
                        return {"deals_completed": row[0], "volume_usd": row[1]}
                finally:
                    cursor.close()
        except Exception:
            return None
        return None

reputation_service = ReputationService()


import sys
import os
import time

# Add project root 
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from services.blacklist_service import blacklist_service
from services.audit_service import audit_service
from services.reputation_service import reputation_service
from services.db_manager import db

def verify_blacklist():
    print("\n--- Testing Blacklist ---")
    user_id = "test_bad_actor_999"
    admin_id = "admin_1"
    
    # Clean up first
    blacklist_service.remove_user(user_id)
    
    # 1. Add
    print(f"Adding {user_id}...")
    blacklist_service.add_user(user_id, "Scam attempt", admin_id)
    
    # 2. Check
    is_blocked = blacklist_service.is_blacklisted(user_id)
    print(f"Is blacklisted? {is_blocked} (Expected: True)")
    
    info = blacklist_service.get_info(user_id)
    print(f"Info: {info}")
    
    # 3. Remove
    print(f"Removing {user_id}...")
    blacklist_service.remove_user(user_id)
    is_blocked_after = blacklist_service.is_blacklisted(user_id)
    print(f"Is blacklisted after remove? {is_blocked_after} (Expected: False)")

def verify_audit():
    print("\n--- Testing Audit Logs ---")
    user_id = "test_user_123"
    audit_service.log_action("TEST_ACTION", user_id, details="Running verification script")
    
    # Verify DB insertion
    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            print(f"Last Log: {row}")

def verify_reputation():
    print("\n--- Testing Reputation ---")
    user_id = "test_rep_user"
    
    # Reset
    with db.session() as conn:
        with conn.cursor() as cursor:
             cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
             cursor.execute("INSERT INTO users (user_id, deals_completed, volume_usd) VALUES (%s, %s, %s)", (user_id, 55, 100.0))

    badges = reputation_service.get_badges(user_id)
    print(f"Badges for {user_id} (55 deals): {badges} (Expected: Gold)")

if __name__ == "__main__":
    verify_blacklist()
    verify_audit()
    verify_reputation()

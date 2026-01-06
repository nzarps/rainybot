
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database import load_counter, load_all_data, get_deal_by_dealid, update_user_stats, get_top_users, save_counter

def verify():
    print("--- Verifying Database Refactor ---")
    
    # 1. Counter
    c = load_counter()
    print(f"Counter: {c}")
    try:
        new_c = c + 1
        save_counter(new_c)
        c2 = load_counter()
        if c2 == new_c:
            print(f"Counter update success: {c2}")
        else:
            print(f"Counter update failed: {c2} != {new_c}")
    except Exception as e:
        print(f"Counter test error: {e}")

    # 2. Load All Data
    data = load_all_data()
    print(f"Loaded {len(data)} deals.")
    
    # 3. Get Specific Deal
    target_id = "0co0577d4q8macwpn09hv8nqqg4dc8judoqn9j9ugl0we4lcmp4vsry106nl1sa1"
    deal = get_deal_by_dealid(target_id)
    if deal:
        print(f"Found deal {target_id}: Amount={deal.get('amount')}, Currency={deal.get('currency')}")
    else:
        print(f"Deal {target_id} NOT FOUND.")

    # 4. User Stats
    print("Testing User Stats...")
    test_uid = 999999
    update_user_stats(test_uid, 100.0)
    top = get_top_users(limit=20)
    found = False
    for uid, stats in top:
        if str(uid) == str(test_uid):
            print(f"Found test user {uid}: {stats}")
            found = True
            break
    if not found:
        print("Test user not found in top users.")

if __name__ == "__main__":
    verify()

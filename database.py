import json
import logging
import time
from services.db_manager import db

logger = logging.getLogger("Database")

# --- Performance Caching Layer ---
class SimpleCache:
    def __init__(self, ttl=60):
        self.cache = {}
        self.ttl = ttl

    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None

    def set(self, key, data):
        self.cache[key] = (data, time.time())

# TTL Caches for high-frequency queries
STATS_CACHE = SimpleCache(ttl=60)      # Cache user stats for 60s
LEADERBOARD_CACHE = SimpleCache(ttl=300) # Cache leaderboard for 5m

# --- Global Memory Cache ---
GLOBAL_DEAL_CACHE = None
cache_lock = None # Initialize lazily

def create_deal_id(length: int = 64, prefix: str = ""):
    import string
    import secrets
    charset = string.ascii_lowercase + string.digits
    deal_id = ''.join(secrets.choice(charset) for _ in range(length))
    return f"{prefix}{deal_id}" if prefix else deal_id

def _row_to_dict(row):
    """Convert DB row to deal dictionary"""
    # Row: (deal_id, channel_id, buyer_id, seller_id, amount, currency, status, created_at, other_data)
    if not row:
        return None
        
    base_data = {
        "deal_id": row[0],
        "channel_id": row[1],
        "buyer": row[2],
        "seller": row[3],
        "amount": row[4],
        "currency": row[5],
        "status": row[6],
        "start_time": row[7]
    }
    
    other_data = row[8] if row[8] else {}
    # If other_data is already a dict (psycopg2 handles JSONB automatically), use it. 
    # If it's a string (SQLite), parse it.
    if isinstance(other_data, str):
        try:
            other_data = json.loads(other_data)
        except:
            other_data = {}
            
    full_data = {**other_data, **base_data}
    return full_data

def load_all_data():
    global GLOBAL_DEAL_CACHE
    if GLOBAL_DEAL_CACHE is not None:
        return GLOBAL_DEAL_CACHE

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT deal_id, channel_id, buyer_id, seller_id, amount, currency, status, created_at, other_data FROM deals")
        rows = cursor.fetchall()
        if db.db_type == "sqlite":
            cursor.close()
            
        data = {}
        for row in rows:
            deal_dict = _row_to_dict(row)
            if deal_dict:
                data[deal_dict['deal_id']] = deal_dict
        
        GLOBAL_DEAL_CACHE = data
        return data

def save_all_data(data):
    """Save all data to DB (Background)"""
    global GLOBAL_DEAL_CACHE
    GLOBAL_DEAL_CACHE = data
    
    import threading
    def _bg_save():
        try:
            # Use list(data.items()) to avoid "dictionary changed size during iteration"
            items_snapshot = list(data.items())
            with db.session() as conn:
                cursor = conn.cursor()
                for deal_id, info in items_snapshot:
                    _upsert_deal_cursor(cursor, deal_id, info)
                if db.db_type == "sqlite":
                    cursor.close()
        except Exception as e:
            logger.error(f"Background save_all_data failed: {e}")

    threading.Thread(target=_bg_save, daemon=True).start()

def _upsert_deal_cursor(cursor, deal_id, info):
    channel_id = str(info.get("channel_id"))
    buyer = info.get("buyer")
    seller = info.get("seller")
    amount = info.get("amount", 0.0)
    currency = info.get("currency")
    created_at = info.get("start_time")
    status = info.get("status", "active")
    
    schema_keys = {"deal_id", "channel_id", "buyer", "seller", "amount", "currency", "start_time", "status"}
    other_data = {k: v for k, v in info.items() if k not in schema_keys}
    
    # Handle JSON serialization based on DB type
    if db.db_type == "postgres":
        from psycopg2.extras import Json
        json_val = Json(other_data)
    else:
        json_val = json.dumps(other_data)

    if db.db_type == "sqlite":
        # Use INSERT OR REPLACE for SQLite to handle all unique constraints (deal_id and channel_id)
        cursor.execute(f"""
            INSERT OR REPLACE INTO deals (deal_id, channel_id, buyer_id, seller_id, amount, currency, status, created_at, other_data)
            VALUES ({db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p})
        """, (deal_id, channel_id, buyer, seller, amount, currency, status, created_at, json_val))
    else:
        # Postgres UPSERT
        cursor.execute(f"""
            INSERT INTO deals (deal_id, channel_id, buyer_id, seller_id, amount, currency, status, created_at, other_data)
            VALUES ({db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p})
            ON CONFLICT(deal_id) DO UPDATE SET
                channel_id=EXCLUDED.channel_id,
                buyer_id=EXCLUDED.buyer_id,
                seller_id=EXCLUDED.seller_id,
                amount=EXCLUDED.amount,
                currency=EXCLUDED.currency,
                status=EXCLUDED.status,
                created_at=EXCLUDED.created_at,
                other_data=EXCLUDED.other_data
        """, (deal_id, channel_id, buyer, seller, amount, currency, status, created_at, json_val))

def save_deal_field_sync(deal_id, field, value):
    """Synchronously updates a single field of a deal in the DB and cache."""
    global GLOBAL_DEAL_CACHE
    data = load_all_data()
    if deal_id not in data:
        return False
        
    data[deal_id][field] = value
    GLOBAL_DEAL_CACHE = data
    
    try:
        with db.session() as conn:
            cursor = conn.cursor()
            _upsert_deal_cursor(cursor, deal_id, data[deal_id])
            if db.db_type == "sqlite":
                cursor.close()
        return True
    except Exception as e:
        logger.error(f"Sync save failed for {deal_id}.{field}: {e}")
        return False

def load_counter():
    # Sync with counter.json (User Request: "old stats")
    file_val = 0
    try:
        import os
        if os.path.exists("counter.json"):
            with open("counter.json", "r") as f:
                content = f.read().strip()
                if content:
                    file_val = int(content)
    except Exception as e:
        logger.error(f"Failed to read counter.json: {e}")

    db_val = 0
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT value FROM config WHERE key={db.p}", ('deal_counter',))
        row = cursor.fetchone()
        if db.db_type == "sqlite":
            cursor.close()
        if row:
            db_val = int(row[0])
    
    # Return max value and ensure DB is synced
    final_val = max(file_val, db_val)
    
    # If file was higher, update DB
    if file_val > db_val:
        save_counter(final_val) # This will update DB and overwrite file again (safe)
        
    return final_val

def save_counter(counter):
    # Save to DB
    with db.session() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO config (key, value) VALUES ({db.p}, {db.p})
            ON CONFLICT (key) DO UPDATE SET value = excluded.value
        """ if db.db_type == "sqlite" else f"""
            INSERT INTO config (key, value) VALUES ({db.p}, {db.p})
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, ('deal_counter', str(counter)))
        if db.db_type == "sqlite":
            cursor.close()
            
    # Save to counter.json
    try:
        with open("counter.json", "w") as f:
            f.write(str(counter))
    except Exception as e:
        logger.error(f"Failed to write counter.json: {e}")

def get_deal_by_dealid(deal_id):
    """Fetch deal from cache (Fast)"""
    data = load_all_data()
    return data.get(deal_id)

def get_deal_by_channel(channel_id):
    """Fetch deal from cache by channel ID (Fast)"""
    data = load_all_data()
    cid_str = str(channel_id)
    for deal_id, deal in data.items():
        if str(deal.get('channel_id')) == cid_str:
            return deal_id, deal
    return None, None

def get_deal_by_address(address):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        if db.db_type == "postgres":
             # Query: other_data ->> 'address' = ?
            query = f"SELECT deal_id, channel_id, buyer_id, seller_id, amount, currency, status, created_at, other_data FROM deals WHERE other_data ->> 'address' = {db.p}"
        else:
             # SQLite: json_extract
            query = f"SELECT deal_id, channel_id, buyer_id, seller_id, amount, currency, status, created_at, other_data FROM deals WHERE json_extract(other_data, '$.address') = {db.p}"

        cursor.execute(query, (address,))
        row = cursor.fetchone()
        if db.db_type == "sqlite":
            cursor.close()
        if row:
            deal_dict = _row_to_dict(row)
            return deal_dict['deal_id'], deal_dict
    return None, None

def update_deal(channel_id, deal_data):
    """Update deal in cache and DB synchronously for reliability"""
    global GLOBAL_DEAL_CACHE
    deal_id = deal_data.get("deal_id") or str(channel_id)
    
    # Update cache
    data = load_all_data()
    data[deal_id] = deal_data
    GLOBAL_DEAL_CACHE = data

    # Sync Save (small enough that sync is better for ACID)
    try:
        with db.session() as conn:
            cursor = conn.cursor()
            _upsert_deal_cursor(cursor, deal_id, deal_data)
            if db.db_type == "sqlite":
                cursor.close()
    except Exception as e:
        logger.error(f"update_deal failed: {e}")

# =====================================================
# USER STATS (Leaderboard)
# =====================================================

def load_user_stats():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, deals_completed, volume_usd, current_streak, highest_streak, xp FROM users")
        rows = cursor.fetchall()
        if db.db_type == "sqlite":
            cursor.close()
        stats = {}
        for row in rows:
            stats[str(row[0])] = {
                "deals": row[1], 
                "volume": row[2],
                "streak": row[3],
                "highest_streak": row[4],
                "xp": row[5]
            }
        return stats

def update_user_stats(user_id: int, amount_usd: float, crypto_amount: float = 0.0, currency: str = ""):
    from datetime import datetime
    uid = str(user_id)
    now = datetime.utcnow()
    today_str = now.strftime('%Y-%m-%d')
    
    # XP formula: 10 XP per deal + 1 XP per $10 volume (capped at 50 XP volume bonus)
    xp_gain = 10 + min(50, int(amount_usd / 10))
    import time
    timestamp = time.time()

    deal_info = {
        "amount": amount_usd,
        "crypto": crypto_amount,
        "currency": currency.upper(),
        "date": today_str
    }
    
    with db.session() as conn:
        cursor = conn.cursor()
        
        # Get current streak data
        cursor.execute(f"SELECT current_streak, highest_streak, last_deal_date FROM users WHERE user_id = {db.p}", (uid,))
        row = cursor.fetchone()
        
        current_streak = 0
        highest_streak = 0
        last_deal_date = None
        
        if row:
            current_streak, highest_streak, last_deal_date = row
            
            if last_deal_date == today_str:
                # Already did a deal today, streak stays the same
                pass
            elif last_deal_date:
                from datetime import timedelta
                last_date = datetime.strptime(last_deal_date, '%Y-%m-%d')
                if (now.date() - last_date.date()) == timedelta(days=1):
                    # Next day! Increment streak
                    current_streak += 1
                else:
                    # Missed a day or more, reset streak
                    current_streak = 1
            else:
                current_streak = 1
        else:
            current_streak = 1
            
        highest_streak = max(highest_streak, current_streak)

        cursor.execute(f"""
            INSERT INTO users (user_id, deals_completed, volume_usd, current_streak, highest_streak, last_deal_date, xp, last_deal_info, first_seen)
            VALUES ({db.p}, 1, {db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p}, {db.p})
            ON CONFLICT(user_id) DO UPDATE SET
                deals_completed = {"deals_completed + 1" if db.db_type == "sqlite" else "users.deals_completed + 1"},
                volume_usd = {"volume_usd + " + db.p if db.db_type == "sqlite" else "users.volume_usd + " + db.p},
                current_streak = {db.p},
                highest_streak = {db.p},
                last_deal_date = {db.p},
                xp = {"xp + " + db.p if db.db_type == "sqlite" else "users.xp + " + db.p},
                last_deal_info = {db.p},
                first_seen = COALESCE(users.first_seen, {db.p})
        """, (uid, amount_usd, current_streak, highest_streak, today_str, xp_gain, json.dumps(deal_info), timestamp,
              amount_usd, current_streak, highest_streak, today_str, xp_gain, json.dumps(deal_info), timestamp))
        
        if db.db_type == "sqlite":
            cursor.close()

def get_gamified_stats(user_id):
    """Fetch all gamification data for a user with TTL caching."""
    cached = STATS_CACHE.get(user_id)
    if cached: return cached

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT deals_completed, volume_usd, current_streak, highest_streak, xp, achievements, badges, 
                   used_chains, languages_used, fast_deals, reputation_score, first_seen, referral_code,
                   last_deal_info, last_achievement
            FROM users WHERE user_id = {db.p}
        """, (str(user_id),))
        row = cursor.fetchone()
        if row:
            import json
            achievements = row[5] if row[5] else "[]"
            badges = row[6] if row[6] else "[]"
            
            if isinstance(achievements, str):
                try: achievements = json.loads(achievements)
                except: achievements = []
                
            if isinstance(badges, str):
                try: badges = json.loads(badges)
                except: badges = []

            used_chains = row[7] if row[7] else "[]"
            if isinstance(used_chains, str):
                try: used_chains = json.loads(used_chains)
                except: used_chains = []

            last_deal_info = row[13]
            if isinstance(last_deal_info, str):
                try: last_deal_info = json.loads(last_deal_info)
                except: last_deal_info = None

            # Legacy Backfill: If last_deal_info is missing, fetch from deals table
            if not last_deal_info and row[0] > 0: # row[0] is deals_completed
                try:
                    # Comprehensive status list for completed deals
                    cursor.execute(f"""
                        SELECT amount, currency, other_data, created_at 
                        FROM deals 
                        WHERE (buyer_id = {db.p} OR seller_id = {db.p}) 
                        AND status IN ('released', 'completed', 'awaiting_withdrawal') 
                        ORDER BY created_at DESC LIMIT 1
                    """, (str(user_id), str(user_id)))
                    deal_row = cursor.fetchone()
                    
                    if deal_row:
                        d_amount, d_curr, d_other, d_date = deal_row
                        if isinstance(d_other, str):
                             try: d_other = json.loads(d_other)
                             except: d_other = {}
                        
                        # Handle varied amount keys (ltc_amount is common, fallback to secured_amount)
                        crypto_amt = d_other.get('ltc_amount', d_other.get('secured_amount', 0.0))
                        
                        # Format date
                        from datetime import datetime
                        d_str = datetime.fromtimestamp(d_date).strftime('%Y-%m-%d') if d_date else "Legacy"
                        
                        last_deal_info = {
                            "amount": float(d_amount or 0),
                            "crypto": float(crypto_amt or 0),
                            "currency": d_curr.upper() if d_curr else "UNKNOWN",
                            "date": d_str
                        }
                        
                        # Use the existing connection to update (safer for some DB drivers)
                        cursor.execute(f"UPDATE users SET last_deal_info = {db.p} WHERE user_id = {db.p}", (json.dumps(last_deal_info), str(user_id)))
                        print(f"[BACKFILL] Successfully loaded legacy deal for UID {user_id}: {last_deal_info}")
                    else:
                        print(f"[BACKFILL] No completed deals found in deals table for UID {user_id}")
                except Exception as e:
                    logger.error(f"Error backfilling last_deal_info: {e}")
                    print(f"[BACKFILL_ERROR] UID {user_id}: {e}")

            res = {
                "deals": row[0],
                "volume": row[1],
                "streak": row[2],
                "highest_streak": row[3],
                "xp": row[4],
                "achievements": achievements,
                "badges": badges,
                "used_chains": used_chains,
                "languages_used": row[8] or 1,
                "fast_deals": row[9] or 0,
                "reputation": row[10] or 0,
                "first_seen": row[11],
                "referral_code": row[12],
                "last_deal_info": last_deal_info,
                "last_achievement": row[14]
            }
            if db.db_type == "sqlite": cursor.close()
            STATS_CACHE.set(user_id, res)
            return res

        if db.db_type == "sqlite": cursor.close()
        return {
            "deals": 0, "volume": 0.0, "streak": 0, "highest_streak": 0, 
            "xp": 0, "achievements": [], "badges": [],
            "used_chains": [], "languages_used": 1, "fast_deals": 0,
            "reputation": 0, "first_seen": None, "referral_code": None,
            "last_deal_info": None, "last_achievement": None
        }

def update_user_metadata(user_id, chain=None, language=None, fast_deal=False):
    """Update non-volume metadata for achievements."""
    uid = str(user_id)
    with db.session() as conn:
        cursor = conn.cursor()
        
        if language:
             # Logic to check if its a new language would be complex without loading first.
             # We skip for now and just set to a higher value if needed, 
             # but better to have a proper 'languages_used_list' column.
             # For now, let's just increment if its not 'en'.
             pass

        if chain:
             # Get current used_chains
             cursor.execute(f"SELECT used_chains FROM users WHERE user_id = {db.p}", (uid,))
             row = cursor.fetchone()
             chains = []
             if row and row[0]:
                 try: chains = json.loads(row[0])
                 except: pass
             
             if chain.lower() not in [c.lower() for c in chains]:
                 chains.append(chain.lower())
                 cursor.execute(f"UPDATE users SET used_chains = {db.p} WHERE user_id = {db.p}", (json.dumps(chains), uid))

        if fast_deal:
             cursor.execute(f"UPDATE users SET fast_deals = fast_deals + 1 WHERE user_id = {db.p}", (uid,))

def update_achievements(user_id, achievements_list):
    import json
    uid = str(user_id)
    json_val = json.dumps(achievements_list)
    with db.session() as conn:
        cursor = conn.cursor()
        # Find the new achievement if achievements_list grew
        cursor.execute(f"SELECT achievements FROM users WHERE user_id = {db.p}", (uid,))
        row = cursor.fetchone()
        old_list = []
        if row and row[0]:
            try: old_list = json.loads(row[0])
            except: pass
        
        new_ach = None
        for a in achievements_list:
            if a not in old_list:
                new_ach = a # Found the newest one
                break

        if new_ach:
            cursor.execute(f"UPDATE users SET achievements = {db.p}, last_achievement = {db.p} WHERE user_id = {db.p}", (json_val, new_ach, uid))
        else:
            cursor.execute(f"UPDATE users SET achievements = {db.p} WHERE user_id = {db.p}", (json_val, uid))
        if db.db_type == "sqlite":
            cursor.close()

def update_badges(user_id, badges_list):
    import json
    uid = str(user_id)
    json_val = json.dumps(badges_list)
    with db.session() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET badges = {db.p} WHERE user_id = {db.p}", (json_val, uid))
        if db.db_type == "sqlite":
            cursor.close()

def get_top_users(limit=10):
    """Fetch top users by volume with TTL caching for high-concurrency."""
    cache_key = f"top_{limit}"
    cached = LEADERBOARD_CACHE.get(cache_key)
    if cached: return cached

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT user_id, deals_completed, volume_usd 
            FROM users 
            ORDER BY volume_usd DESC 
            LIMIT {db.p}
        """, (limit,))
        rows = cursor.fetchall()
        if db.db_type == "sqlite": cursor.close()
        
        result = []
        for row in rows:
            result.append((str(row[0]), {"deals": row[1], "volume": row[2]}))
        
        LEADERBOARD_CACHE.set(cache_key, result) # Cache for 5 mins
        return result

def get_single_user_stats(user_id):
    """Fetch stats for a single user efficiently."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT deals_completed, volume_usd FROM users WHERE user_id = {db.p}", (str(user_id),))
        row = cursor.fetchone()
        if db.db_type == "sqlite":
            cursor.close()
        
        if row:
            return {"deals": row[0], "volume": row[1]}
        return {"deals": 0, "volume": 0.0}

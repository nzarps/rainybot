
import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from services.rpc_service import rpc_manager
from utils.backup import backup_sqlite, backup_postgres, MAX_BACKUPS

def verify_backup():
    print("--- Testing Backup System ---")
    # Simulate backup call
    # Try sqlite logic (even if file missing, it prints error safely)
    backup_sqlite()
    
    # Try logic for postgres
    # backup_postgres() # Skipped to avoid shell error noise if pg_dump missing
    
    if os.path.exists("backups"):
        print(f"Backups directory exists: {os.listdir('backups')}")
    else:
        print("Backups dir NOT created.")

def verify_rpc():
    print("\n--- Testing RPC Service ---")
    print(f"RPC Manager initialized. Cache state: {rpc_manager._cache}")
    # We can't easily test async call without loop, but instantiation is verified.

if __name__ == "__main__":
    verify_backup()
    verify_rpc()

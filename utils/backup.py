
import os
import shutil
import datetime
import subprocess
import glob

# Configuration
BACKUP_DIR = "backups"
DB_FILE_SQLITE = "rainyday.db"
POSTGRES_DB = "rainyday"
MAX_BACKUPS = 10

def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def cleanup_old_backups():
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.zip")))
    if len(files) > MAX_BACKUPS:
        for f in files[:-MAX_BACKUPS]:
            print(f"Deleting old backup: {f}")
            os.remove(f)

def backup_sqlite():
    if not os.path.exists(DB_FILE_SQLITE):
        print(f"SQLite DB {DB_FILE_SQLITE} not found. Skipping.")
        return False
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_zip = os.path.join(BACKUP_DIR, f"backup_sqlite_{timestamp}")
    
    try:
        shutil.make_archive(target_zip, 'zip', root_dir='.', base_dir=DB_FILE_SQLITE)
        print(f"SQLite backup created: {target_zip}.zip")
        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def backup_postgres():
    # Requires pg_dump installed and accessible
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_file = os.path.join(BACKUP_DIR, f"pg_dump_{timestamp}.sql")
    target_zip = os.path.join(BACKUP_DIR, f"backup_pg_{timestamp}")
    
    # Try to grab creds from env if needed, but PGPASSWORD env var is standard
    try:
        # Simple local execution
        cmd = f"pg_dump {POSTGRES_DB} > {dump_file}"
        ret = subprocess.call(cmd, shell=True)
        
        if ret == 0:
            shutil.make_archive(target_zip, 'zip', root_dir=BACKUP_DIR, base_dir=os.path.basename(dump_file))
            os.remove(dump_file) # Remove raw SQL after zip
            print(f"Postgres backup created: {target_zip}.zip")
            return True
        else:
            print("pg_dump failed (exit code != 0). Check postgres credentials/path.")
            return False
            
    except Exception as e:
        print(f"Postgres backup error: {e}")
        return False

if __name__ == "__main__":
    ensure_backup_dir()
    
    # Heuristic: check if we are using postgres based on .env or assumptions.
    # For now, try sqlite, if not found, try postgres.
    
    if os.path.exists(DB_FILE_SQLITE):
        backup_sqlite()
    else:
        # Fallback to postgres backup attempt
        backup_postgres()
        
    cleanup_old_backups()

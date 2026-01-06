# Setting Up PostgreSQL for RainyDay Bot

Since you are running on Linux, here is how to find or generate the credentials you need.

## 1. Check if PostgreSQL is running
Run the following command in your terminal:
```bash
sudo systemctl status postgresql
```
If it says `Active: active (exited)` or `active (running)`, it's running.
If it says `Unit postgresql.service could not be found` or `inactive`, you need to install or start it.

**To Install/Start:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## 2. Create the Database and User
You usually create a **new** user and database specifically for the bot.

Run these commands one by one:

1. **Switch to the postgres system user:**
   ```bash
   sudo -i -u postgres
   ```

2. **Open the SQL prompt:**
   ```bash
   psql
   ```

3. **Create the User (Copy/Paste this):**
   *(Replace 'secure_password' with a real password you want to use)*
   ```sql
   CREATE USER rainyday_user WITH PASSWORD 'secure_password';
   ```

4. **Create the Database:**
   ```sql
   CREATE DATABASE rainyday_db OWNER rainyday_user;
   ```

5. **Grant Privileges:**
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE rainyday_db TO rainyday_user;
   ```
   *(If using Postgres 15+, you also need this):*
   ```sql
   \c rainyday_db
   GRANT ALL ON SCHEMA public TO rainyday_user;
   ```

6. **Exit:**
   Type `\q` to exit psql, then `exit` to go back to your normal user.

## 3. Configure Your .env File
Now that you have created them, open your `.env` file (`/home/k/rainyday-bot/.env`) and fill in the values:

```env
POSTGRES_DB=rainyday_db
POSTGRES_USER=rainyday_user
POSTGRES_PASSWORD=secure_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

## Troubleshooting
- **Connection Refused**: This means Postgres isn't running or isn't listening on `127.0.0.1`.
    - Try changing `POSTGRES_HOST` to `localhost` in `.env`.
    - Check `/etc/postgresql/{version}/main/pg_hba.conf` to ensure it allows "md5" or "scram-sha-256" authentication for local connections.

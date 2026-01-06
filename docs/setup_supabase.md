# Connecting Supabase to RainyDay Bot

I have updated the bot to accept a single **Connection String**.

## Instructions

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard).
2. Click **Settings** (Cog Icon on the left) -> **Database**.
3. Under **Connection String**, click the **URI** tab (not parameters).
4. Copy the long string. It looks like:
   `postgresql://postgres.xxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres`
   
   *(Note: You will need to replace `[YOUR-PASSWORD]` with the actual password you created for the project. If you are asked for "Transaction" or "Session" mode, choose **Session** mode for best results with bots).*

   > **Why not API Keys?**
   > RainyDay Bot uses a direct SQL connection for maximum performance and compatibility with standard database tools. The API Keys (Anon/Service Role) are for web apps (Javascript). For Python backend bots, the "Connection String" is the correct method.

5. Open `.env` and add this single line:
   ```env
   DATABASE_URL=postgresql://postgres.xxxx:mypassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
   
   *(You can remove the old POSTGRES_USER, POSTGRES_HOST, etc variables).*

6. **Done!** The bot will now connect to Supabase.

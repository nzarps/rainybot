@tasks.loop(seconds=60)
async def check_idle_deals():
    """Check for deals where roles haven't been selected for too long."""
    try:
        data = load_all_data()
        current_time = time.time()
        
        for deal_id, deal in list(data.items()): # Use list to avoid runtime error during iteration
            # Only check deals that are in "started" phase (waiting for roles)
            if deal.get("status") != "started":
                continue
                
            # Skip if roles ARE selected (i.e., deal is active)
            if deal.get("seller") != "None" and deal.get("buyer") != "None":
                continue
                
            start_time = deal.get("start_time", 0)
            elapsed = current_time - start_time
            channel_id = deal.get("channel_id")
            
            if not channel_id:
                continue
                
            channel = bot.get_channel(int(channel_id))
            if not channel:
                continue

            # WARN at 10 minutes (600 seconds)
            if elapsed > 600 and not deal.get("role_warning_sent"):
                try:
                    embed = discord.Embed(
                        title="⏳ Idle Warning",
                        description=(
                            "No roles have been selected for 10 minutes.\n"
                            "**This ticket will close automatically in 5 minutes.**"
                        ),
                        color=discord.Color.orange()
                    )
                    await channel.send(embed=embed, view=ExtendButton())
                    
                    deal["role_warning_sent"] = True
                    save_all_data(data)
                    print(f"[Idle] Sent warning for deal {deal_id}")
                except Exception as e:
                    print(f"[Idle] Failed to warn {deal_id}: {e}")

            # CLOSE at 15 minutes (900 seconds)
            elif elapsed > 900:
                try:
                    print(f"[Idle] Auto-closing deal {deal_id}")
                    embed = discord.Embed(
                        title="❌ Ticket Closed",
                        description="Ticket closed due to inactivity (15m timeout).",
                        color=discord.Color.red()
                    )
                    await channel.send(embed=embed)
                    
                    # Mark as cancelled
                    deal["status"] = "cancelled"
                    save_all_data(data)
                    
                    await asyncio.sleep(2)
                    await channel.delete()
                    
                    # Remove from data completely or keep as cancelled? 
                    # Usually keeping as cancelled is safer for records, but user asked to "close".
                    # Existing code seems to keep records. I will update status.
                    
                except Exception as e:
                    print(f"[Idle] Failed to close {deal_id}: {e}")

    except Exception as e:
        print(f"Idle Check Loop Error: {e}")

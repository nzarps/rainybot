async def update_embeds_on_change(channel, deal):
    """
    Scans the channel for relevant embeds and updates them with new deal participants.
    Targets: "User Selection", "User Confirmation", "RainyDay Auto MiddleMan System"
    """
    try:
        buyer_id = deal.get("buyer")
        seller_id = deal.get("seller")
        
        buyer_mention = f"<@{buyer_id}>" if buyer_id and buyer_id != "None" else "`None`"
        seller_mention = f"<@{seller_id}>" if seller_id and seller_id != "None" else "`None`"
        
        async for message in channel.history(limit=50):
            if message.author.id == bot.user.id and message.embeds:
                embed = message.embeds[0]
                
                # 1. Update "User Selection"
                if embed.title == "User Selection":
                    new_desc = (
                        f"**Sender**\n{buyer_mention}\n\n"
                        f"**Receiver**\n{seller_mention}"
                    )
                    new_embed = discord.Embed(title=embed.title, description=new_desc, color=embed.color)
                    if embed.thumbnail: new_embed.set_thumbnail(url=embed.thumbnail.url)
                    if embed.author: new_embed.set_author(name=embed.author.name, icon_url=embed.author.icon_url)
                    await message.edit(embed=new_embed)
                    
                # 2. Update "User Confirmation"
                elif embed.title == "User Confirmation":
                    new_embed = embed.copy()
                    new_embed.clear_fields()
                    new_embed.add_field(name="Sender", value=buyer_mention, inline=False)
                    new_embed.add_field(name="Receiver", value=seller_mention, inline=False)
                    await message.edit(embed=new_embed)
                    
                # 3. Update "RainyDay Auto MiddleMan System"
                elif embed.title == "RainyDay Auto MiddleMan System":
                    # Reconstruct description to be safe
                    new_desc = (
                        "### 🛡️ Secure Transaction Protocol\n"
                        "• This channel is monitored by our automated escrow system.\n"
                        "• All funds are held securely until the buyer confirms receipt.\n"
                        "• Always confirm you have received the goods before releasing funds.\n\n"
                        "### 📝 Deal Context\n"
                        f"• **Sender:** {buyer_mention}\n"
                        f"• **Receiver:** {seller_mention}\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    )
                    new_embed = discord.Embed(title=embed.title, description=new_desc, color=embed.color)
                    if embed.thumbnail: new_embed.set_thumbnail(url=embed.thumbnail.url)
                    if embed.author: new_embed.set_author(name=embed.author.name, icon_url=embed.author.icon_url)
                    if embed.footer: new_embed.set_footer(text=embed.footer.text, icon_url=embed.footer.icon_url)
                    
                    # Add back fields (Warning Note)
                    if embed.fields:
                         for f in embed.fields:
                             new_embed.add_field(name=f.name, value=f.value, inline=f.inline)
                             
                    await message.edit(embed=new_embed)
                    
    except Exception as e:
        print(f"Failed to update embeds: {e}")

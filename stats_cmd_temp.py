@bot.tree.command(name="stats", description="Check deal statistics for yourself or another user.")
@app_commands.describe(user="The user to check (optional, defaults to you)")
async def stats_cmd(interaction: discord.Interaction, user: discord.Member = None):
    await interaction.response.defer() # Not ephemeral, so others can see the flex
    
    target_user = user or interaction.user
    stats = get_single_user_stats(target_user.id)
    
    deals = stats.get("deals", 0)
    volume = stats.get("volume", 0.0)
    
    # "Professional" Look
    embed = discord.Embed(
        description=f"### {target_user.mention}\n\n**Deals completed:**\n{deals}\n\n**Total USD Value:**\n${volume:,.2f}",
        color=0x2ECC71 # Emerald Green
    )
    
    # Avatar on the right (thumbnail)
    if target_user.avatar:
        embed.set_thumbnail(url=target_user.avatar.url)
    
    # Simple green bar on the side is default for embeds with color
    
    await interaction.followup.send(embed=embed)

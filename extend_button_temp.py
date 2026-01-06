class ExtendButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Extend Time (+15m)", style=discord.ButtonStyle.green, custom_id="extend_time")
    async def extend_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        deal_id, deal = get_deal_by_channel(interaction.channel.id)
        if not deal:
            return await interaction.response.send_message("Deal not found.", ephemeral=True)

        # Update start time to NEW time (effectively resetting the timer)
        deal["start_time"] = time.time()
        deal["role_warning_sent"] = False
        update_deal(interaction.channel.id, deal)

        await interaction.response.send_message("✅ Time extended by 15 minutes!", ephemeral=False)
        # Disable button after use to prevent spam/confusion
        self.stop()
        await interaction.message.delete()

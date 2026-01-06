import discord

async def safe_respond(interaction, *, content=None, embed=None, view=None, ephemeral=False, defer=False, edit_original=False, send_modal=None):
    try:
        if send_modal:
            if not interaction.response.is_done():
                await interaction.response.send_modal(send_modal)
                return True
            return False
        elif defer:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=ephemeral)
            return True
        elif edit_original and interaction.message:
            await interaction.message.edit(content=content, embed=embed, view=view)
            return True
        elif not interaction.response.is_done():
            kwargs = {}
            if content is not None:
                kwargs['content'] = content
            if embed is not None:
                kwargs['embed'] = embed
            if view is not None:
                kwargs['view'] = view
            kwargs['ephemeral'] = ephemeral
            await interaction.response.send_message(**kwargs)
            return True
        else:
            await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
            return True
    except (discord.InteractionResponded, discord.NotFound, discord.HTTPException) as e:
        try:
            if interaction.message and not edit_original:
                await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
                return True
        except:
            pass
        return False

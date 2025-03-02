import api
from config import *
from log import *

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from typing import *

# loading token
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all(), help_command=None)
mg = api.Manager(DATA_FILE)

# connection events

@bot.event
async def on_ready():
    log(f'Ready as {bot.user.name}!')

    # commands = await bot.tree.sync()
    # log(f'Synced tree with {len(commands)} commands', level=SUCCESS)


# events

@bot.event
async def on_interaction(inter:discord.Interaction):
    '''
    Gets called when a button is pressed or a command is used.
    '''
    if inter.type == discord.InteractionType.application_command:
        return
    
    if inter.type == discord.InteractionType.modal_submit:
        if inter.data['custom_id'].startswith('set-text'):
            await send_whisper(inter)
        return
    
    log(f'{inter.user.id} pressed on {inter.id}')

    message_id = inter.message.id
    whisper = mg.get_whisper(message_id)

    # no whisper
    if whisper == None:
        embed = discord.Embed(
            color=discord.Color.red(),
            description='**Whisper not found!**\n\n'\
                'If it was a one-time whisper, it probably expired.'
        )

    # not owner
    elif inter.user.id not in [whisper.owner, whisper.viewer]:
        embed = discord.Embed(
            color=discord.Color.red(),
            description='**You are not meant to view this whisper!**'
        )

    # showing whisper
    else:
        title = '🔥 One-time whisper!' if whisper.once else None

        embed = discord.Embed(
            color=discord.Color.blurple(),
            description=whisper.text
        )
        if title != None:
            embed.set_author(name=title)

        # removing one-time whispers
        if inter.user.id == whisper.viewer and whisper.once:
            print(f'Removing one-time whisper {message_id}')
            mg.remove_whisper(message_id)

    await inter.response.send_message(embed=embed, ephemeral=True)


# commands
@bot.tree.command(
    name='whisper',
    description='Whisper saved text to someone.'
)
@discord.app_commands.describe(
    user='User to whisper saved text to',
    selfdestruct='Whether the whisper should only be viewed once (no by default)',
)
@discord.app_commands.user_install()
async def whisper(
    inter:discord.Interaction,
    user:discord.User,
    selfdestruct:Literal[   
        'Yes (viewable only once)',
        'No (viewable anytime)'
    ]='No (viewable anytime)'
):
    '''
    Whispers saved text.
    '''
    
    if user.id == inter.user.id:
        embed = discord.Embed(
            color=discord.Color.red(),
            description="**You can't whisper to yourself!**"
        )
        await inter.response.send_message(embed=embed,ephemeral=True)
        return

    selfdestruct = 1 if selfdestruct == 'Yes (viewable only once)' else 0
    modal = discord.ui.Modal(
        title='Whisper',
        custom_id=f'set-text:{user.id}:{selfdestruct}'
    )
    modal.add_item(
        discord.ui.TextInput(
            label='Your text',
            style=discord.TextStyle.paragraph,
            max_length=4000 # embed desctiption limit is 4096 but text input limit is 4000
        )
    )
    await inter.response.send_modal(modal)
    return
        
    # sending


# utils?
async def send_whisper(inter: discord.Interaction):
    data = inter.data['custom_id'].split(':')[1:]
    embed = discord.Embed(
        description=f'{inter.user.mention} whispers to <@{data[0]}>...'\
            f'\n\nClick on the button to read the whisper.'
    )

    view = discord.ui.View()

    button = discord.ui.Button(
        style=discord.ButtonStyle.blurple,
        label='Loading...', disabled=True
    )
    view.add_item(button)

    await inter.response.send_message(embed=embed, view=view)
    original = await inter.original_response()

    mg.send_whisper(
        original.id, inter.user.id,
        int(data[0]), inter.data['components'][0]['components'][0]['value'],
        data[1] == '1'
    )

    # new view
    view = discord.ui.View()

    button = discord.ui.Button(
        style=discord.ButtonStyle.blurple,
        label='Read whisper'
    )
    view.add_item(button)

    await inter.edit_original_response(view=view)

@discord.app_commands.describe(
    message_id='Message ID of the whisper'
)
@bot.tree.command(
    name='read',
    description='Read whisper'
)
async def slash_read_whisper(inter:discord.Interaction, message_id: str):
    whisper = mg.get_whisper(int(message_id))
    if whisper == None:
        embed = discord.Embed(
            color=discord.Color.red(),
            description="Whisper not found or it expired"
        )
    elif inter.user.id in [whisper.owner, whisper.viewer]:
        embed = discord.Embed(
            color=discord.Color.blurple(),
            description=whisper.text
        )
    else:
        embed = discord.Embed(
            color=discord.Color.red(),
            description='**You are not meant to view this whisper!**'
        )
    await inter.response.send_message(embed=embed,ephemeral=True) 

## RUNNING BOT
bot.run(TOKEN)

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
mg = api.Manager(USERS_FILE)

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
    
    # answering
    log(f'{inter.user.id} pressed on {inter.id}')

    message_id = int(inter.data['custom_id'])
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

save_text_cmd = 'save-text:1283547176848326771'

# text_gr = discord.app_commands.Group(
#     name='text',
#     description='Manage currently saved text.'
# )

@bot.tree.command(
    name='view-text',
    description='View your currently saved text.'
)
@discord.app_commands.user_install()
async def view_text(
    inter:discord.Interaction
):
    '''
    Shows your current saved text.
    '''
    user = mg.get_user(inter.user.id)

    if user.saved_message == None:
        embed = discord.Embed(
            color=discord.Color.red(),
            description='**No saved text!**\n\n'\
                f'Use </{save_text_cmd}> to save your text.'
        )
    else:
        embed = discord.Embed(
            color=discord.Color.blurple(),
            description="**Saved text:**\n\n"+user.saved_message
        )

    await inter.response.send_message(embed=embed,ephemeral=True)
        


@bot.tree.command(
    name='save-text',
    description='Saves your text to whisper to someone.'
)
@discord.app_commands.user_install()
@discord.app_commands.describe(
    text='Your text to whisper to someone',
)
async def save_text(
    inter:discord.Interaction,
    text:str
):
    '''
    Saves text to whisper.
    '''
    if len(text) > 1024:
        embed = discord.Embed(
            color=discord.Color.red(),
            description="Your text must not be longer than 1024 characters!"
        )

    else:
        mg.save_whisper(inter.user.id, text)

        embed = discord.Embed(
            color=discord.Color.blurple(),
            description="**Success!**"
        )

    await inter.response.send_message(embed=embed,ephemeral=True)



@bot.tree.command(
    name='remove-text',
    description='Remove saved text.'
)
@discord.app_commands.user_install()
async def remove_text(
    inter:discord.Interaction
):
    '''
    Removes saved text.
    '''
    user = mg.get_user(inter.user.id)

    if user.saved_message == None:
        embed = discord.Embed(
            color=discord.Color.red(),
            description="**You don't have any text saved!**"
        )

    else:
        mg.unsave_whisper(inter.user.id)

        embed = discord.Embed(
            color=discord.Color.blurple(),
            description="**Text removed!**"
        )

    await inter.response.send_message(embed=embed,ephemeral=True)


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
    bot_user = mg.get_user(inter.user.id)
    
    if user.id == inter.user.id:
        embed = discord.Embed(
            color=discord.Color.red(),
            description="**You can't whisper to yourself!**"
        )
        await inter.response.send_message(embed=embed,ephemeral=True)
        return

    if bot_user.saved_message == None:
        embed = discord.Embed(
            color=discord.Color.red(),
            description="**You don't have any text saved!**\n\n"\
                f'Use </{save_text_cmd}> to save your text and try again.'
        )
        await inter.response.send_message(embed=embed,ephemeral=True)
        return
        
    # sending
    selfdestruct = selfdestruct == 'Yes (viewable only once)'

    embed = discord.Embed(
        description=f'{inter.user.mention} whispers to {user.mention}...'\
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
        user.id, bot_user.saved_message,
        selfdestruct
    )

    # new view
    view = discord.ui.View()

    button = discord.ui.Button(
        style=discord.ButtonStyle.blurple,
        label='Read whisper', custom_id=str(original.id)
    )
    view.add_item(button)

    await inter.edit_original_response(view=view)


## RUNNING BOT
bot.run(TOKEN)
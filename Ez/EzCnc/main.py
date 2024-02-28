from cnc import CNC
import better_disbot as disbot
import streamlit as st
import asyncio
import threading
import uvicorn
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ.get("bottoken")
server_id = os.environ.get("server_id")
app = CNC(
    db_name="Database", name="EZCNC", debug=True, logs_path="EZCNC_logs"
)  # initiate the api
#app.generate_fake_clients(5)
api = app.api  # exporting the api class so that you can run   "uvicorn main:api"
Database = app.Database
# Define a function to run the Discord bot
def run_discord_bot(db,guild__id:str):
    
    bot = disbot.BOT(db=db,guild_id=guild__id)
    bot.bot.run(TOKEN)


# Start the Discord bot in a separate thread
discord_thread = threading.Thread(target=run_discord_bot, args=(Database,server_id))
discord_thread.start()

# Start the API using uvicorn
if __name__ == "__main__":
    uvicorn.run(api, host="127.0.0.1", port=8000)


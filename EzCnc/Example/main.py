from EzCnc import CNC, disbot
import streamlit as st
import asyncio
import threading
import uvicorn
app = CNC(
    db_name="Database", name="EZCNC", debug=True, logs_path="EZCNC_logs"
)  # initiate the api
# app.generate_fake_clients(10)
api = app.api  # exporting the api class so that you can run   "uvicorn main:api"
Database = app.Database
TOKEN = ""

# Define a function to run the Discord bot
def run_discord_bot(db):
    bot = disbot.BOT(db=db)
    bot.bot.run(TOKEN)


# Start the Discord bot in a separate thread
discord_thread = threading.Thread(target=run_discord_bot, args=(Database,))
discord_thread.start()

# Start the API using uvicorn
if __name__ == "__main__":
    uvicorn.run(api, host="127.0.0.1", port=8000)


from fastapi import FastAPI, File, UploadFile
from Structs.Structs import Client, Command, CommandRequester, ClientResponse
from Database import DB
import os
from loguru import logger

logger.add("LOGS.logs")
Database = DB("Main Test")
DEBUG = True
NAME = "EZ CNC"

app = FastAPI(debug=DEBUG, title=NAME)


@app.post("/api/client/identify", status_code=200)
def identify(client: Client):
    if Database.new_client(client):
        return {"Status": True}
    else:
        return {"Status": False}


@app.post("/api/cnc/command", status_code=200)
def newcommand(command: Command):
    if Database.new_command(command):
        return {"Status": True}
    else:
        return {"Status": False}


@app.post("/api/client/command", status_code=200)
def is_commanded(Requester: CommandRequester):
    response = Database.iscommanded(Requester)
    if response:
        return {"Status": True, "Data": response}
    else:
        return {"Status": False}


@app.post("/api/client/response/file", status_code=200)
def client_response(file: UploadFile, UUID: str):
    # try:
    file_type = os.path.splitext(file.filename)[1]
    Database.insert_file(file, file_type, str(UUID))
    return {"Status": True}


"""
except Exception as e:
    logger.error(str(e))
    return {"Status": False}
"""

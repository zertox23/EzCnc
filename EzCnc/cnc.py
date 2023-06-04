from typing import Any
from fastapi import FastAPI, File, UploadFile
from EzCnc.Structs import Client, Command, CommandRequester, ClientResponse
from EzCnc.Database import DB, Plots
import os
from faker import Faker
from faker.providers import internet
from loguru import logger
import uvicorn


import random

fake = Faker()
fake.add_provider(internet)


class CNC:
    def __init__(
        self,
        db_name: str = "Database.db",
        debug: bool = False,
        name: str = "EzCnc",
        logs_path: str = "EzCnc_logs.logs",
    ):
        self.debug = debug
        self.Database = DB(db_name)
        self.plots = Plots(self.Database)
        logger.add(f"{logs_path}.logs")
        self.api = FastAPI(debug=debug, title=name)

        @self.api.post("/api/client/identify", status_code=200)
        def identify(client: Client):
            if self.Database.new_client(client):
                return {"Status": True}
            else:
                return {"Status": False}

        @self.api.post("/api/cnc/command", status_code=200)
        def newcommand(command: Command):
            if self.Database.new_command(command):
                return {"Status": True}
            else:
                return {"Status": False}

        @self.api.post("/api/client/command", status_code=200)
        def is_commanded(Requester: CommandRequester):
            response = self.Database.iscommanded(Requester)
            if response:
                return {"Status": True, "Data": response}
            else:
                return {"Status": False}

        @self.api.post("/api/client/response/file", status_code=200)
        def client_response(file: UploadFile, UUID: str):
            try:
                self.Database.insert_file(file, str(UUID))
                return {"Status": True}
            except Exception as e:
                logger.error(str(e))
                return {"Status": False}

        @self.api.post("/api/client/response/text", status_code=200)
        def client_response(resp: ClientResponse):
            try:
                self.Database.insert_response(resp)
                return {"Status": True}
            except Exception as e:
                logger.error(str(e))
                return {"Status": False}

    def _GENERATE_FAKE_CLIENTS(self):
        latitude = fake.latitude()
        longitude = fake.longitude()
        location = f"{latitude}, {longitude}"

        return Client(
            uuid=fake.uuid4(),
            name=fake.name(),
            ip=fake.ipv4(),
            country=fake.country(),
            location=location,
        )

    def generate_fake_clients(self, count: int = 10):
        for i in range(count):
            self.Database.new_client(self._GENERATE_FAKE_CLIENTS())

    def generate_fake_responses(self):
        commands = ["cam", "data", "time", "ip"]
        if len(self.Database._return_all_uuids()) > 0:
            for uuid in self.Database._return_all_uuids():
                r = random.choice([1, 0])
                if r > 0:
                    response = ClientResponse(
                        uuid=str(uuid[0]),
                        command=str(random.choice(commands)),
                        response=str(random.choice(["", "RESPONSE"])),
                        result=random.choice([0, 1]),
                    )
                    self.Database.insert_response(resp=response)

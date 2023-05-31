from pydantic import BaseModel
from typing import Optional, Union


class Client(BaseModel):
    uuid: str
    name: str
    ip: str
    country: str
    location: str


class Command(BaseModel):
    command: str
    target: str
    parameter: Union[str, None] = None


class CommandRequester(BaseModel):
    uuid: str


class ClientResponse(BaseModel):
    uuid: str
    command: str
    isfile: bool
    response: str

from pydantic import BaseModel

class Victim(BaseModel):
    id:int
    name:str|None
    ip:str|None
    country:str|None
    location:str|None
    img:str|None

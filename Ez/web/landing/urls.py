from django.urls import path
from . import views

urlpatterns = [
    path("",view=views.home,name="landing"),
    path("control/<int:id>",view=views.control,name="control"),
]

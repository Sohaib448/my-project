from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("Backend is running")

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/", include("detector.urls")),
]
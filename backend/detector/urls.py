from django.urls import path
from . import views

urlpatterns = [
    path('api/health/', health_check, name='health_check'),
]
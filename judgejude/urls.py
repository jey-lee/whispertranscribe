from django.urls import path
from .views import index, transcribe


from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('transcribe/', transcribe, name='transcribe'),
]
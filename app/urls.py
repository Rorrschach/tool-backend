from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login),
    path('register/', views.register),
    path('upload_image/', views.upload_image),
    path('update_image/<int:pk>/', views.update_image),
]
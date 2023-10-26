from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login),
    path('register/', views.register),
    path('upload_images/', views.upload_images),
    path('update_image/<int:pk>/', views.update_image),
]
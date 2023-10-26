from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login),
    path('register/', views.register),
    path('save_annotations/', views.save_annotation),
    path('upload_image/', views.upload_image),
    path('get_user_annotations/', views.get_images_and_annotations),   
]
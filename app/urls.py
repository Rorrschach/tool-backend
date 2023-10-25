from django.urls import path, re_path
from . import views

urlpatterns = [
    # path('', views.getUsers),
    # path('create/', views.createUser),
    # path('read/<str:pk>', views.getUser),
    # path('update/<str:pk>', views.updateUser),
    # path('delete/<str:pk>', views.deleteUser),
    
    re_path('login', views.login),
    re_path('register', views.register),
    re_path('test', views.test_token),
    re_path('saveAnnotations', views.save_annotation),
    
]
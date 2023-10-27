from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('register/', views.register),
    path('upload_images/', views.upload_images),
    path('update_image/<int:pk>/', views.update_annotations),
    path('add_labels', views.add_labels_to_images),
    path('images/getAll/', views.get_all_images)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('register/', views.register),
    path('images/upload/', views.upload_images),
    path('images/updateAnnotations/<int:pk>/', views.update_annotations),
    path('images/addLabels/', views.add_labels_to_images),
    path('images/getAll/', views.get_all_images),
    path('images/get/<int:pk>/', views.get_image_by_id),
    path('pdfs/upload/', views.upload_pdfs),
    path('nlp/upload/', views.upload_nlp_data),
    path('nlp/getAll/', views.get_all_nlp_data),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
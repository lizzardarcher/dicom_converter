from django.urls import path

from apps.converter import views

urlpatterns = [
    path('upload_research', views.UploadResearchView.as_view(), name='upload research'),
    path('my_research', views.UploadResearchView.as_view(), name='my research'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('progress/', views.progress_view, name='progress'),
]
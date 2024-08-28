from django.urls import path

from apps.converter import views

urlpatterns = [
    # path('', views.HomeView.as_view(), name='home'),
    path('upload_research', views.UploadResearchView.as_view(), name='upload research'),
    path('my_research', views.UploadResearchView.as_view(), name='my research'),
]
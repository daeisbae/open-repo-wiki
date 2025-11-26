from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('<str:owner>/<str:repo>/', views.repo_detail, name='repo_detail'),
    path('api/status/<str:owner>/<str:repo>/', views.repo_status_stream, name='repo_status_stream'),
    path('api/repository', views.RepositoryQueueView.as_view(), name='repository_api'),
]

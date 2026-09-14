from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('backups/', views.backup_list, name='backup_list'),
    path('backups/create/', views.create_backup, name='create_backup'),
    path('backups/download/<str:filename>/', views.download_backup, name='download_backup'),
    path('backups/delete/<str:filename>/', views.delete_backup, name='delete_backup'),
]

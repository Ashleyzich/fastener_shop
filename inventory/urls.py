from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/create/', views.product_create, name='product_create'),
    path('product/<int:pk>/update/', views.product_update, name='product_update'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('locations/', views.location_list, name='location_list'),
    path('adjustment/', views.stock_adjustment, name='stock_adjustment'),
    path('adjustment/process/', views.process_stock_adjustment, name='process_stock_adjustment'),
    path('api/search/', views.product_search_api, name='product_search_api'),
]

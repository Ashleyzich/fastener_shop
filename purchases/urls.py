from django.urls import path
from . import views

urlpatterns = [
    path('', views.purchase_list, name='purchase_list'),
    path('create/', views.create_purchase, name='create_purchase'),
    path('<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('<int:pk>/add-item/', views.add_item_to_purchase, name='add_item_to_purchase'),
    path('<int:pk>/order/', views.order_purchase, name='order_purchase'),
    path('<int:pk>/receive/', views.receive_purchase, name='receive_purchase'),
    path('<int:pk>/cancel/', views.cancel_purchase, name='cancel_purchase'),
    path('item/<int:pk>/remove/', views.remove_item_from_purchase, name='remove_item_from_purchase'),
]

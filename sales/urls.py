from django.urls import path
from . import views

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('pos/', views.pos, name='pos'),
    path('create/', views.create_sale, name='create_sale'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/receipt/', views.print_receipt, name='print_receipt'),
    path('api/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('api/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('api/update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('api/complete-sale/', views.complete_sale, name='complete_sale'),
    path('api/cancel-sale/', views.cancel_sale, name='cancel_sale'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/record/', views.record_payment, name='record_payment'),
    path('payments/sale/<int:sale_id>/balance/', views.get_sale_balance, name='get_sale_balance'),
]

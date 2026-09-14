from django.urls import path
from . import views

urlpatterns = [
    path('sales/', views.sales_report, name='sales_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('profit/', views.profit_report, name='profit_report'),
    path('purchases/', views.purchase_report, name='purchase_report'),

    path('export/sales/', views.export_sales_csv, name='export_sales_csv'),
    path('export/inventory/', views.export_inventory_csv, name='export_inventory_csv'),
]


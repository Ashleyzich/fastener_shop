from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderItem

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'supplier', 'status', 'payment_status', 'total_amount', 'order_date']
    list_filter = ['status', 'payment_status', 'order_date']
    search_fields = ['po_number', 'supplier__name']
    inlines = [PurchaseOrderItemInline]

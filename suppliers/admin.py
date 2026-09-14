from django.contrib import admin
from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'company_name', 'contact_person', 'phone', 'email', 'is_active']
    search_fields = ['name', 'company_name', 'phone', 'email']
    list_filter = ['is_active']

from django.contrib import admin
from .models import ShopSettings, UnitOfMeasure, Location

@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'currency', 'tax_rate']

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'unit_type']

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

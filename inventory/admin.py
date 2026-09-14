from django.contrib import admin
from .models import Category, ProductType, Material, Finish, Grade, ThreadType, Product, ProductPrice, StockMovement

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'description']
    search_fields = ['name', 'code']
    list_per_page = 20

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']

@admin.register(Finish)
class FinishAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']

@admin.register(ThreadType)
class ThreadTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'diameter', 'length', 'quantity', 'selling_price', 'location', 'is_low_stock']
    list_filter = ['category', 'material', 'finish', 'grade', 'is_active']
    search_fields = ['name', 'sku', 'barcode', 'diameter', 'length', 'description']
    list_editable = ['quantity', 'selling_price', 'location']
    list_per_page = 25
    readonly_fields = ['sku', 'barcode']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'product_type')
        }),
        ('Specifications', {
            'fields': ('diameter', 'length', 'width', 'thread_type', 'grade', 'material', 'finish')
        }),
        ('Stock Management', {
            'fields': ('quantity', 'low_stock_threshold', 'location', 'unit', 'is_active')
        }),
        ('Pricing', {
            'fields': ('buying_price', 'selling_price')
        }),
        ('Identification', {
            'fields': ('sku', 'barcode', 'image')
        }),
    )

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'reference', 'created_at', 'created_by']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reference']
    list_per_page = 25

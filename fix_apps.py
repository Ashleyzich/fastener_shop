# fix_apps.py
import os

# Fix core/models.py
core_models = """
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        app_label = 'core'

class ShopSettings(models.Model):
    shop_name = models.CharField(max_length=200, default="Fastener Shop")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    low_stock_threshold = models.PositiveIntegerField(default=20)
    receipt_header = models.TextField(blank=True)
    receipt_footer = models.TextField(blank=True)
    
    def __str__(self):
        return self.shop_name
    
    class Meta:
        verbose_name_plural = "Shop Settings"
        app_label = 'core'

class UnitOfMeasure(models.Model):
    UNIT_TYPES = [
        ('PIECE', 'Piece'),
        ('BOX', 'Box'),
        ('PACKET', 'Packet'),
        ('KG', 'Kilogram'),
        ('METER', 'Meter'),
        ('PAIR', 'Pair'),
        ('SET', 'Set'),
        ('DOZEN', 'Dozen'),
    ]
    
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    unit_type = models.CharField(max_length=10, choices=UNIT_TYPES, default='PIECE')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        app_label = 'core'

class Location(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        app_label = 'core'
"""

with open('core/models.py', 'w') as f:
    f.write(core_models)

print("✓ Fixed core/models.py")

# Fix core/apps.py
core_apps = """
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'
"""

with open('core/apps.py', 'w') as f:
    f.write(core_apps)

print("✓ Fixed core/apps.py")

# Fix settings.py INSTALLED_APPS
settings_path = 'fastener_shop/settings.py'
with open(settings_path, 'r') as f:
    content = f.read()

# Replace INSTALLED_APPS section
old_apps = """INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    
    # Local apps
    'core',
    'accounts',
    'inventory',
    'sales',
    'purchases',
    'customers',
    'suppliers',
    'reports',
]"""

new_apps = """INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local apps
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'inventory.apps.InventoryConfig',
    'sales.apps.SalesConfig',
    'purchases.apps.PurchasesConfig',
    'customers.apps.CustomersConfig',
    'suppliers.apps.SuppliersConfig',
    'reports.apps.ReportsConfig',
]"""

if old_apps in content:
    content = content.replace(old_apps, new_apps)
    with open(settings_path, 'w') as f:
        f.write(content)
    print("✓ Fixed INSTALLED_APPS in settings.py")
else:
    print("⚠ Could not find INSTALLED_APPS section. Please fix manually.")

print("\n✅ Fixes applied! Now run:")
print("python manage.py makemigrations")
print("python manage.py migrate")
print("python manage.py runserver")
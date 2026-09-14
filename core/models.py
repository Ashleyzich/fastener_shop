
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

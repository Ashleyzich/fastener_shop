from django.db import models
from core.models import TimeStampedModel
from inventory.models import Product
from customers.models import Customer
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid

class Sale(TimeStampedModel):
    """Main sale/invoice record"""
    SALE_TYPES = [
        ('CASH', 'Cash Sale'),
        ('CREDIT', 'Credit Sale'),
        ('QUOTE', 'Quote'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('ECOCASH', 'Ecocash'),
        ('SWIPE', 'Swipe/Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT', 'Credit'),
        ('MIXED', 'Mixed Payment'),
        ('PAID', 'Paid'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales')
    sale_type = models.CharField(max_length=10, choices=SALE_TYPES, default='CASH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    salesperson = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='sales')
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        year = timezone.now().year
        month = timezone.now().month
        sequence = Sale.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).count() + 1
        return f"INV-{year}-{month:02d}-{sequence:04d}"
    
    @property
    def remaining_balance(self):
        return self.total_amount - self.paid_amount
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"
    
    class Meta:
        ordering = ['-created_at']
        app_label = 'sales'

class SaleItem(models.Model):
    """Individual items in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = (self.quantity * self.unit_price) - self.discount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.sale.invoice_number} - {self.product.name} x {self.quantity}"
    
    class Meta:
        ordering = ['id']
        app_label = 'sales'

class Payment(TimeStampedModel):
    """Payment records for sales"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Sale.PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Payment {self.id} - {self.sale.invoice_number} - {self.amount}"
    
    class Meta:
        ordering = ['-created_at']
        app_label = 'sales'

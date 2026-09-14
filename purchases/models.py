from django.db import models
from core.models import TimeStampedModel
from inventory.models import Product
from suppliers.models import Supplier
from django.utils import timezone
import uuid

class PurchaseOrder(TimeStampedModel):
    """Purchase order from supplier"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ORDERED', 'Ordered'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_STATUS = [
        ('UNPAID', 'Unpaid'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
    ]
    
    po_number = models.CharField(max_length=50, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='UNPAID')
    
    # Financial
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Dates
    order_date = models.DateField(auto_now_add=True)
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self.generate_po_number()
        super().save(*args, **kwargs)
    
    def generate_po_number(self):
        year = timezone.now().year
        sequence = PurchaseOrder.objects.filter(
            created_at__year=year
        ).count() + 1
        return f"PO-{year}-{sequence:04d}"
    
    @property
    def remaining_balance(self):
        return self.total_amount - self.paid_amount
    
    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"
    
    class Meta:
        ordering = ['-order_date']
        app_label = 'purchases'

class PurchaseOrderItem(models.Model):
    """Items in purchase order"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product.name} x {self.quantity}"
    
    class Meta:
        ordering = ['id']
        app_label = 'purchases'

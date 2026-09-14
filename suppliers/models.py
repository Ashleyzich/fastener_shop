from django.db import models
from core.models import TimeStampedModel

class Supplier(TimeStampedModel):
    """Supplier model"""
    name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    
    # Payment terms
    payment_terms = models.CharField(max_length=100, blank=True)
    
    # Account balance
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    
    @property
    def outstanding_balance(self):
        """Calculate amount owed to supplier"""
        from purchases.models import PurchaseOrder
        total_ordered = PurchaseOrder.objects.filter(
            supplier=self,
            status__in=['PENDING', 'PARTIALLY_PAID']
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0
        
        total_paid = PurchaseOrder.objects.filter(
            supplier=self,
            status__in=['PAID', 'PARTIALLY_PAID']
        ).aggregate(total=models.Sum('paid_amount'))['total'] or 0
        
        return self.opening_balance + total_ordered - total_paid
    
    def __str__(self):
        return self.company_name or self.name
    
    class Meta:
        ordering = ['name']
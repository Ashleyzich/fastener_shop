from django.db import models
from core.models import TimeStampedModel
from django.core.validators import MinValueValidator

class Customer(TimeStampedModel):
    """Customer model for both walk-in and account customers"""
    CUSTOMER_TYPES = [
        ('WALK_IN', 'Walk-in Customer'),
        ('COMPANY', 'Company'),
        ('INDIVIDUAL', 'Individual'),
        ('CONTRACTOR', 'Contractor'),
    ]
    
    name = models.CharField(max_length=200)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='WALK_IN')
    company_name = models.CharField(max_length=200, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credit_terms = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    @property
    def outstanding_balance(self):
        """Calculate current outstanding balance"""
        from sales.models import Sale
        total_invoiced = Sale.objects.filter(
            customer=self, 
            status__in=['PENDING', 'PARTIALLY_PAID']
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0
        
        total_paid = Sale.objects.filter(
            customer=self,
            status__in=['PAID', 'PARTIALLY_PAID']
        ).aggregate(total=models.Sum('paid_amount'))['total'] or 0
        
        return self.opening_balance + total_invoiced - total_paid
    
    def __str__(self):
        if self.customer_type == 'WALK_IN':
            return "Walk-in Customer"
        elif self.customer_type == 'COMPANY' and self.company_name:
            return self.company_name
        return self.name
    
    class Meta:
        ordering = ['name']
        app_label = 'customers'

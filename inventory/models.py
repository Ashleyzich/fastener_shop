from django.db import models
from core.models import TimeStampedModel, UnitOfMeasure, Location
from django.core.validators import MinValueValidator
import uuid

class Category(models.Model):
    """Product categories"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        app_label = 'inventory' 

class ProductType(models.Model):
    """Specific product types within categories"""
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='product_types')
    code = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    class Meta:
        unique_together = ['name', 'category']
        ordering = ['name']
        app_label = 'inventory' 

class Material(models.Model):
    """Material specification"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        app_label = 'inventory' 

class Finish(models.Model):
    """Surface finish types"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Finishes"
        ordering = ['name']
        app_label = 'inventory' 

class Grade(models.Model):
    """Material grades"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        app_label = 'inventory' 

class ThreadType(models.Model):
    """Thread specifications"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Product(TimeStampedModel):
    """Main product model with all specifications"""
    
    # Identification
    sku = models.CharField(max_length=50, unique=True, editable=False)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Classification
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT, related_name='products', null=True, blank=True)
    
    # Specifications
    diameter = models.CharField(max_length=20, blank=True, null=True)  # M6, M8, M10, etc.
    length = models.CharField(max_length=20, blank=True, null=True)   # 50mm, 100mm, etc.
    width = models.CharField(max_length=20, blank=True, null=True)    # For U-bolts, washers
    thread_type = models.ForeignKey(ThreadType, on_delete=models.PROTECT, null=True, blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, null=True, blank=True)
    material = models.ForeignKey(Material, on_delete=models.PROTECT, null=True, blank=True)
    finish = models.ForeignKey(Finish, on_delete=models.PROTECT, null=True, blank=True)
    
    # Stock management
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=20)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, default=1)
    
    # Pricing
    buying_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.generate_sku()
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)
    
    def generate_sku(self):
        """Generate a unique SKU based on product attributes"""
        prefix = self.category.code[:3].upper() if self.category else 'GEN'
        diameter = self.diameter.replace('M', '') if self.diameter else 'XX'
        length = self.length.replace('mm', '') if self.length else 'XXX'
        return f"{prefix}-{diameter}-{length}-{uuid.uuid4().hex[:4].upper()}"
    
    def generate_barcode(self):
        """Generate a unique barcode"""
        return f"FS{uuid.uuid4().hex[:10].upper()}"
    
    def get_full_name(self):
        """Generate full product name with specifications"""
        parts = [self.name]
        if self.diameter:
            parts.append(self.diameter)
        if self.length:
            parts.append(f"× {self.length}")
        if self.grade:
            parts.append(f"Grade {self.grade.name}")
        if self.material:
            parts.append(self.material.name)
        if self.finish:
            parts.append(self.finish.name)
        return " | ".join(parts)
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold
    
    @property
    def stock_value(self):
        return self.quantity * self.buying_price
    
    def __str__(self):
        return self.get_full_name()
    
    class Meta:
        ordering = ['category', 'name', 'diameter', 'length']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['name']),
            models.Index(fields=['diameter']),
            models.Index(fields=['category']),
        ]

class ProductPrice(TimeStampedModel):
    """Different price tiers for products"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prices')
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)  # 1, 10, 100 pieces
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} {self.unit.code} - {self.price}"
    
    class Meta:
        unique_together = ['product', 'unit', 'quantity']
        ordering = ['product', 'quantity']

class StockMovement(TimeStampedModel):
    """Track all stock movements"""
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
        ('RETURN', 'Return'),
        ('DAMAGE', 'Damaged'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"
    
    class Meta:
        ordering = ['-created_at']
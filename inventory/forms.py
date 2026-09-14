from django import forms
from .models import Product, Category, StockMovement
from core.models import UnitOfMeasure, Location

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'product_type',
            'diameter', 'length', 'width', 'thread_type', 'grade',
            'material', 'finish', 'quantity', 'low_stock_threshold',
            'location', 'unit', 'buying_price', 'selling_price',
            'is_active', 'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'product_type': forms.Select(attrs={'class': 'form-select'}),
            'diameter': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'M6, M8, M10, M12, etc.'}),
            'length': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10mm, 20mm, 50mm, etc.'}),
            'width': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Width if applicable'}),
            'thread_type': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'material': forms.Select(attrs={'class': 'form-select'}),
            'finish': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'buying_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class StockAdjustmentForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    adjustment_type = forms.ChoiceField(
        choices=[('ADD', 'Add Stock'), ('REMOVE', 'Remove Stock')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.DecimalField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
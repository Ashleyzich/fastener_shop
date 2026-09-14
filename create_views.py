import os

# Create accounts/views.py
accounts_views = '''from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def profile(request):
    """User profile view"""
    context = {
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)
'''

# Create inventory/views.py
inventory_views = '''from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Product, Category, StockMovement
from core.models import UnitOfMeasure, Location

@login_required
def product_list(request):
    """List all products with search"""
    products = Product.objects.filter(is_active=True)
    search_query = request.GET.get('search', '')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(diameter__icontains=search_query) |
            Q(length__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'search_query': search_query,
        'categories': Category.objects.all(),
        'locations': Location.objects.all(),
    }
    return render(request, 'inventory/product_list.html', context)

@login_required
def product_detail(request, pk):
    """Product detail view"""
    product = get_object_or_404(Product, pk=pk)
    stock_movements = product.stock_movements.all()[:20]
    
    context = {
        'product': product,
        'stock_movements': stock_movements,
    }
    return render(request, 'inventory/product_detail.html', context)

@login_required
def product_create(request):
    """Create new product - placeholder"""
    messages.info(request, 'Product creation form coming soon.')
    return redirect('product_list')

@login_required
def product_update(request, pk):
    """Update product - placeholder"""
    messages.info(request, 'Product update form coming soon.')
    return redirect('product_detail', pk=pk)

@login_required
def product_delete(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.is_active = False
        product.save()
        messages.success(request, f'Product "{product.name}" deleted.')
        return redirect('product_list')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})

@login_required
def category_list(request):
    """List categories"""
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})

@login_required
def location_list(request):
    """List locations"""
    locations = Location.objects.all()
    return render(request, 'inventory/location_list.html', {'locations': locations})

@login_required
def stock_adjustment(request):
    """Stock adjustment - placeholder"""
    products = Product.objects.filter(is_active=True)
    return render(request, 'inventory/stock_adjustment.html', {'products': products})

@login_required
def product_search_api(request):
    """API endpoint for product search"""
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(sku__icontains=query) |
        Q(diameter__icontains=query) |
        Q(length__icontains=query)
    )[:20]
    
    data = [{
        'id': p.id,
        'name': p.name,
        'full_name': p.get_full_name(),
        'sku': p.sku,
        'price': float(p.selling_price),
        'quantity': float(p.quantity),
        'location': p.location.name if p.location else 'N/A',
        'diameter': p.diameter,
        'length': p.length,
    } for p in products]
    
    return JsonResponse({'products': data})
'''

# Create sales/views.py
sales_views = '''from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Sale, SaleItem

@login_required
def sale_list(request):
    """List all sales"""
    sales = Sale.objects.all().order_by('-created_at')[:100]
    return render(request, 'sales/sale_list.html', {'sales': sales})

@login_required
def pos(request):
    """Point of Sale - basic version"""
    return render(request, 'sales/pos.html')

@login_required
def create_sale(request):
    """Create sale - placeholder"""
    messages.info(request, 'Use POS for sales.')
    return redirect('pos')

@login_required
def sale_detail(request, pk):
    """Sale detail"""
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/sale_detail.html', {'sale': sale})

@login_required
def add_to_cart(request):
    """Add to cart - placeholder"""
    return JsonResponse({'success': False, 'message': 'Coming soon'})

@login_required
def remove_from_cart(request):
    """Remove from cart - placeholder"""
    return JsonResponse({'success': False, 'message': 'Coming soon'})

@login_required
def update_cart_item(request):
    """Update cart - placeholder"""
    return JsonResponse({'success': False, 'message': 'Coming soon'})

@login_required
def complete_sale(request):
    """Complete sale - placeholder"""
    return JsonResponse({'success': False, 'message': 'Coming soon'})

@login_required
def cancel_sale(request):
    """Cancel sale - placeholder"""
    return JsonResponse({'success': False, 'message': 'Coming soon'})
'''

# Create customers/views.py
customers_views = '''from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Customer

@login_required
def customer_list(request):
    """List customers"""
    customers = Customer.objects.all()
    return render(request, 'customers/customer_list.html', {'customers': customers})

@login_required
def customer_create(request):
    """Create customer - placeholder"""
    messages.info(request, 'Customer creation coming soon.')
    return redirect('customer_list')

@login_required
def customer_detail(request, pk):
    """Customer detail"""
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'customers/customer_detail.html', {'customer': customer})

@login_required
def customer_update(request, pk):
    """Update customer - placeholder"""
    messages.info(request, 'Customer update coming soon.')
    return redirect('customer_detail', pk=pk)
'''

# Create suppliers/views.py
suppliers_views = '''from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Supplier

@login_required
def supplier_list(request):
    """List suppliers"""
    suppliers = Supplier.objects.all()
    return render(request, 'suppliers/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_create(request):
    """Create supplier - placeholder"""
    messages.info(request, 'Supplier creation coming soon.')
    return redirect('supplier_list')

@login_required
def supplier_detail(request, pk):
    """Supplier detail"""
    supplier = get_object_or_404(Supplier, pk=pk)
    return render(request, 'suppliers/supplier_detail.html', {'supplier': supplier})

@login_required
def supplier_update(request, pk):
    """Update supplier - placeholder"""
    messages.info(request, 'Supplier update coming soon.')
    return redirect('supplier_detail', pk=pk)
'''

# Create purchases/views.py
purchases_views = '''from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PurchaseOrder

@login_required
def purchase_list(request):
    """List purchase orders"""
    purchases = PurchaseOrder.objects.all().order_by('-order_date')[:100]
    return render(request, 'purchases/purchase_list.html', {'purchases': purchases})

@login_required
def create_purchase(request):
    """Create purchase - placeholder"""
    messages.info(request, 'Purchase creation coming soon.')
    return redirect('purchase_list')

@login_required
def purchase_detail(request, pk):
    """Purchase detail"""
    purchase = get_object_or_404(PurchaseOrder, pk=pk)
    return render(request, 'purchases/purchase_detail.html', {'purchase': purchase})
'''

# Create reports/views.py
reports_views = '''from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def sales_report(request):
    """Sales report"""
    return render(request, 'reports/sales_report.html')

@login_required
def inventory_report(request):
    """Inventory report"""
    return render(request, 'reports/inventory_report.html')

@login_required
def profit_report(request):
    """Profit report"""
    return render(request, 'reports/profit_report.html')
'''

# Write all files
files = {
    'accounts/views.py': accounts_views,
    'inventory/views.py': inventory_views,
    'sales/views.py': sales_views,
    'customers/views.py': customers_views,
    'suppliers/views.py': suppliers_views,
    'purchases/views.py': purchases_views,
    'reports/views.py': reports_views,
}

for filepath, content in files.items():
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Created {filepath}")

print("\nAll view files created successfully!")
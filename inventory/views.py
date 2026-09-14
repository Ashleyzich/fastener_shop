from accounts.permissions import manager_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F, Count
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from decimal import Decimal
from .models import Product, Category, StockMovement, Material, Finish, Grade
from core.models import UnitOfMeasure, Location

@login_required
def product_list(request):
    """List all products with search and filters"""
    products = Product.objects.filter(is_active=True).select_related(
        'category', 'material', 'finish', 'grade', 'location'
    )
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(diameter__icontains=search_query) |
            Q(length__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__name__icontains=search_query)
        )
    
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    diameter = request.GET.get('diameter', '')
    if diameter:
        products = products.filter(diameter=diameter)
    
    grade_id = request.GET.get('grade', '')
    if grade_id:
        products = products.filter(grade_id=grade_id)
    
    material_id = request.GET.get('material', '')
    if material_id:
        products = products.filter(material_id=material_id)
    
    finish_id = request.GET.get('finish', '')
    if finish_id:
        products = products.filter(finish_id=finish_id)
    
    location_id = request.GET.get('location', '')
    if location_id:
        products = products.filter(location_id=location_id)
    
    low_stock_only = request.GET.get('low_stock', '')
    if low_stock_only:
        products = products.filter(quantity__lte=F('low_stock_threshold'))
    
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        products = products.order_by('name', 'diameter', 'length')
    elif sort_by == 'quantity':
        products = products.order_by('quantity')
    elif sort_by == '-quantity':
        products = products.order_by('-quantity')
    elif sort_by == 'price_low':
        products = products.order_by('selling_price')
    elif sort_by == 'price_high':
        products = products.order_by('-selling_price')
    elif sort_by == 'recent':
        products = products.order_by('-updated_at')
    
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    grades = Grade.objects.all()
    materials = Material.objects.all()
    finishes = Finish.objects.all()
    locations = Location.objects.all()
    diameters = Product.objects.exclude(
        diameter__isnull=True
    ).exclude(
        diameter=''
    ).values_list('diameter', flat=True).distinct().order_by('diameter')
    
    total_products = products.count()
    total_stock_value = products.aggregate(
        total=Sum(F('quantity') * F('buying_price'))
    )['total'] or 0
    
    context = {
        'products': page_obj,
        'search_query': search_query,
        'categories': categories,
        'grades': grades,
        'materials': materials,
        'finishes': finishes,
        'locations': locations,
        'diameters': diameters,
        'selected_category': category_id,
        'selected_diameter': diameter,
        'selected_grade': grade_id,
        'selected_material': material_id,
        'selected_finish': finish_id,
        'selected_location': location_id,
        'sort_by': sort_by,
        'total_products': total_products,
        'total_stock_value': total_stock_value,
    }
    
    return render(request, 'inventory/product_list.html', context)

@login_required
def product_detail(request, pk):
    """Product detail view"""
    product = get_object_or_404(Product, pk=pk)
    stock_movements = product.stock_movements.all()[:20]
    prices = product.prices.all()
    
    context = {
        'product': product,
        'stock_movements': stock_movements,
        'prices': prices,
    }
    return render(request, 'inventory/product_detail.html', context)

@login_required
def product_create(request):
    """Create new product"""
    messages.info(request, 'Product creation form coming soon. Use Admin panel for now.')
    return redirect('admin:inventory_product_add')

@login_required
def product_update(request, pk):
    """Update product"""
    messages.info(request, 'Product update form coming soon. Use Admin panel for now.')
    return redirect('admin:inventory_product_change', pk)

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
    categories = Category.objects.annotate(
        product_count=Count('products')
    )
    return render(request, 'inventory/category_list.html', {'categories': categories})

@login_required
def location_list(request):
    """List locations"""
    locations = Location.objects.annotate(
        product_count=Count('product'),
        total_quantity=Sum('product__quantity'),
        stock_value=Sum(F('product__quantity') * F('product__buying_price'))
    )
    return render(request, 'inventory/location_list.html', {'locations': locations})

@manager_required
def stock_adjustment(request):
    """Stock adjustment view with form"""
    products = Product.objects.filter(is_active=True).select_related('category', 'location')
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(diameter__icontains=search_query)
        )
    
    recent_adjustments = StockMovement.objects.filter(
        movement_type__in=['IN', 'OUT', 'ADJUST']
    ).select_related('product', 'created_by').order_by('-created_at')[:20]
    
    context = {
        'products': products[:100],
        'recent_adjustments': recent_adjustments,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/stock_adjustment.html', context)

@manager_required
@transaction.atomic
def process_stock_adjustment(request):
    """Process stock adjustment"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        adjustment_type = request.POST.get('adjustment_type')
        quantity = Decimal(request.POST.get('quantity', '0'))
        reason = request.POST.get('reason', '')
        
        if not product_id or quantity <= 0:
            messages.error(request, 'Please provide valid product and quantity.')
            return redirect('stock_adjustment')
        
        product = get_object_or_404(Product, pk=product_id)
        
        if adjustment_type == 'ADD':
            product.quantity += quantity
            movement_type = 'IN'
            message = f'Added {quantity} units to {product.name}.'
        elif adjustment_type == 'REMOVE':
            if product.quantity < quantity:
                messages.error(request, f'Insufficient stock. Only {product.quantity} available.')
                return redirect('stock_adjustment')
            product.quantity -= quantity
            movement_type = 'OUT'
            message = f'Removed {quantity} units from {product.name}.'
        elif adjustment_type == 'SET':
            product.quantity = quantity
            movement_type = 'ADJUST'
            message = f'Set {product.name} stock to {quantity} units.'
        else:
            messages.error(request, 'Invalid adjustment type.')
            return redirect('stock_adjustment')
        
        product.save()
        
        StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            reference='Manual Adjustment',
            notes=reason or 'Stock adjustment',
            created_by=request.user
        )
        
        messages.success(request, message)
        return redirect('stock_adjustment')
    
    return redirect('stock_adjustment')

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

from accounts.permissions import manager_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from .models import PurchaseOrder, PurchaseOrderItem
from suppliers.models import Supplier
from inventory.models import Product, StockMovement

@login_required
def purchase_list(request):
    """List all purchase orders"""
    purchases = PurchaseOrder.objects.select_related('supplier').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        purchases = purchases.filter(
            Q(po_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query) |
            Q(supplier__company_name__icontains=search_query)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        purchases = purchases.filter(status=status)
    
    # Order by date
    purchases = purchases.order_by('-order_date')
    
    # Statistics
    total_orders = PurchaseOrder.objects.count()
    pending_orders = PurchaseOrder.objects.filter(status='ORDERED').count()
    received_orders = PurchaseOrder.objects.filter(status='RECEIVED').count()
    total_spent = PurchaseOrder.objects.filter(status='RECEIVED').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    context = {
        'purchases': purchases[:100],
        'search_query': search_query,
        'selected_status': status,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'received_orders': received_orders,
        'total_spent': total_spent,
    }
    
    return render(request, 'purchases/purchase_list.html', context)

@login_required
def purchase_detail(request, pk):
    """Purchase order detail"""
    purchase = get_object_or_404(PurchaseOrder, pk=pk)
    items = purchase.items.all()
    
    context = {
        'purchase': purchase,
        'items': items,
    }
    
    return render(request, 'purchases/purchase_detail.html', context)

@login_required
def create_purchase(request):
    """Create new purchase order"""
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        notes = request.POST.get('notes', '')
        expected_date = request.POST.get('expected_date', '')
        
        if not supplier_id:
            messages.error(request, 'Please select a supplier.')
            return redirect('create_purchase')
        
        supplier = get_object_or_404(Supplier, pk=supplier_id)
        
        purchase = PurchaseOrder.objects.create(
            supplier=supplier,
            status='DRAFT',
            notes=notes,
            created_by=request.user
        )
        
        if expected_date:
            purchase.expected_date = expected_date
            purchase.save()
        
        messages.success(request, f'Purchase order {purchase.po_number} created. Add items below.')
        return redirect('purchase_detail', pk=purchase.pk)
    
    suppliers = Supplier.objects.filter(is_active=True)
    return render(request, 'purchases/purchase_form.html', {'suppliers': suppliers})

@login_required
@transaction.atomic
def add_item_to_purchase(request, pk):
    """Add item to purchase order"""
    if request.method == 'POST':
        purchase = get_object_or_404(PurchaseOrder, pk=pk)
        
        if purchase.status not in ['DRAFT', 'ORDERED']:
            messages.error(request, 'Cannot add items to a received or cancelled order.')
            return redirect('purchase_detail', pk=pk)
        
        product_id = request.POST.get('product')
        quantity = Decimal(request.POST.get('quantity', '0'))
        unit_price = Decimal(request.POST.get('unit_price', '0'))
        
        if not product_id or quantity <= 0 or unit_price < 0:
            messages.error(request, 'Please provide valid product, quantity, and price.')
            return redirect('purchase_detail', pk=pk)
        
        product = get_object_or_404(Product, pk=product_id)
        
        PurchaseOrderItem.objects.create(
            purchase_order=purchase,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            total_price=quantity * unit_price
        )
        
        # Update purchase total
        update_purchase_total(purchase)
        
        messages.success(request, f'Added {quantity} x {product.name} to {purchase.po_number}.')
        return redirect('purchase_detail', pk=pk)
    
    products = Product.objects.filter(is_active=True)
    return render(request, 'purchases/add_item.html', {
        'purchase': get_object_or_404(PurchaseOrder, pk=pk),
        'products': products
    })

@login_required
@transaction.atomic
def remove_item_from_purchase(request, pk):
    """Remove item from purchase order"""
    if request.method == 'POST':
        item = get_object_or_404(PurchaseOrderItem, pk=pk)
        purchase = item.purchase_order
        
        if purchase.status not in ['DRAFT', 'ORDERED']:
            messages.error(request, 'Cannot remove items from a received or cancelled order.')
            return redirect('purchase_detail', pk=purchase.pk)
        
        item.delete()
        update_purchase_total(purchase)
        
        messages.success(request, 'Item removed from purchase order.')
        return redirect('purchase_detail', pk=purchase.pk)
    
    return redirect('purchase_list')

@login_required
@transaction.atomic
def order_purchase(request, pk):
    """Mark purchase order as ordered"""
    purchase = get_object_or_404(PurchaseOrder, pk=pk)
    
    if purchase.items.count() == 0:
        messages.error(request, 'Cannot order an empty purchase order.')
        return redirect('purchase_detail', pk=pk)
    
    purchase.status = 'ORDERED'
    purchase.save()
    
    messages.success(request, f'Purchase order {purchase.po_number} marked as ordered.')
    return redirect('purchase_detail', pk=pk)

@manager_required
@transaction.atomic
def receive_purchase(request, pk):
    """Receive stock from purchase order"""
    purchase = get_object_or_404(PurchaseOrder, pk=pk)
    
    if purchase.status == 'RECEIVED':
        messages.info(request, 'This purchase order has already been received.')
        return redirect('purchase_detail', pk=pk)
    
    if purchase.status != 'ORDERED':
        messages.error(request, 'Only ordered purchase orders can be received.')
        return redirect('purchase_detail', pk=pk)
    
    # Update stock for each item
    for item in purchase.items.all():
        item.product.quantity += item.quantity
        item.product.buying_price = item.unit_price  # Update buying price
        item.product.save()
        
        # Create stock movement
        StockMovement.objects.create(
            product=item.product,
            movement_type='IN',
            quantity=item.quantity,
            reference=f'PO {purchase.po_number}',
            notes='Stock received from purchase order',
            created_by=request.user
        )
    
    purchase.status = 'RECEIVED'
    purchase.received_date = timezone.now().date()
    purchase.save()
    
    messages.success(request, f'Stock received from {purchase.po_number}. Inventory updated.')
    return redirect('purchase_detail', pk=pk)

@login_required
@transaction.atomic
def cancel_purchase(request, pk):
    """Cancel purchase order"""
    purchase = get_object_or_404(PurchaseOrder, pk=pk)
    
    if purchase.status == 'RECEIVED':
        messages.error(request, 'Cannot cancel a received purchase order.')
        return redirect('purchase_detail', pk=pk)
    
    purchase.status = 'CANCELLED'
    purchase.save()
    
    messages.success(request, f'Purchase order {purchase.po_number} cancelled.')
    return redirect('purchase_detail', pk=pk)

def update_purchase_total(purchase):
    """Update purchase order total"""
    items = purchase.items.all()
    subtotal = sum(item.total_price for item in items)
    purchase.subtotal = subtotal
    purchase.total_amount = subtotal + purchase.tax + purchase.shipping_cost
    purchase.save()

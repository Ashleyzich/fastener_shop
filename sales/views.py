from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.db.models import Q, Sum, F

from .models import Sale, SaleItem, Payment
from inventory.models import Product, StockMovement
from customers.models import Customer

@login_required
def sale_list(request):
    """List all sales"""
    sales = Sale.objects.filter(status='COMPLETED').order_by('-created_at')[:100]
    return render(request, 'sales/sale_list.html', {'sales': sales})

@login_required
def sale_detail(request, pk):
    """Sale detail view"""
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.all()
    payments = sale.payments.all()
    
    context = {
        'sale': sale,
        'items': items,
        'payments': payments,
    }
    return render(request, 'sales/sale_detail.html', context)

@login_required
def create_sale(request):
    """Redirect to POS"""
    return redirect('pos')

@login_required
def pos(request):
    """Point of Sale view"""
    walk_in_customer, created = Customer.objects.get_or_create(
        customer_type='WALK_IN',
        defaults={'name': 'Walk-in Customer'}
    )
    
    sale_id = request.session.get('current_sale_id')
    current_sale = None
    sale_items = []
    
    if sale_id:
        current_sale = Sale.objects.filter(id=sale_id, status='DRAFT').first()
        if current_sale:
            sale_items = current_sale.items.all()
    
    recent_sales = Sale.objects.filter(status='COMPLETED').order_by('-created_at')[:10]
    customers = Customer.objects.filter(is_active=True).exclude(customer_type='WALK_IN')
    recent_products = Product.objects.filter(is_active=True).order_by('-updated_at')[:20]
    
    context = {
        'walk_in_customer': walk_in_customer,
        'current_sale': current_sale,
        'sale_items': sale_items,
        'recent_sales': recent_sales,
        'customers': customers,
        'recent_products': recent_products,
    }
    
    return render(request, 'sales/pos.html', context)

@login_required
@transaction.atomic
def add_to_cart(request):
    """Add product to current sale"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = Decimal(request.POST.get('quantity', '1'))
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        if product.quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Insufficient stock. Only {product.quantity} available.'
            })
        
        sale_id = request.session.get('current_sale_id')
        sale = None
        
        if sale_id:
            sale = Sale.objects.filter(id=sale_id, status='DRAFT').first()
        
        if not sale:
            walk_in_customer, created = Customer.objects.get_or_create(
                customer_type='WALK_IN',
                defaults={'name': 'Walk-in Customer'}
            )
            
            sale = Sale.objects.create(
                customer=walk_in_customer,
                sale_type='CASH',
                status='DRAFT',
                salesperson=request.user
            )
            request.session['current_sale_id'] = sale.id
        
        existing_item = sale.items.filter(product=product).first()
        
        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if product.quantity < new_quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Insufficient stock. Only {product.quantity} available.'
                })
            
            existing_item.quantity = new_quantity
            existing_item.total_price = new_quantity * existing_item.unit_price
            existing_item.save()
        else:
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=product.selling_price,
                total_price=quantity * product.selling_price
            )
        
        update_sale_totals(sale)
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart.',
            'sale_id': sale.id,
            'item_count': sale.items.count(),
            'total': float(sale.total_amount)
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@transaction.atomic
def remove_from_cart(request):
    """Remove item from cart"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        item = get_object_or_404(SaleItem, id=item_id)
        sale = item.sale
        
        if sale.status != 'DRAFT':
            return JsonResponse({'success': False, 'message': 'Cannot modify completed sale.'})
        
        item.delete()
        update_sale_totals(sale)
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed.',
            'item_count': sale.items.count(),
            'total': float(sale.total_amount)
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@transaction.atomic
def update_cart_item(request):
    """Update item quantity"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = Decimal(request.POST.get('quantity', '1'))
        
        item = get_object_or_404(SaleItem, id=item_id)
        sale = item.sale
        
        if sale.status != 'DRAFT':
            return JsonResponse({'success': False, 'message': 'Cannot modify completed sale.'})
        
        if item.product.quantity < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Insufficient stock. Only {item.product.quantity} available.'
            })
        
        item.quantity = quantity
        item.total_price = quantity * item.unit_price
        item.save()
        
        update_sale_totals(sale)
        
        return JsonResponse({
            'success': True,
            'item_total': float(item.total_price),
            'total': float(sale.total_amount)
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@transaction.atomic
def complete_sale(request):
    """Complete the sale with credit support"""
    if request.method == 'POST':
        sale_id = request.session.get('current_sale_id')
        if not sale_id:
            return JsonResponse({'success': False, 'message': 'No active sale found.'})
        
        sale = get_object_or_404(Sale, id=sale_id, status='DRAFT')
        
        if not sale.items.exists():
            return JsonResponse({'success': False, 'message': 'Cannot complete empty sale.'})
        
        customer_id = request.POST.get('customer_id')
        if customer_id:
            sale.customer_id = customer_id
        
        payment_method = request.POST.get('payment_method', 'CASH')
        sale.payment_method = payment_method
        
        if payment_method == 'CREDIT':
            sale.sale_type = 'CREDIT'
            sale.status = 'PENDING'
            sale.paid_amount = Decimal('0')
            sale.save()
            
            Payment.objects.create(
                sale=sale,
                amount=Decimal('0'),
                payment_method='CREDIT',
                received_by=request.user,
                notes='Credit sale - full amount pending'
            )
        else:
            sale.sale_type = 'CASH'
            sale.status = 'COMPLETED'
            sale.paid_amount = sale.total_amount
            sale.save()
            
            Payment.objects.create(
                sale=sale,
                amount=sale.total_amount,
                payment_method=payment_method,
                received_by=request.user
            )
        
        for item in sale.items.all():
            item.product.quantity -= item.quantity
            item.product.save()
            
            StockMovement.objects.create(
                product=item.product,
                movement_type='OUT',
                quantity=item.quantity,
                reference=f'Sale {sale.invoice_number}',
                notes='Sale',
                created_by=request.user
            )
        
        del request.session['current_sale_id']
        
        return JsonResponse({
            'success': True,
            'message': 'Sale completed successfully.',
            'sale_id': sale.id,
            'invoice_number': sale.invoice_number,
            'total': float(sale.total_amount),
            'status': sale.status,
            'paid': float(sale.paid_amount),
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@transaction.atomic
def cancel_sale(request):
    """Cancel current sale"""
    if request.method == 'POST':
        sale_id = request.session.get('current_sale_id')
        if sale_id:
            sale = Sale.objects.filter(id=sale_id, status='DRAFT').first()
            if sale:
                sale.status = 'CANCELLED'
                sale.save()
                del request.session['current_sale_id']
                return JsonResponse({'success': True, 'message': 'Sale cancelled.'})
    
    return JsonResponse({'success': False, 'message': 'No active sale found.'})

def update_sale_totals(sale):
    """Update sale totals"""
    items = sale.items.all()
    subtotal = sum(item.total_price for item in items)
    discount = sale.discount or Decimal('0')
    tax = Decimal('0')
    total = subtotal - discount + tax
    
    sale.subtotal = subtotal
    sale.tax = tax
    sale.total_amount = total
    sale.save()

# Payment Views
@login_required
def payment_list(request):
    """List all payments"""
    payments = Payment.objects.select_related('sale', 'sale__customer', 'received_by').order_by('-created_at')[:100]
    
    total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    today_payments = Payment.objects.filter(
        created_at__date=timezone.now().date()
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'payments': payments,
        'total_payments': total_payments,
        'today_payments': today_payments,
    }
    
    return render(request, 'sales/payment_list.html', context)

@login_required
def record_payment(request):
    """Record a payment"""
    customers_with_balance = []
    for customer in Customer.objects.filter(is_active=True):
        if customer.outstanding_balance > 0:
            customers_with_balance.append(customer)
    
    if request.method == 'POST':
        sale_id = request.POST.get('sale_id')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'CASH')
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')
        
        if not sale_id or not amount:
            messages.error(request, 'Sale and amount are required.')
            return redirect('record_payment')
        
        sale = get_object_or_404(Sale, pk=sale_id)
        amount = Decimal(amount)
        
        if amount <= 0:
            messages.error(request, 'Amount must be greater than zero.')
            return redirect('record_payment')
        
        remaining = sale.total_amount - sale.paid_amount
        if amount > remaining:
            messages.error(request, f'Amount exceeds remaining balance of ${remaining}.')
            return redirect('record_payment')
        
        Payment.objects.create(
            sale=sale,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            received_by=request.user,
            notes=notes
        )
        
        sale.paid_amount += amount
        if sale.paid_amount >= sale.total_amount:
            sale.status = 'COMPLETED'
        else:
            sale.status = 'PARTIALLY_PAID'
        sale.save()
        
        messages.success(request, f'Payment of ${amount} recorded.')
        return redirect('payment_list')
    
    credit_sales = Sale.objects.filter(
        status__in=['PENDING', 'PARTIALLY_PAID']
    ).select_related('customer').order_by('-created_at')
    
    context = {
        'customers_with_balance': customers_with_balance,
        'credit_sales': credit_sales,
    }
    
    return render(request, 'sales/record_payment.html', context)

@login_required
def get_sale_balance(request, sale_id):
    """API for sale balance"""
    sale = get_object_or_404(Sale, pk=sale_id)
    remaining = sale.total_amount - sale.paid_amount
    return JsonResponse({
        'invoice': sale.invoice_number,
        'total': float(sale.total_amount),
        'paid': float(sale.paid_amount),
        'remaining': float(remaining),
        'customer': sale.customer.name,
    })

@login_required
def print_receipt(request, pk):
    """Print receipt for a sale"""
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.all()
    
    context = {
        'sale': sale,
        'items': items,
    }
    
    return render(request, 'sales/receipt.html', context)

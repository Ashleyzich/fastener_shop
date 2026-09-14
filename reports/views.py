from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal

from sales.models import Sale, SaleItem
from inventory.models import Product, Category, StockMovement
from customers.models import Customer
from suppliers.models import Supplier
from purchases.models import PurchaseOrder

@login_required
def sales_report(request):
    """Sales report with date range filtering"""
    today = timezone.now().date()
    
    report_type = request.GET.get('report_type', 'this_month')
    
    if report_type == 'today':
        start_date = today
        end_date = today
    elif report_type == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif report_type == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif report_type == 'last_7_days':
        start_date = today - timedelta(days=7)
        end_date = today
    elif report_type == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif report_type == 'last_month':
        first_of_month = today.replace(day=1)
        start_date = (first_of_month - timedelta(days=1)).replace(day=1)
        end_date = first_of_month - timedelta(days=1)
    elif report_type == 'all':
        start_date = None
        end_date = None
    elif report_type == 'custom':
        start_str = request.GET.get('start_date', '')
        end_str = request.GET.get('end_date', '')
        if start_str:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        else:
            start_date = today.replace(day=1)
        if end_str:
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        else:
            end_date = today
    else:
        start_date = today.replace(day=1)
        end_date = today
    
    sales_query = Sale.objects.filter(status='COMPLETED')
    
    if start_date and end_date:
        sales_query = sales_query.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
    
    total_sales = sales_query.count()
    total_revenue = sales_query.aggregate(total=Sum('total_amount'))['total'] or 0
    total_items = SaleItem.objects.filter(sale__in=sales_query).aggregate(
        total=Sum('quantity')
    )['total'] or 0
    avg_sale = total_revenue / total_sales if total_sales > 0 else 0
    
    payment_breakdown = sales_query.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('-total')
    
    top_products = SaleItem.objects.filter(sale__in=sales_query).values(
        'product__name',
        'product__diameter',
        'product__length'
    ).annotate(
        quantity=Sum('quantity'),
        revenue=Sum('total_price')
    ).order_by('-revenue')[:10]
    
    top_customers = sales_query.values('customer__name').annotate(
        purchases=Count('id'),
        total=Sum('total_amount')
    ).order_by('-total')[:10]
    
    recent_sales = sales_query.order_by('-created_at')[:50]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'report_type': report_type,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_items': total_items,
        'avg_sale': avg_sale,
        'payment_breakdown': payment_breakdown,
        'top_products': top_products,
        'top_customers': top_customers,
        'recent_sales': recent_sales,
        'has_data': total_sales > 0,
    }
    
    return render(request, 'reports/sales_report.html', context)

@login_required
def inventory_report(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'location')
    total_products = products.count()
    total_stock_value = products.aggregate(total=Sum(F('quantity') * F('buying_price')))['total'] or 0
    total_retail_value = products.aggregate(total=Sum(F('quantity') * F('selling_price')))['total'] or 0
    low_stock = products.filter(quantity__lte=F('low_stock_threshold'))
    out_of_stock = products.filter(quantity=0)
    
    category_breakdown = products.values('category__name').annotate(
        count=Count('id'),
        stock_value=Sum(F('quantity') * F('buying_price')),
        retail_value=Sum(F('quantity') * F('selling_price'))
    ).order_by('-stock_value')
    
    location_breakdown = products.values('location__name').annotate(
        count=Count('id'),
        stock_value=Sum(F('quantity') * F('buying_price'))
    ).order_by('-stock_value')
    
    recent_movements = StockMovement.objects.select_related('product', 'created_by').order_by('-created_at')[:50]
    
    context = {
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'total_retail_value': total_retail_value,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'category_breakdown': category_breakdown,
        'location_breakdown': location_breakdown,
        'recent_movements': recent_movements,
    }
    
    return render(request, 'reports/inventory_report.html', context)

@login_required
def profit_report(request):
    report_type = request.GET.get('report_type', 'this_month')
    today = timezone.now().date()
    
    if report_type == 'today':
        start_date = today
        end_date = today
    elif report_type == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif report_type == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif report_type == 'last_month':
        first_of_month = today.replace(day=1)
        start_date = (first_of_month - timedelta(days=1)).replace(day=1)
        end_date = first_of_month - timedelta(days=1)
    else:
        start_date = today.replace(day=1)
        end_date = today
    
    sales = Sale.objects.filter(
        status='COMPLETED',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_cost = 0
    
    for sale in sales:
        for item in sale.items.all():
            total_cost += item.product.buying_price * item.quantity
    
    gross_profit = total_revenue - total_cost
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'report_type': report_type,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'gross_profit': gross_profit,
        'profit_margin': profit_margin,
        'total_sales': sales.count(),
        'product_profit': [],
    }
    
    return render(request, 'reports/profit_report.html', context)

@login_required
def purchase_report(request):
    today = timezone.now().date()
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    month_start = today.replace(day=1)
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = month_start
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = today
    
    purchases = PurchaseOrder.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    )
    
    total_orders = purchases.count()
    total_purchased = purchases.aggregate(total=Sum('total_amount'))['total'] or 0
    
    supplier_breakdown = purchases.values('supplier__name').annotate(
        orders=Count('id'),
        total=Sum('total_amount')
    ).order_by('-total')
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_orders': total_orders,
        'total_purchased': total_purchased,
        'supplier_breakdown': supplier_breakdown,
        'purchases': purchases[:50],
    }
    
    return render(request, 'reports/purchase_report.html', context)
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from sales.models import Sale, SaleItem
from inventory.models import Product

@login_required
def export_sales_csv(request):
    """Export sales to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Invoice', 'Customer', 'Date', 'Payment Method', 'Total'])
    
    sales = Sale.objects.filter(status='COMPLETED').order_by('-created_at')
    
    for sale in sales:
        writer.writerow([
            sale.invoice_number,
            sale.customer.name,
            sale.created_at.strftime('%Y-%m-%d %H:%M'),
            sale.payment_method,
            sale.total_amount
        ])
    
    return response

@login_required
def export_inventory_csv(request):
    """Export inventory to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['SKU', 'Name', 'Category', 'Diameter', 'Length', 'Quantity', 'Buying Price', 'Selling Price', 'Location'])
    
    products = Product.objects.filter(is_active=True).select_related('category', 'location')
    
    for product in products:
        writer.writerow([
            product.sku,
            product.name,
            product.category.name,
            product.diameter or '',
            product.length or '',
            product.quantity,
            product.buying_price,
            product.selling_price,
            product.location.name if product.location else ''
        ])
    
    return response

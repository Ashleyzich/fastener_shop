from django.shortcuts import render, redirect
from accounts.permissions import admin_required, manager_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from inventory.models import Product
from sales.models import Sale, SaleItem
from customers.models import Customer
from suppliers.models import Supplier

@login_required
def dashboard(request):
    """Main dashboard view"""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    today_sales = Sale.objects.filter(
        created_at__date=today,
        status='COMPLETED'
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    monthly_sales = Sale.objects.filter(
        created_at__date__gte=month_start,
        status='COMPLETED'
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(
        is_active=True,
        quantity__lte=F('low_stock_threshold')
    ).select_related('category', 'location')[:10]
    
    low_stock_count = Product.objects.filter(
        is_active=True,
        quantity__lte=F('low_stock_threshold')
    ).count()
    
    out_of_stock = Product.objects.filter(
        is_active=True,
        quantity=0
    ).count()
    
    stock_value = Product.objects.filter(is_active=True).aggregate(
        total=Sum(F('quantity') * F('buying_price'))
    )['total'] or 0
    
    top_products = SaleItem.objects.filter(
        sale__created_at__date__gte=month_start,
        sale__status='COMPLETED'
    ).values(
        'product__name',
        'product__diameter',
        'product__length'
    ).annotate(
        total_qty=Sum('quantity'),
        total_sales=Sum('total_price')
    ).order_by('-total_qty')[:10]
    
    recent_sales = Sale.objects.filter(
        status='COMPLETED'
    ).order_by('-created_at')[:10]
    
    total_customers = Customer.objects.filter(is_active=True).count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    
    context = {
        'today_sales': today_sales,
        'monthly_sales': monthly_sales,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'low_stock_count': low_stock_count,
        'out_of_stock': out_of_stock,
        'stock_value': stock_value,
        'top_products': top_products,
        'recent_sales': recent_sales,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
    }
    
    return render(request, 'core/dashboard.html', context)
import os
import shutil
import datetime
from django.shortcuts import render, redirect
from accounts.permissions import admin_required, manager_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, FileResponse

@admin_required
def backup_list(request):
    """List all backups"""
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    
    backups = []
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.db'):
                file_path = os.path.join(backup_dir, file)
                file_stat = os.stat(file_path)
                backups.append({
                    'name': file,
                    'size': file_stat.st_size,
                    'created': datetime.datetime.fromtimestamp(file_stat.st_mtime),
                    'path': file_path,
                })
    
    # Sort by created date (newest first)
    backups.sort(key=lambda x: x['created'], reverse=True)
    
    context = {
        'backups': backups,
    }
    
    return render(request, 'core/backup_list.html', context)

@admin_required
def create_backup(request):
    """Create a new backup"""
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backup_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_file)
    
    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        messages.success(request, f'Backup created successfully: {backup_file}')
    else:
        messages.error(request, 'Database file not found!')
    
    return redirect('backup_list')

@admin_required
def download_backup(request, filename):
    """Download a backup file"""
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, 'Backup file not found!')
        return redirect('backup_list')

@admin_required
def delete_backup(request, filename):
    """Delete a backup file"""
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        messages.success(request, f'Backup deleted: {filename}')
    else:
        messages.error(request, 'Backup file not found!')
    
    return redirect('backup_list')


def welcome(request):
    """Welcome page shown before login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/welcome.html')

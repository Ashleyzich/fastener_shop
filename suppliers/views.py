from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from .models import Supplier
from purchases.models import PurchaseOrder

@login_required
def supplier_list(request):
    """List all suppliers with search"""
    suppliers = Supplier.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(contact_person__icontains=search_query)
        )
    
    # Filter active only
    active_only = request.GET.get('active', '')
    if active_only:
        suppliers = suppliers.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(suppliers.order_by('name'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_suppliers = Supplier.objects.count()
    active_suppliers = Supplier.objects.filter(is_active=True).count()
    total_outstanding = sum(s.outstanding_balance for s in Supplier.objects.all())
    
    context = {
        'suppliers': page_obj,
        'search_query': search_query,
        'total_suppliers': total_suppliers,
        'active_suppliers': active_suppliers,
        'total_outstanding': total_outstanding,
    }
    
    return render(request, 'suppliers/supplier_list.html', context)

@login_required
def supplier_detail(request, pk):
    """Supplier detail with purchase history"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    # Get supplier's purchase orders
    purchases = PurchaseOrder.objects.filter(supplier=supplier).order_by('-order_date')
    
    # Statistics
    total_orders = purchases.count()
    total_purchased = purchases.aggregate(total=Sum('total_amount'))['total'] or 0
    recent_orders = purchases[:10]
    
    context = {
        'supplier': supplier,
        'purchases': purchases,
        'total_orders': total_orders,
        'total_purchased': total_purchased,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'suppliers/supplier_detail.html', context)

@login_required
def supplier_create(request):
    """Create new supplier"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        company_name = request.POST.get('company_name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        tax_id = request.POST.get('tax_id', '').strip()
        payment_terms = request.POST.get('payment_terms', '').strip()
        
        if not name and not company_name:
            messages.error(request, 'Name or Company Name is required.')
            return redirect('supplier_create')
        
        supplier = Supplier.objects.create(
            name=name or company_name,
            company_name=company_name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address,
            tax_id=tax_id,
            payment_terms=payment_terms,
        )
        
        messages.success(request, f'Supplier "{supplier.name}" created successfully.')
        return redirect('supplier_detail', pk=supplier.pk)
    
    return render(request, 'suppliers/supplier_form.html')

@login_required
def supplier_update(request, pk):
    """Update supplier"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier.name = request.POST.get('name', supplier.name)
        supplier.company_name = request.POST.get('company_name', supplier.company_name)
        supplier.contact_person = request.POST.get('contact_person', supplier.contact_person)
        supplier.phone = request.POST.get('phone', supplier.phone)
        supplier.email = request.POST.get('email', supplier.email)
        supplier.address = request.POST.get('address', supplier.address)
        supplier.tax_id = request.POST.get('tax_id', supplier.tax_id)
        supplier.payment_terms = request.POST.get('payment_terms', supplier.payment_terms)
        supplier.is_active = request.POST.get('is_active') == 'on'
        supplier.save()
        
        messages.success(request, f'Supplier "{supplier.name}" updated successfully.')
        return redirect('supplier_detail', pk=supplier.pk)
    
    return render(request, 'suppliers/supplier_form.html', {'supplier': supplier})

@login_required
def supplier_delete(request, pk):
    """Delete/deactivate supplier"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier.is_active = False
        supplier.save()
        messages.success(request, f'Supplier "{supplier.name}" deactivated.')
        return redirect('supplier_list')
    
    return render(request, 'suppliers/supplier_confirm_delete.html', {'supplier': supplier})

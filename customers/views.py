from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from .models import Customer
from sales.models import Sale

@login_required
def customer_list(request):
    """List all customers with search"""
    customers = Customer.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by type
    customer_type = request.GET.get('type', '')
    if customer_type:
        customers = customers.filter(customer_type=customer_type)
    
    # Sort
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'recent':
        customers = customers.order_by('-created_at')
    elif sort_by == 'balance':
        customers = sorted(customers, key=lambda c: c.outstanding_balance, reverse=True)
    else:
        customers = customers.order_by('name')
    
    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_customers = Customer.objects.count()
    total_credit = Customer.objects.filter(credit_limit__gt=0).count()
    total_outstanding = sum(c.outstanding_balance for c in Customer.objects.all())
    
    context = {
        'customers': page_obj,
        'search_query': search_query,
        'selected_type': customer_type,
        'sort_by': sort_by,
        'total_customers': total_customers,
        'total_credit': total_credit,
        'total_outstanding': total_outstanding,
    }
    
    return render(request, 'customers/customer_list.html', context)

@login_required
def customer_detail(request, pk):
    """Customer detail with purchase history"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Get customer's sales
    sales = Sale.objects.filter(customer=customer).order_by('-created_at')
    
    # Statistics
    total_purchases = sales.count()
    total_spent = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    recent_sales = sales[:10]
    
    context = {
        'customer': customer,
        'sales': sales,
        'total_purchases': total_purchases,
        'total_spent': total_spent,
        'recent_sales': recent_sales,
    }
    
    return render(request, 'customers/customer_detail.html', context)

@login_required
def customer_create(request):
    """Create new customer"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        customer_type = request.POST.get('customer_type', 'INDIVIDUAL')
        company_name = request.POST.get('company_name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        credit_limit = request.POST.get('credit_limit', '0')
        credit_terms = request.POST.get('credit_terms', '').strip()
        
        if not name:
            messages.error(request, 'Name is required.')
            return redirect('customer_create')
        
        customer = Customer.objects.create(
            name=name,
            customer_type=customer_type,
            company_name=company_name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address,
            credit_limit=credit_limit,
            credit_terms=credit_terms,
        )
        
        messages.success(request, f'Customer "{customer.name}" created successfully.')
        return redirect('customer_detail', pk=customer.pk)
    
    return render(request, 'customers/customer_form.html')

@login_required
def customer_update(request, pk):
    """Update customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.name = request.POST.get('name', customer.name)
        customer.customer_type = request.POST.get('customer_type', customer.customer_type)
        customer.company_name = request.POST.get('company_name', customer.company_name)
        customer.contact_person = request.POST.get('contact_person', customer.contact_person)
        customer.phone = request.POST.get('phone', customer.phone)
        customer.email = request.POST.get('email', customer.email)
        customer.address = request.POST.get('address', customer.address)
        customer.credit_limit = request.POST.get('credit_limit', customer.credit_limit)
        customer.credit_terms = request.POST.get('credit_terms', customer.credit_terms)
        customer.is_active = request.POST.get('is_active') == 'on'
        customer.save()
        
        messages.success(request, f'Customer "{customer.name}" updated successfully.')
        return redirect('customer_detail', pk=customer.pk)
    
    return render(request, 'customers/customer_form.html', {'customer': customer})

@login_required
def customer_delete(request, pk):
    """Delete/deactivate customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.is_active = False
        customer.save()
        messages.success(request, f'Customer "{customer.name}" deactivated.')
        return redirect('customer_list')
    
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer})

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from sales.models import Sale, Payment
from customers.models import Customer

@login_required
def customer_statement(request, pk):
    """Generate customer account statement"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Get date range
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    today = timezone.now().date()
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = today.replace(day=1)  # Default to first of month
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = today
    
    # Get all sales in date range
    sales = Sale.objects.filter(
        customer=customer,
        status='COMPLETED',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).order_by('created_at')
    
    # Get payments in date range
    payments = Payment.objects.filter(
        sale__customer=customer,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).order_by('created_at')
    
    # Calculate running balance
    running_balance = customer.opening_balance
    transactions = []
    
    # Combine sales and payments into single transaction list
    for sale in sales:
        running_balance += sale.total_amount - sale.paid_amount
        transactions.append({
            'date': sale.created_at,
            'type': 'Sale',
            'reference': sale.invoice_number,
            'debit': sale.total_amount,
            'credit': sale.paid_amount,
            'balance': running_balance,
        })
    
    for payment in payments:
        running_balance -= payment.amount
        transactions.append({
            'date': payment.created_at,
            'type': 'Payment',
            'reference': f'Payment for {payment.sale.invoice_number}',
            'debit': 0,
            'credit': payment.amount,
            'balance': running_balance,
        })
    
    # Sort transactions by date
    transactions.sort(key=lambda x: x['date'])
    
    # Totals
    total_debits = sum(t['debit'] for t in transactions)
    total_credits = sum(t['credit'] for t in transactions)
    closing_balance = running_balance
    
    context = {
        'customer': customer,
        'start_date': start_date,
        'end_date': end_date,
        'transactions': transactions,
        'total_debits': total_debits,
        'total_credits': total_credits,
        'opening_balance': customer.opening_balance,
        'closing_balance': closing_balance,
    }
    
    return render(request, 'customers/customer_statement.html', context)

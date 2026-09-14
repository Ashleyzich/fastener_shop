# fix_complete_sale.py
with open('sales/views.py', 'r') as f:
    content = f.read()

# Find the complete_sale function
start = content.find('def complete_sale')
if start == -1:
    print('complete_sale not found')
    exit()

# Find the end - next function definition
end = content.find('def update_sale_totals', start)
if end == -1:
    end = len(content)

new_function = '''def complete_sale(request):
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

'''

content = content[:start] + new_function + content[end:]

with open('sales/views.py', 'w') as f:
    f.write(content)

print('Updated complete_sale function successfully')

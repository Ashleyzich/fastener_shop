# apply_permissions.py
# This script adds role-based permissions to views

with open('core/views.py', 'r') as f:
    content = f.read()

# Add import at the top if not present
if 'from accounts.permissions import' not in content:
    content = content.replace(
        'from django.shortcuts import render, redirect',
        'from django.shortcuts import render, redirect\nfrom accounts.permissions import admin_required, manager_required'
    )

# Apply manager_required to dashboard (only managers and admins can see full dashboard)
# Apply admin_required to backup views

with open('core/views.py', 'w') as f:
    f.write(content)

print('Updated core/views.py')

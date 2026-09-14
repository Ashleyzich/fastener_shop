# Fastener Shop Management System

A comprehensive management system for fastener shops.

## Features

- Modern Dashboard
- Point of Sale (POS)
- Inventory Management
- Customer Management
- Supplier Management
- Purchase Orders
- Credit Sales & Payments
- Reports (Sales, Inventory, Profit)
- User Roles (Admin, Manager, Cashier)
- Database Backups

## Tech Stack

- Django 5.0+
- SQLite
- Bootstrap 5.3
- Font Awesome

## Installation

1. Clone repo
   git clone https://github.com/YOUR_USERNAME/fastener-shop.git

2. Create venv
   python -m venv venv

3. Activate venv
   venv\Scripts\activate

4. Install dependencies
   pip install -r requirements.txt

5. Run migrations
   python manage.py migrate

6. Create superuser
   python manage.py createsuperuser

7. Run server
   python manage.py runserver

## User Roles

- Cashier: POS, Sales, Customers, Payments
- Manager: Everything except User Management and Backups
- Admin: Full access

## License




## Support

Open an issue in the repository for support.




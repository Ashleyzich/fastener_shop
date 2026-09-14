# Fastener Shop Management System

A comprehensive, modern management system built specifically for fastener shops selling bolts, nuts, washers, U-bolts, screws, threaded rods, anchors, rivets, and other fasteners.

## Features

- Modern Dashboard with real-time statistics
- Point of Sale (POS) system
- Credit sales and payment tracking
- Product management with detailed specifications
- Inventory tracking with low stock alerts
- Customer management with statements
- Supplier management
- Purchase orders and stock receiving
- Sales, inventory, and profit reports
- CSV export functionality
- User roles (Admin, Manager, Cashier)
- Database backups
- Receipt printing

## Tech Stack

- Backend: Django 5.0+
- Database: SQLite (PostgreSQL ready)
- Frontend: HTML5, CSS3, Bootstrap 5.3
- JavaScript: Vanilla JS
- Icons: Font Awesome
- Fonts: Google Fonts (Inter)

## Installation

1. Clone the repository
git clone https://github.com/YOUR_USERNAME/fastener-shop.git
cd fastener-shop

2. Create virtual environment
python -m venv venv
venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Run migrations
python manage.py makemigrations
python manage.py migrate

5. Create superuser
python manage.py createsuperuser

6. Run the server
python manage.py runserver

7. Open browser at http://127.0.0.1:8000

## User Roles

- Cashier: POS, Sales, Customers, Payments
- Manager: Everything except User Management and Backups
- Admin: Full access

## License



## Support

Open an issue in the repository for support.


import os

# Create simple placeholder templates
templates = {
    'templates/accounts/profile.html': '''{% extends 'base.html' %}
{% block title %}Profile{% endblock %}
{% block content %}
<h2>User Profile</h2>
<p>Username: {{ user.username }}</p>
<p>Email: {{ user.email|default:"Not set" }}</p>
<a href="{% url 'dashboard' %}" class="btn btn-secondary">Back to Dashboard</a>
{% endblock %}
''',
    'templates/inventory/product_list.html': '''{% extends 'base.html' %}
{% block title %}Products{% endblock %}
{% block content %}
<h2>Products</h2>
<p>Product list coming soon.</p>
<a href="{% url 'dashboard' %}" class="btn btn-secondary">Back to Dashboard</a>
{% endblock %}
''',
    'templates/inventory/product_detail.html': '''{% extends 'base.html' %}
{% block title %}Product Details{% endblock %}
{% block content %}
<h2>{{ product.name }}</h2>
<p>SKU: {{ product.sku }}</p>
<p>Quantity: {{ product.quantity }}</p>
<p>Price: ${{ product.selling_price }}</p>
<a href="{% url 'product_list' %}" class="btn btn-secondary">Back to Products</a>
{% endblock %}
''',
}

for filepath, content in templates.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Created {filepath}")

print("\nTemplates created!")
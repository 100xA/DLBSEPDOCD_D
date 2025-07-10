"""Catalog views."""

from django.shortcuts import render

from .models import Product


def product_list(request):
    """Display list of active products."""
    products = Product.objects.filter(is_active=True).order_by('name')
    return render(request, 'catalog/product_list.html', {'products': products}) 
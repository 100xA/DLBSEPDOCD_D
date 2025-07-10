"""Orders views."""

import json

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from devops_pipeline.apps.catalog.models import Product

from .models import Order, OrderItem


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_order(request):
    """Create a new order."""
    try:
        data = json.loads(request.body)
        sku = data.get("sku")
        qty = data.get("qty", 1)

        product = Product.objects.get(sku=sku, is_active=True)

        # Create order
        order = Order.objects.create(
            user=request.user, status=Order.Status.PAID  # Simplified for demo
        )

        # Create order item
        OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price)

        # Calculate total
        order.total = product.price * qty
        order.save()

        # Cache the price
        cache.set(f"order:{order.pk}:total", str(order.total), 3600)

        return JsonResponse({"id": order.pk, "total": str(order.total)}, status=201)

    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def create_order_web(request):
    """Create a new order via web form."""
    if request.method != "POST":
        return redirect("catalog:product_list")
    
    try:
        sku = request.POST.get("sku")
        qty = int(request.POST.get("qty", 1))

        product = get_object_or_404(Product, sku=sku, is_active=True)

        # Create order
        order = Order.objects.create(
            user=request.user, status=Order.Status.PAID  # Simplified for demo
        )

        # Create order item
        OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price)

        # Calculate total
        order.total = product.price * qty
        order.save()

        # Cache the price
        cache.set(f"order:{order.pk}:total", str(order.total), 3600)

        return render(request, "orders/success.html", {"order": order})

    except Product.DoesNotExist:
        return redirect("catalog:product_list")
    except Exception:
        return redirect("catalog:product_list")


@login_required
def order_list(request):
    """Display user's orders."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

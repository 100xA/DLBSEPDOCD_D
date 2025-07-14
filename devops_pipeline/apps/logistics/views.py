"""Logistics views."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .models import Shipping, ShippingEvent


@login_required
def track_shipment(request, tracking_number):
    """Track shipment by tracking number."""
    try:
        shipping = Shipping.objects.get(tracking_number=tracking_number)
        
        # Check if user owns this order
        if shipping.order.user != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        events = shipping.events.all()
        
        tracking_data = {
            'tracking_number': shipping.tracking_number,
            'carrier': shipping.get_carrier_display(),
            'status': shipping.get_status_display(),
            'estimated_delivery': shipping.estimated_delivery,
            'actual_delivery': shipping.actual_delivery,
            'events': [
                {
                    'status': event.get_status_display(),
                    'location': event.location,
                    'description': event.description,
                    'timestamp': event.event_time.isoformat()
                }
                for event in events
            ]
        }
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse(tracking_data)
        
        return render(request, 'logistics/tracking.html', {
            'shipping': shipping,
            'events': events
        })
        
    except Shipping.DoesNotExist:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Tracking number not found'}, status=404)
        return render(request, 'logistics/tracking_not_found.html')


@require_http_methods(["GET"])
def shipping_status(request, order_id):
    """Get shipping status for an order."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        shipping = Shipping.objects.get(order_id=order_id)
        
        # Check if user owns this order
        if shipping.order.user != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        return JsonResponse({
            'order_id': order_id,
            'tracking_number': shipping.tracking_number,
            'carrier': shipping.get_carrier_display(),
            'status': shipping.get_status_display(),
            'estimated_delivery': shipping.estimated_delivery,
            'shipping_address': shipping.shipping_address
        })
        
    except Shipping.DoesNotExist:
        return JsonResponse({'error': 'Shipping information not found'}, status=404)


@login_required
def shipping_history(request):
    """Show user's shipping history."""
    user_orders = request.user.order_set.all()
    shipments = Shipping.objects.filter(order__in=user_orders).order_by('-created_at')
    
    return render(request, 'logistics/shipping_history.html', {
        'shipments': shipments
    }) 
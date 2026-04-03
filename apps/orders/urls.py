from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Customer URLs
    path('checkout/', views.checkout, name='checkout'),
    path('create/', views.create_order, name='create'),
    path('success/<int:order_id>/', views.order_success, name='success'),
    path('cancel/<int:order_id>/', views.cancel_order, name='cancel'),
    path('<int:order_id>/', views.order_detail, name='detail'),
    path('track/<int:order_id>/', views.track_order, name='track'),
    
    # Company URLs
    path('company/orders/', views.company_orders, name='company_orders'),
    path('company/approve/<int:order_id>/', views.approve_order, name='approve_order'),
    path('company/process/<int:order_id>/', views.process_order, name='process_order'),
    path('company/ship/<int:order_id>/', views.ship_order, name='ship_order'),
    
    # Seller URLs
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/process/<int:item_id>/', views.process_order_item, name='process_order_item'),
    path('seller/ship/<int:item_id>/', views.ship_order_item, name='ship_order_item'),
    path('seller/deliver/<int:item_id>/', views.deliver_order_item, name='deliver_order_item'),
]
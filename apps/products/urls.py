from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Public views
    path('', views.product_list, name='list'),
    path('category/<slug:category_slug>/', views.product_list, name='category_list'),
    path('detail/<slug:slug>/', views.product_detail, name='detail'),
    path('detail/<slug:slug>/add-review/', views.add_review, name='add_review'),
    
    # Product management (Company/Seller only)
    path('manage/', views.product_manage, name='manage'),
    path('create/', views.product_create, name='create'),
    path('edit/<int:product_id>/', views.product_edit, name='edit'),
    path('delete/<int:product_id>/', views.product_delete, name='delete'),
    path('images/<int:product_id>/', views.product_images, name='images'),
    path('image-delete/<int:image_id>/', views.product_image_delete, name='image_delete'),
    
    # Category management (Admin only)
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/edit/<int:category_id>/', views.category_edit, name='category_edit'),
    path('categories/delete/<int:category_id>/', views.category_delete, name='category_delete'),

    path('api/products/', views.api_products, name='api_products'),
]
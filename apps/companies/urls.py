from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('', views.company_list, name='list'),
    path('<int:company_id>/', views.company_detail, name='detail'),
    path('sellers/', views.manage_sellers, name='manage_sellers'),
    path('sellers/add/', views.add_seller, name='add_seller'),
    path('sellers/<int:seller_id>/edit/', views.edit_seller, name='edit_seller'),
    path('sellers/<int:seller_id>/delete/', views.delete_seller, name='delete_seller'),
]
# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('representative-login/', views.representative_login_view, name='representative_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('representative-dashboard/', views.representative_dashboard, name='representative_dashboard'),
    path('add-representative/', views.add_representative, name='add_representative'),
    path('logout/', views.logout_view, name='logout'),
    # Admin: Harcama Kategori Yönetimi
    path('expense-categories/', views.expense_category_list, name='expense_category_list'),
    path('expense-categories/add/', views.expense_category_create, name='expense_category_create'),
    path('expense-categories/edit/<int:pk>/', views.expense_category_edit, name='expense_category_edit'),
    path('expense-categories/delete/<int:pk>/', views.expense_category_delete, name='expense_category_delete'),
    
    # Temsilci: Harcama Giriş ve Listeleme
    path('expense-entry/', views.expense_entry, name='expense_entry'),
    path('expenses/', views.expense_list, name='expense_list'),

    path('expense-report/', views.expense_report, name='expense_report'),

    path('customer-entry/', views.customer_entry, name='customer_entry'),
    path('customer-list/', views.customer_list, name='customer_list'),
    # Admin: Abonelik Türü Yönetimi
    path('subscription-types/', views.subscription_type_list, name='subscription_type_list'),
    path('subscription-types/add/', views.subscription_type_create, name='subscription_type_create'),
    path('subscription-types/edit/<int:pk>/', views.subscription_type_edit, name='subscription_type_edit'),
    path('subscription-types/delete/<int:pk>/', views.subscription_type_delete, name='subscription_type_delete'),
    path('subscription-durations/', views.subscription_duration_list, name='subscription_duration_list'),
    path('payment-methods/', views.payment_method_list, name='payment_method_list'),
    path('payment-methods/add/', views.payment_method_create, name='payment_method_create'),
    path('payment-methods/edit/<int:pk>/', views.payment_method_edit, name='payment_method_edit'),
    path('payment-methods/delete/<int:pk>/', views.payment_method_delete, name='payment_method_delete'),
    path('subscription-durations/add/', views.subscription_duration_create, name='subscription_duration_create'),
    path('subscription-durations/edit/<int:pk>/', views.subscription_duration_edit, name='subscription_duration_edit'),
    path('subscription-durations/delete/<int:pk>/', views.subscription_duration_delete, name='subscription_duration_delete'),
    path('admin-customer-dashboard/', views.admin_customer_dashboard, name='admin_customer_dashboard'),

]

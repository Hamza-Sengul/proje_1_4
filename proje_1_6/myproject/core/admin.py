# core/admin.py

from django.contrib import admin
from .models import Product, ProductLog

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'can_be_given', 'updated_at')
    list_filter = ('can_be_given',)
    search_fields = ('name',)

@admin.register(ProductLog)
class ProductLogAdmin(admin.ModelAdmin):
    list_display = ('representative', 'customer', 'product', 'quantity_given', 'extra_fee', 'created_at')
    list_filter = ('representative', 'product')
    search_fields = ('customer__first_name', 'customer__last_name', 'product__name')

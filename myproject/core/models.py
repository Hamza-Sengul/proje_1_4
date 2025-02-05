from django.db import models
from django.contrib.auth.models import User

class RepresentativeProfile(models.Model):
    CATEGORY_CHOICES = (
        (1, 'Kategori 1 (Harcama)'),
        (2, 'Kategori 2 (Harcama, Müşteri Ekleme)'),
        (3, 'Kategori 3 (Harcama, Müşteri Ekleme, Tahsilat Alma)'),
        (4, 'Kategori 4 (Harcama, Müşteri Ekleme, Tahsilat Alma, Araç Ekleme)'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='representative_profile')
    category = models.PositiveSmallIntegerField(choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.get_category_display()}"


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategori Adı")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Harcamа Kategorisi"
        verbose_name_plural = "Harcamа Kategorileri"

    def __str__(self):
        return self.name

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='expenses')
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Miktar")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Harcamа"
        verbose_name_plural = "Harcamalar"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.amount}"


# --- Abonelik ile İlgili Modeller ---
class SubscriptionType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Abonelik Türü")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Abonelik Türü"
        verbose_name_plural = "Abonelik Türleri"
    
    def __str__(self):
        return self.name

class SubscriptionDuration(models.Model):
    name = models.CharField(max_length=100, verbose_name="Abonelik Süresi")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Abonelik Süresi"
        verbose_name_plural = "Abonelik Süreleri"
    
    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    name = models.CharField(max_length=100, verbose_name="Ödeme Yöntemi")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ödeme Yöntemi"
        verbose_name_plural = "Ödeme Yöntemleri"
    
    def __str__(self):
        return self.name

# --- Müşteri Modeli ---
class Customer(models.Model):
    representative = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers', verbose_name="Temsilci")
    first_name = models.CharField(max_length=30, verbose_name="Ad")
    last_name = models.CharField(max_length=30, verbose_name="Soyad")
    identifier = models.CharField(max_length=50, verbose_name="TC / Vergi No")
    tax_address = models.TextField(blank=True, null=True, verbose_name="Vergi Adresi")
    address = models.TextField(verbose_name="Adres")
    subscription_type = models.ForeignKey(SubscriptionType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Abonelik Türü")
    subscription_duration = models.ForeignKey(SubscriptionDuration, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Abonelik Süresi")
    subscription_start_date = models.DateField(null=True, blank=True, verbose_name="Aboneliğin Başlama Tarihi")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ödeme Tipi")
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Ödeme Miktarı")
    detail = models.TextField(blank=True, null=True, verbose_name="Detay Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = "Müşteri"
        verbose_name_plural = "Müşteriler"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.identifier}"

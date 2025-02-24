from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta

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

class Customer(models.Model):
    representative = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers', verbose_name="Temsilci")
    first_name = models.CharField(max_length=30, verbose_name="Ad")
    last_name = models.CharField(max_length=30, verbose_name="Soyad")
    identifier = models.CharField(max_length=50, verbose_name="TC / Vergi No")
    tax_address = models.CharField(max_length=50, blank=True, null=True, verbose_name="Vergi Adresi")
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



class PaymentRecord(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Ödeme Bekleniyor'),
        ('paid', 'Ödeme Yapıldı'),
    )

    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='payment_records', verbose_name="Müşteri")
    period_start = models.DateField(verbose_name="Periyot Başlangıcı")
    period_end = models.DateField(verbose_name="Periyot Bitişi")
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending', verbose_name="Ödeme Durumu")
    payment_date = models.DateField(null=True, blank=True, verbose_name="Ödeme Tarihi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ödeme Kaydı"
        verbose_name_plural = "Ödeme Kayıtları"
        ordering = ['period_start']

    def __str__(self):
        return f"{self.customer} - {self.period_start} / {self.status}"

    @classmethod
    def create_period(cls, customer):
        from datetime import date, timedelta  
        start_date = customer.subscription_start_date
        today = date.today()

        if not start_date:
            return None

        num_periods = ((today - start_date).days // 30) + 1

        period_start = start_date + timedelta(days=(num_periods - 1) * 30)
        period_end = period_start + timedelta(days=29)  

        record, created = cls.objects.get_or_create(
            customer=customer,
            period_start=period_start,
            period_end=period_end,
            defaults={'status': 'pending'}
        )
        return record

class CustomerRequest(models.Model):
    REQUEST_TYPE_CHOICES = (
        ('talep', 'Talep'),
        ('istek', 'İstek'),
        ('sikayet', 'Şikayet'),
    )
    REQUEST_STATUS_CHOICES = (
        ('pending', 'Çözülmedi / Beklemede'),
        ('in_progress', 'İşlemde'),
        ('resolved', 'Çözüldü / Tamamlandı'),
    )

    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='requests')
    representative = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()

    status = models.CharField(
        max_length=20, choices=REQUEST_STATUS_CHOICES,
        default='pending', verbose_name='Durum'
    )
    solution = models.TextField(blank=True, null=True, verbose_name='Çözüm Notu')
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name='Çözülme Tarihi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.get_request_type_display()} - {self.get_status_display()}"

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="Ürün Adı")
    quantity = models.PositiveIntegerField(verbose_name="Stok Adedi")
    can_be_given = models.BooleanField(default=True, verbose_name="Verilebilir")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"

    def __str__(self):
        return f"{self.name} (Stok: {self.quantity}, Verilebilir: {self.can_be_given})"


class ProductLog(models.Model):
    representative = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Temsilci"
    )
    customer = models.ForeignKey(
        'Customer', on_delete=models.CASCADE, 
        verbose_name="Müşteri"
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, 
        null=True, blank=True, verbose_name="Ürün"
    )
    quantity_given = models.PositiveIntegerField(verbose_name="Verilen Adet")
    extra_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                    verbose_name="Ek Ücret")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ürün Verme Logu"
        verbose_name_plural = "Ürün Verme Logları"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.representative} -> {self.customer} | {self.product} x {self.quantity_given}"





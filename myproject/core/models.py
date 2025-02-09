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
        from datetime import date, timedelta  # timedelta eklenmeli
        start_date = customer.subscription_start_date
        today = date.today()

        # Müşterinin abonelik başlangıç tarihi tanımlı değilse işlem yapmayalım.
        if not start_date:
            return None

        # Bugüne kadar kaç periyot geçtiğini hesaplayalım:
        num_periods = ((today - start_date).days // 30) + 1

        # Son periyot başlangıcı:
        period_start = start_date + timedelta(days=(num_periods - 1) * 30)
        period_end = period_start + timedelta(days=29)  # 30 günlük periyot

        # Eğer bu periyot için zaten bir ödeme kaydı yoksa oluştur
        record, created = cls.objects.get_or_create(
            customer=customer,
            period_start=period_start,
            period_end=period_end,
            defaults={'status': 'pending'}
        )
        return record

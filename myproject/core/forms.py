from django import forms
from .models import RepresentativeProfile, ExpenseCategory, Expense, Customer, SubscriptionType, SubscriptionDuration, PaymentMethod, CustomerRequest, Product, ProductLog

class RepresentativeCreationForm(forms.Form):
    username = forms.CharField(max_length=150, label="Kullanıcı Adı")
    first_name = forms.CharField(max_length=30, label="Ad")
    last_name = forms.CharField(max_length=30, label="Soyad")
    temporary_password = forms.CharField(widget=forms.PasswordInput, label="Geçici Şifre")
    category = forms.ChoiceField(choices=RepresentativeProfile.CATEGORY_CHOICES, label="Temsilci Kategorisi")


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name']
        labels = {
            'name': 'Kategori Adı'
        }

class ExpenseEntryForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount']
        labels = {
            'category': 'Kategori',
            'description': 'Açıklama (isteğe bağlı)',
            'amount': 'Miktar'
        }


class CustomerCreationForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'identifier', 'tax_address',
            'address', 'subscription_type', 'subscription_duration',
            'subscription_start_date', 'payment_method', 'payment_amount',
            'detail'
        ]
        labels = {
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'identifier': 'TC / Vergi No',
            'tax_address': 'Vergi Adresi (Vergi No girilmişse)',
            'address': 'Adres',
            'subscription_type': 'Abonelik Türü',
            'subscription_duration': 'Abonelik Süresi',
            'subscription_start_date': 'Aboneliğin Başlama Tarihi',
            'payment_method': 'Ödeme Tipi',
            'payment_amount': 'Ödeme Miktarı',
            'detail': 'Detay Açıklama'
        }
        widgets = {
            'subscription_start_date': forms.DateInput(attrs={'type': 'date'}),
            'detail': forms.Textarea(attrs={'rows': 3}),
        }

class SubscriptionTypeForm(forms.ModelForm):
    class Meta:
        model = SubscriptionType
        fields = ['name']
        labels = {'name': 'Abonelik Türü'}

class SubscriptionDurationForm(forms.ModelForm):
    class Meta:
        model = SubscriptionDuration
        fields = ['name']
        labels = {'name': 'Abonelik Süresi'}

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name']
        labels = {'name': 'Ödeme Yöntemi'}



class CustomerRequestForm(forms.ModelForm):
    class Meta:
        model = CustomerRequest
        fields = ['customer', 'request_type', 'title', 'description']
        labels = {
            'customer': 'Müşteri',
            'request_type': 'Kayıt Türü (Talep / İstek / Şikayet)',
            'title': 'Başlık',
            'description': 'Açıklama'
        }



class GiveProductForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(),
        label="Müşteri"
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        label="Ürün (verilebilir)"
    )
    quantity_given = forms.IntegerField(min_value=1, label="Verilen Adet")
    extra_fee = forms.DecimalField(max_digits=10, decimal_places=2, label="Ek Ücret", initial=0)
    
    def __init__(self, *args, **kwargs):
        rep_user = kwargs.pop('representative_user', None)
        super().__init__(*args, **kwargs)

        # Müşteri listesi: Bu temsilcinin veya alt kademelerin müşterileri
        # (ihtiyaca göre daraltabilirsiniz, burada sadece rep_user'ın kendi eklediği müşterileri göstermek basit bir örnek)
        if rep_user:
            self.fields['customer'].queryset = Customer.objects.filter(representative=rep_user)

        # Ürün listesi: can_be_given = True, quantity > 0
        self.fields['product'].queryset = Product.objects.filter(can_be_given=True, quantity__gt=0)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'quantity', 'can_be_given']
        labels = {
            'name': 'Ürün Adı',
            'quantity': 'Stok Adedi',
            'can_be_given': 'Verilebilir mi?',
        }
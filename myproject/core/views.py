# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .forms import RepresentativeCreationForm, ExpenseCategoryForm, ExpenseEntryForm, CustomerCreationForm, SubscriptionTypeForm, SubscriptionDurationForm, PaymentMethodForm
from .models import ExpenseCategory, Expense, RepresentativeProfile, Customer, SubscriptionType, SubscriptionDuration, PaymentMethod
from django.contrib.auth import logout
from django.db.models import Sum
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# Ana sayfa: Yönetici ve Temsilci giriş seçeneklerini sunar.
def home(request):
    return render(request, 'core/home.html')

# Yönetici girişi view'ı
def admin_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                form.add_error(None, "Bu kullanıcı yönetici değildir.")
    else:
        form = AuthenticationForm(request)
    return render(request, 'core/admin_login.html', {'form': form})

# Temsilci girişi view'ı
def representative_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Yönetici dışındaki kullanıcılar temsilci olarak kabul edilir.
            if not user.is_superuser:
                login(request, user)
                return redirect('representative_dashboard')
            else:
                form.add_error(None, "Bu kullanıcı temsilci olarak giriş yapamaz.")
    else:
        form = AuthenticationForm(request)
    return render(request, 'core/representative_login.html', {'form': form})

# Yönetici paneli view'ı (yalnızca superuser erişimi)
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    return render(request, 'core/admin_dashboard.html')
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_customer_dashboard(request):
    # Tüm müşteri kayıtlarını oluşturulma tarihine göre azalan sırada alalım
    customers = Customer.objects.select_related(
        'representative', 'subscription_type', 'subscription_duration', 'payment_method'
    ).order_by('-created_at')
    
    # Filtre parametrelerini GET üzerinden alalım
    rep_id = request.GET.get('representative')          # Temsilci id
    date_start = request.GET.get('date_start')            # Başlangıç tarihi (YYYY-MM-DD)
    date_end = request.GET.get('date_end')                # Bitiş tarihi (YYYY-MM-DD)
    subscription_type_id = request.GET.get('subscription_type')
    identifier = request.GET.get('identifier')            # TC/Vergi No
    
    # Filtreleme uygulamaları
    if rep_id:
        customers = customers.filter(representative__id=rep_id)
    if date_start:
        try:
            date_start_parsed = datetime.strptime(date_start, "%Y-%m-%d")
            customers = customers.filter(created_at__gte=date_start_parsed)
        except ValueError:
            pass
    if date_end:
        try:
            date_end_parsed = datetime.strptime(date_end, "%Y-%m-%d")
            customers = customers.filter(created_at__lte=date_end_parsed)
        except ValueError:
            pass
    if subscription_type_id:
        customers = customers.filter(subscription_type__id=subscription_type_id)
    if identifier:
        customers = customers.filter(identifier__icontains=identifier)
    
    # Sayfalama: Her sayfada 10 kayıt gösterilsin.
    paginator = Paginator(customers, 10)
    page = request.GET.get('page')
    try:
        customers_page = paginator.page(page)
    except PageNotAnInteger:
        customers_page = paginator.page(1)
    except EmptyPage:
        customers_page = paginator.page(paginator.num_pages)
    
    # Filtre seçenekleri için: Temsilci listesi (benzersiz) ve abonelik türleri
    representatives = Customer.objects.values('representative__id', 'representative__username').distinct()
    subscription_types = SubscriptionType.objects.all()
    
    filter_params = {
        'representative': rep_id or '',
        'date_start': date_start or '',
        'date_end': date_end or '',
        'subscription_type': subscription_type_id or '',
        'identifier': identifier or '',
    }
    
    context = {
        'customers': customers_page,
        'representatives': representatives,
        'subscription_types': subscription_types,
        'filter_params': filter_params,
        'paginator': paginator,
        'page_obj': customers_page,
        'is_paginated': customers_page.has_other_pages(),
    }
    
    return render(request, 'core/admin_customer_dashboard.html', context)
# Temsilci paneli view'ı (yönetici dışındaki kullanıcılar için)
@login_required
def representative_dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    return render(request, 'core/representative_dashboard.html')

# Yönetici panelinden temsilci ekleme view'ı (yalnızca yönetici erişimi)
@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_representative(request):
    if request.method == 'POST':
        form = RepresentativeCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            temporary_password = form.cleaned_data['temporary_password']
            category = form.cleaned_data['category']
            # Yeni kullanıcı oluşturuluyor.
            user = User.objects.create_user(
                username=username, 
                password=temporary_password,
                first_name=first_name, 
                last_name=last_name
            )
            # Kullanıcıya temsilci profil bilgisi ekleniyor.
            RepresentativeProfile.objects.create(user=user, category=category)
            return redirect('admin_dashboard')
    else:
        form = RepresentativeCreationForm()
    return render(request, 'core/add_representative.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')


# --- ADMIN: Harcama Kategori Yönetimi ---

@login_required
@user_passes_test(lambda u: u.is_superuser)
def expense_category_list(request):
    categories = ExpenseCategory.objects.all().order_by('created_at')
    return render(request, 'core/expense_category_list.html', {'categories': categories})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def expense_category_create(request):
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expense_category_list')
    else:
        form = ExpenseCategoryForm()
    return render(request, 'core/expense_category_form.html', {'form': form, 'action': 'Ekle'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def expense_category_edit(request, pk):
    category = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('expense_category_list')
    else:
        form = ExpenseCategoryForm(instance=category)
    return render(request, 'core/expense_category_form.html', {'form': form, 'action': 'Düzenle'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def expense_category_delete(request, pk):
    category = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('expense_category_list')
    return render(request, 'core/expense_category_confirm_delete.html', {'category': category})

# core/views.py (devam)

@login_required
def expense_entry(request):
    # Eğer sadece 1. kategori temsilcileri bu işlemi yapabiliyorsa; kontrol ekleyebilirsiniz:
    # if hasattr(request.user, 'representative_profile') and request.user.representative_profile.category != 1:
    #     return redirect('representative_dashboard')
    
    if request.method == 'POST':
        form = ExpenseEntryForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('expense_list')
    else:
        form = ExpenseEntryForm()
    return render(request, 'core/expense_entry.html', {'form': form})

@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/expense_list.html', {'expenses': expenses})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def expense_report(request):
    # İlk olarak tüm harcamaları sıralı şekilde alalım:
    expenses_qs = Expense.objects.select_related('user', 'category').order_by('-created_at')
    
    # Filtreleme için GET parametrelerini alalım:
    rep_id     = request.GET.get('representative')  # temsilci (user id)
    date_start = request.GET.get('date_start')        # YYYY-MM-DD formatında
    date_end   = request.GET.get('date_end')
    price_min  = request.GET.get('price_min')
    price_max  = request.GET.get('price_max')
    
    # Eğer temsilci filtresi varsa
    if rep_id:
        expenses_qs = expenses_qs.filter(user__id=rep_id)
    
    # Tarih filtresi (oluşturulma tarihi)
    if date_start:
        try:
            # Tarih formatının doğru olduğundan emin olun
            date_start_parsed = datetime.strptime(date_start, "%Y-%m-%d")
            expenses_qs = expenses_qs.filter(created_at__gte=date_start_parsed)
        except ValueError:
            pass
    if date_end:
        try:
            date_end_parsed = datetime.strptime(date_end, "%Y-%m-%d")
            expenses_qs = expenses_qs.filter(created_at__lte=date_end_parsed)
        except ValueError:
            pass

    # Fiyat filtresi
    if price_min:
        try:
            expenses_qs = expenses_qs.filter(amount__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            expenses_qs = expenses_qs.filter(amount__lte=float(price_max))
        except ValueError:
            pass
    
    # Üst kısımda görüntülemek için genel toplam ve kategori bazlı toplamları hesaplayalım:
    total_expense = expenses_qs.aggregate(total=Sum('amount'))['total'] or 0
    category_totals = expenses_qs.values('category__name').annotate(total=Sum('amount')).order_by('category__name')
    
    # Sayfalama: Her sayfada 10 kayıt gösterelim.
    paginator = Paginator(expenses_qs, 10)
    page = request.GET.get('page')
    try:
        expenses = paginator.page(page)
    except PageNotAnInteger:
        expenses = paginator.page(1)
    except EmptyPage:
        expenses = paginator.page(paginator.num_pages)
    
    # Filtreleme formu için; temsilci listesini (harcama kaydı olan temsilcileri) hazırlayalım:
    representatives = Expense.objects.values('user__id', 'user__username').distinct()
    
    context = {
        'total_expense': total_expense,
        'category_totals': category_totals,
        'expenses': expenses,
        'representatives': representatives,
        'paginator': paginator,
        'page_obj': expenses,
        'is_paginated': expenses.has_other_pages(),
        # Filtre alanlarının dolu kalması için mevcut filtre değerlerini gönderiyoruz:
        'filter_params': {
            'representative': rep_id or '',
            'date_start': date_start or '',
            'date_end': date_end or '',
            'price_min': price_min or '',
            'price_max': price_max or '',
        },
    }
    return render(request, 'core/expense_report.html', context)

@login_required
def customer_entry(request):
    # Eğer kullanıcı 2. kademe (ve üzeri) temsilci değilse, geri yönlendirme yapılıyor.
    if hasattr(request.user, 'representative_profile') and int(request.user.representative_profile.category) < 2:
        return redirect('representative_dashboard')
    
    if request.method == 'POST':
        form = CustomerCreationForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.representative = request.user
            customer.save()
            return redirect('representative_dashboard')
    else:
        form = CustomerCreationForm()
    return render(request, 'core/customer_entry.html', {'form': form})

from django.contrib.auth.decorators import user_passes_test

# Sadece admin erişebilsin
@login_required
@user_passes_test(lambda u: u.is_superuser)
def subscription_type_list(request):
    types = SubscriptionType.objects.all().order_by('created_at')
    return render(request, 'core/subscription_type_list.html', {'types': types})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def subscription_type_create(request):
    if request.method == 'POST':
        form = SubscriptionTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subscription_type_list')
    else:
        form = SubscriptionTypeForm()
    return render(request, 'core/subscription_type_form.html', {'form': form, 'action': 'Ekle'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def subscription_type_edit(request, pk):
    stype = get_object_or_404(SubscriptionType, pk=pk)
    if request.method == 'POST':
        form = SubscriptionTypeForm(request.POST, instance=stype)
        if form.is_valid():
            form.save()
            return redirect('subscription_type_list')
    else:
        form = SubscriptionTypeForm(instance=stype)
    return render(request, 'core/subscription_type_form.html', {'form': form, 'action': 'Düzenle'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def subscription_type_delete(request, pk):
    stype = get_object_or_404(SubscriptionType, pk=pk)
    if request.method == 'POST':
        stype.delete()
        return redirect('subscription_type_list')
    return render(request, 'core/subscription_type_confirm_delete.html', {'stype': stype})

@login_required
def customer_list(request):
    # Eğer kullanıcı yönetici ise, bu sayfaya erişimi engelleyip yönetici paneline yönlendirebilirsiniz.
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    
    # Sadece giriş yapan temsilcinin eklediği müşterileri getiriyoruz.
    customers = Customer.objects.filter(representative=request.user).order_by('-created_at')
    return render(request, 'core/customer_list.html', {'customers': customers})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def subscription_duration_create(request):
    if request.method == 'POST':
        form = SubscriptionDurationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subscription_duration_list')
    else:
        form = SubscriptionDurationForm()
    return render(request, 'core/subscription_duration_form.html', {'form': form, 'action': 'Ekle'})
@login_required
@user_passes_test(lambda u: u.is_superuser)
def subscription_duration_list(request):
    durations = SubscriptionDuration.objects.all().order_by('created_at')
    return render(request, 'core/subscription_duration_list.html', {'durations': durations})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def payment_method_list(request):
    methods = PaymentMethod.objects.all().order_by('created_at')
    return render(request, 'core/payment_method_list.html', {'methods': methods})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def subscription_duration_edit(request, pk):
    duration = get_object_or_404(SubscriptionDuration, pk=pk)
    if request.method == 'POST':
        form = SubscriptionDurationForm(request.POST, instance=duration)
        if form.is_valid():
            form.save()
            return redirect('subscription_duration_list')
    else:
        form = SubscriptionDurationForm(instance=duration)
    return render(request, 'core/subscription_duration_form.html', {'form': form, 'action': 'Düzenle'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def subscription_duration_delete(request, pk):
    duration = get_object_or_404(SubscriptionDuration, pk=pk)
    if request.method == 'POST':
        duration.delete()
        return redirect('subscription_duration_list')
    return render(request, 'core/subscription_duration_confirm_delete.html', {'duration': duration})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def payment_method_create(request):
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payment_method_list')
    else:
        form = PaymentMethodForm()
    return render(request, 'core/payment_method_form.html', {'form': form, 'action': 'Ekle'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def payment_method_edit(request, pk):
    method = get_object_or_404(PaymentMethod, pk=pk)
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, instance=method)
        if form.is_valid():
            form.save()
            return redirect('payment_method_list')
    else:
        form = PaymentMethodForm(instance=method)
    return render(request, 'core/payment_method_form.html', {'form': form, 'action': 'Düzenle'})

# core/views.py

@login_required
@user_passes_test(lambda u: u.is_superuser)
def payment_method_delete(request, pk):
    method = get_object_or_404(PaymentMethod, pk=pk)
    if request.method == 'POST':
        method.delete()
        return redirect('payment_method_list')
    return render(request, 'core/payment_method_confirm_delete.html', {'method': method})


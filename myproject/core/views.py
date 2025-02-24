from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .forms import RepresentativeCreationForm, ExpenseCategoryForm, ExpenseEntryForm, CustomerCreationForm, SubscriptionTypeForm, SubscriptionDurationForm, PaymentMethodForm, CustomerRequestForm, GiveProductForm, ProductForm
from .models import ExpenseCategory, Expense, RepresentativeProfile, Customer, SubscriptionType, SubscriptionDuration, PaymentMethod, PaymentRecord, CustomerRequest, ProductLog, Product
from django.contrib.auth import logout
from django.db.models import Sum
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import date, timedelta
from django.db.models import Q
from django.utils import timezone

def home(request):
    return render(request, 'core/home.html')

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

def representative_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_superuser:
                login(request, user)
                return redirect('representative_dashboard')
            else:
                form.add_error(None, "Bu kullanıcı temsilci olarak giriş yapamaz.")
    else:
        form = AuthenticationForm(request)
    return render(request, 'core/representative_login.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    return render(request, 'core/admin_dashboard.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_customer_dashboard(request):
    customers = Customer.objects.select_related(
        'representative', 'subscription_type', 'subscription_duration', 'payment_method'
    ).order_by('-created_at')
    
    rep_id = request.GET.get('representative')        
    date_start = request.GET.get('date_start')            
    date_end = request.GET.get('date_end')               
    subscription_type_id = request.GET.get('subscription_type')
    identifier = request.GET.get('identifier')           
    
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
    
    paginator = Paginator(customers, 10)
    page = request.GET.get('page')
    try:
        customers_page = paginator.page(page)
    except PageNotAnInteger:
        customers_page = paginator.page(1)
    except EmptyPage:
        customers_page = paginator.page(paginator.num_pages)
    
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

@login_required
def representative_dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    return render(request, 'core/representative_dashboard.html')

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
            user = User.objects.create_user(
                username=username, 
                password=temporary_password,
                first_name=first_name, 
                last_name=last_name
            )
            RepresentativeProfile.objects.create(user=user, category=category)
            return redirect('admin_dashboard')
    else:
        form = RepresentativeCreationForm()
    return render(request, 'core/add_representative.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

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

@login_required
def expense_entry(request):    
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
    expenses_qs = Expense.objects.select_related('user', 'category').order_by('-created_at')
    
    rep_id     = request.GET.get('representative')  
    date_start = request.GET.get('date_start')       
    date_end   = request.GET.get('date_end')
    price_min  = request.GET.get('price_min')
    price_max  = request.GET.get('price_max')
    
    if rep_id:
        expenses_qs = expenses_qs.filter(user__id=rep_id)
    
    if date_start:
        try:
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
    
    total_expense = expenses_qs.aggregate(total=Sum('amount'))['total'] or 0
    category_totals = expenses_qs.values('category__name').annotate(total=Sum('amount')).order_by('category__name')
    
    paginator = Paginator(expenses_qs, 10)
    page = request.GET.get('page')
    try:
        expenses = paginator.page(page)
    except PageNotAnInteger:
        expenses = paginator.page(1)
    except EmptyPage:
        expenses = paginator.page(paginator.num_pages)
    
    representatives = Expense.objects.values('user__id', 'user__username').distinct()
    
    context = {
        'total_expense': total_expense,
        'category_totals': category_totals,
        'expenses': expenses,
        'representatives': representatives,
        'paginator': paginator,
        'page_obj': expenses,
        'is_paginated': expenses.has_other_pages(),
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
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    
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


@login_required
@user_passes_test(lambda u: u.is_superuser)
def payment_method_delete(request, pk):
    method = get_object_or_404(PaymentMethod, pk=pk)
    if request.method == 'POST':
        method.delete()
        return redirect('payment_method_list')
    return render(request, 'core/payment_method_confirm_delete.html', {'method': method})



@login_required
def payment_collection(request):
    # Sadece 3. kademe (ve üzeri) temsilcilerin erişebileceği kontrolü
    if hasattr(request.user, 'representative_profile'):
        if int(request.user.representative_profile.category) < 3:
            return redirect('representative_dashboard')
    else:
        return redirect('representative_dashboard')

    today = date.today()

    # Tüm müşteriler için, bugüne ait ödeme periyodu kaydını (veya oluşturulmamışsa oluşturun) çekelim.
    # Burada, sadece o periyot ödeme durumu "pending" olanları listeleyebiliriz.
    pending_records = PaymentRecord.objects.filter(period_start__lte=today, period_end__gte=today, status='pending')

    if request.method == 'POST':
        # Ödeme işaretleme işlemi: form gönderimiyle, belirli bir PaymentRecord'un id'si gönderilir.
        record_id = request.POST.get('record_id')
        record = get_object_or_404(PaymentRecord, id=record_id)
        record.status = 'paid'
        record.payment_date = today
        record.save()
        return redirect('payment_collection')

    context = {
        'pending_records': pending_records,
        'today': today,
    }
    return render(request, 'core/payment_collection.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def payment_overview(request):
    today = date.today()
    
    # 1) GET parametrelerini alalım
    rep_id = request.GET.get('representative')   # temsilci id
    sub_type_id = request.GET.get('sub_type')    # abonelik türü id
    date_start = request.GET.get('date_start')   # abonelik başlangıç tarihi aralığı (start)
    date_end = request.GET.get('date_end')       # abonelik başlangıç tarihi aralığı (end)
    cust_name = request.GET.get('cust_name')     # müşteri adı araması
    durum = request.GET.get('durum')             # on_time / delayed
    
    # 2) Müşteri sorgusunu oluştur
    customers_qs = Customer.objects.all().order_by('subscription_start_date')
    
    # Temsilci filtre
    if rep_id:
        customers_qs = customers_qs.filter(representative__id=rep_id)
    
    # Abonelik türü filtre
    if sub_type_id:
        customers_qs = customers_qs.filter(subscription_type__id=sub_type_id)
    
    # Tarih aralığı filtre (subscription_start_date)
    if date_start:
        try:
            date_start_parsed = datetime.strptime(date_start, '%Y-%m-%d').date()
            customers_qs = customers_qs.filter(subscription_start_date__gte=date_start_parsed)
        except ValueError:
            pass
    
    if date_end:
        try:
            date_end_parsed = datetime.strptime(date_end, '%Y-%m-%d').date()
            customers_qs = customers_qs.filter(subscription_start_date__lte=date_end_parsed)
        except ValueError:
            pass
    
    # Müşteri adı araması
    if cust_name:
        customers_qs = customers_qs.filter(
            Q(first_name__icontains=cust_name) | Q(last_name__icontains=cust_name)
        )
    
    # 3) payment_info hesaplaması
    payment_info = []
    for customer in customers_qs:
        if customer.subscription_start_date:
            total_periods = ((today - customer.subscription_start_date).days // 30) + 1
            if total_periods < 0:
                total_periods = 0
        else:
            total_periods = 0
        
        paid_periods = customer.payment_records.filter(status='paid').count()
        pending_periods = total_periods - paid_periods
        
        info = {
            'customer': customer,
            'total_periods': total_periods,
            'paid_periods': paid_periods,
            'pending_periods': max(pending_periods, 0),
            'on_time': pending_periods <= 0,  # True/False
            'delayed': pending_periods > 0,   # True/False
        }
        payment_info.append(info)
    
    # 4) Durum (zamanında / gecikmiş) filtresi (in-memory)
    if durum == 'on_time':
        payment_info = [i for i in payment_info if i['on_time'] is True]
    elif durum == 'delayed':
        payment_info = [i for i in payment_info if i['delayed'] is True]
    
    # 5) Filtre seçenekleri: Temsilci, Abonelik türü listesi
    representatives = User.objects.filter(representative_profile__isnull=False)
    subscription_types = SubscriptionType.objects.all()
    
    context = {
        'payment_info': payment_info,
        'today': today,
        
        # Formun seçili kalması için
        'selected_rep': rep_id or '',
        'selected_sub_type': sub_type_id or '',
        'selected_date_start': date_start or '',
        'selected_date_end': date_end or '',
        'selected_cust_name': cust_name or '',
        'selected_durum': durum or '',
        
        # Filtre seçenekleri
        'representatives': representatives,
        'subscription_types': subscription_types,
    }
    return render(request, 'core/payment_overview.html', context)


@login_required
def rep_payment_collection(request):
    # Yalnızca 3. kademe (ve üzeri) temsilcilerin erişebilmesi için kontrol:
    if not (hasattr(request.user, 'representative_profile') and int(request.user.representative_profile.category) >= 3):
        return redirect('representative_dashboard')
        
    today = date.today()
    rep_category = int(request.user.representative_profile.category)
    
    # Kapsam: Kendi eklediği müşteriler veya
    # daha düşük kategoriye sahip temsilciler tarafından eklenen müşteriler.
    customers_in_scope = Customer.objects.filter(
        Q(representative=request.user) |
        Q(representative__representative_profile__category__lt=rep_category)
    )
    
    # Kapsamdaki her müşteri için, bugüne göre geçerli (güncel veya gecikmiş) PaymentRecord oluşturuluyor.
    for cust in customers_in_scope:
        PaymentRecord.create_period(cust)
    
    # Pending (ödeme bekleyen) kayıtları çekiyoruz:
    pending_records = list(PaymentRecord.objects.filter(
        period_start__lte=today,
        status='pending'
    ).filter(
        Q(customer__representative=request.user) |
        Q(customer__representative__representative_profile__category__lt=rep_category)
    ))
    
    # Her bir PaymentRecord için ek bilgiler hesaplayalım:
    for record in pending_records:
        # Hesapla: Eğer bugünkü tarih, periyot bitiş tarihinden sonraysa,
        # kaç gün geciktiğini ve bunun yaklaşık kaç aya denk geldiğini hesaplayalım.
        if today > record.period_end:
            delta = today - record.period_end
            # Örneğin, gecikme ayı = (gün farkı // 30) + (1 eklensin, eğer kalan gün varsa)
            overdue_months = (delta.days // 30) + (1 if delta.days % 30 > 0 else 0)
        else:
            overdue_months = 0
        record.overdue_months = overdue_months
        # Ödenecek ay sayısı: Basitçe gecikme varsa, o periyot için 1 ay ücreti alınacağı varsayılabilir.
        # Eğer sistemde müşterinin birden fazla periyot geciktiği durumda ayrı PaymentRecord'lar varsa,
        # her bir record tek bir periyodu temsil eder.
        record.due_months = overdue_months  # Örneğin, geciken ay sayısı kadar alınabilir.
        
        # Hesapla: Abonelik bitiş tarihi (eğer müşteri için tanımlıysa)
        if record.customer.subscription_start_date and record.customer.subscription_duration:
            try:
                # Örneğin, subscription_duration.name alanı ay cinsinden bir sayı içeriyorsa:
                duration_months = int(record.customer.subscription_duration.name)
                # Daha doğru hesaplama için dateutil.relativedelta kullanılabilir:
                # from dateutil.relativedelta import relativedelta
                # record.subscription_end_date = record.customer.subscription_start_date + relativedelta(months=duration_months)
                # Basit hesaplama: ayı 30 gün olarak kabul ediyoruz.
                record.subscription_end_date = record.customer.subscription_start_date + timedelta(days=duration_months * 30)
            except Exception as e:
                record.subscription_end_date = None
        else:
            record.subscription_end_date = None

    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        record = get_object_or_404(PaymentRecord, id=record_id)
        record.status = 'paid'
        record.payment_date = today
        record.save()
        return redirect('rep_payment_collection')
    
    context = {
        'pending_records': pending_records,
        'today': today,
    }
    return render(request, 'core/rep_payment_collection.html', context)

@login_required
def rep_operations_history(request):
    if not (hasattr(request.user, 'representative_profile') and int(request.user.representative_profile.category) >= 2):
        return redirect('representative_dashboard')
        
    paid_records = PaymentRecord.objects.filter(
        customer__representative=request.user,
        status='paid'
    ).order_by('-payment_date')
    
    context = {
        'paid_records': paid_records,
    }
    return render(request, 'core/rep_operations_history.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_operations_history(request):
    # Tüm ödeme (tahsilat) kayıtlarını, ilgili müşteri ve temsilci bilgileri ile listeliyoruz.
    records = PaymentRecord.objects.select_related('customer', 'customer__representative').order_by('-payment_date')
    context = {
        'records': records,
    }
    return render(request, 'core/admin_operations_history.html', context)


@login_required
def create_request(request):
    # Örneğin, sadece 2. kademe ve üzeri temsilciler kayıt ekleyebilsin
    if not (hasattr(request.user, 'representative_profile') and int(request.user.representative_profile.category) >= 2):
        return redirect('representative_dashboard')
    
    if request.method == 'POST':
        form = CustomerRequestForm(request.POST)
        if form.is_valid():
            new_req = form.save(commit=False)
            new_req.representative = request.user
            # Talep eklenince status default 'pending' olarak gidecek
            new_req.save()
            return redirect('list_requests')  # Kaydı liste sayfasına yönlendirme
    else:
        form = CustomerRequestForm()
    
    return render(request, 'core/create_request.html', {'form': form})

@login_required
def list_requests(request):
    # Örneğin 2. kademe ve üzeri temsilciler tüm kayıtlarını görebilir
    if not (hasattr(request.user, 'representative_profile') and int(request.user.representative_profile.category) >= 2):
        return redirect('representative_dashboard')
    
    rep_category = int(request.user.representative_profile.category)
    
    # Eğer 3. kademe, alt kademelerin kayıtlarını da görebilsin diyorsanız:
    requests_qs = CustomerRequest.objects.filter(
        Q(representative=request.user) |
        Q(representative__representative_profile__category__lt=rep_category)
    ).select_related('customer', 'representative')

    return render(request, 'core/list_requests.html', {'requests': requests_qs})


@login_required
def list_requests_by_customer(request, customer_id):
    # Yine 2. kademe ve üzeri kontrol
    if not (hasattr(request.user, 'representative_profile') and int(request.user.representative_profile.category) >= 2):
        return redirect('representative_dashboard')
    
    rep_category = int(request.user.representative_profile.category)
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Kapsam kontrolü: Bu müşteri temsilcinin veya alt kademe temsilcinin müşterisi olmalı
    # (İsteğe bağlı)
    
    # Müşteriye ait kayıtları çekiyoruz
    requests_qs = CustomerRequest.objects.filter(customer=customer).select_related('representative')
    
    return render(request, 'core/list_requests_customer.html', {
        'customer': customer,
        'requests': requests_qs
    })

@login_required
def update_request(request, req_id):
    customer_request = get_object_or_404(CustomerRequest, id=req_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_solution = request.POST.get('solution')
        
        if new_status in ['pending', 'in_progress', 'resolved']:
            customer_request.status = new_status
            
            # Eğer 'resolved' durumuna geçiyorsa, çözülme tarihini kaydet.
            if new_status == 'resolved':
                customer_request.resolved_at = timezone.now()
            else:
                # resolved değilse, resolved_at null kalabilir
                customer_request.resolved_at = None
        
        customer_request.solution = new_solution
        customer_request.save()
        return redirect('list_requests')
    else:
        return render(request, 'core/update_request.html', {
            'request_obj': customer_request
        })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_requests_list(request):
    req_type = request.GET.get('type')         # talep, istek, sikayet
    req_status = request.GET.get('status')     # pending, in_progress, resolved
    search_query = request.GET.get('q')        # başlık/description araması
    cust_name = request.GET.get('cust_name')   # müşteri adı araması

    requests_qs = CustomerRequest.objects.select_related('customer', 'representative').all().order_by('-created_at')
    
    # Tür (talep, istek, şikayet) filtresi
    if req_type and req_type in ['talep', 'istek', 'sikayet']:
        requests_qs = requests_qs.filter(request_type=req_type)
    
    # Durum filtresi
    if req_status and req_status in ['pending', 'in_progress', 'resolved']:
        requests_qs = requests_qs.filter(status=req_status)
    
    # Başlık veya açıklama araması (q)
    if search_query:
        requests_qs = requests_qs.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    # Müşteri adı araması (cust_name)
    if cust_name:
        requests_qs = requests_qs.filter(
            Q(customer__first_name__icontains=cust_name) | Q(customer__last_name__icontains=cust_name)
        )
    
    context = {
        'requests_list': requests_qs,
        'filter_type': req_type or '',
        'filter_status': req_status or '',
        'filter_query': search_query or '',
        'filter_cust_name': cust_name or '',
    }
    return render(request, 'core/admin_requests_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_product_logs(request):
    logs_qs = ProductLog.objects.select_related('representative', 'customer', 'product').order_by('-created_at')
    
    # Filtreleme (ör. temsilci, ürün, tarih, müşteri adı vs.) eklenebilir
    
    return render(request, 'core/admin_product_logs.html', {'logs': logs_qs})

@login_required
def give_product(request):
    # Temsilci kontrolü: en az 2. kademe veya 3. kademe diyebilirsiniz
    if not (hasattr(request.user, 'representative_profile') and int(request.user.representative_profile.category) >= 2):
        return redirect('representative_dashboard')

    if request.method == 'POST':
        form = GiveProductForm(request.POST, representative_user=request.user)
        if form.is_valid():
            customer = form.cleaned_data['customer']
            product = form.cleaned_data['product']
            quantity_given = form.cleaned_data['quantity_given']
            extra_fee = form.cleaned_data['extra_fee']

            # Stok kontrolü
            if quantity_given > product.quantity:
                form.add_error('quantity_given', 'Stokta yeterli ürün yok.')
            else:
                # Stoktan düş
                product.quantity -= quantity_given
                product.save()
                
                # Log kaydı oluştur
                ProductLog.objects.create(
                    representative=request.user,
                    customer=customer,
                    product=product,
                    quantity_given=quantity_given,
                    extra_fee=extra_fee
                )
                return redirect('representative_dashboard')  # veya 'list_product_logs'
    else:
        form = GiveProductForm(representative_user=request.user)
    
    return render(request, 'core/give_product.html', {'form': form})

@login_required
def list_product_logs(request):
    # Temsilci, kendi verdiği ürün kayıtlarını görebilir
    if not (hasattr(request.user, 'representative_profile') and int(request.user.representative_profile.category) >= 2):
        return redirect('representative_dashboard')
    
    # Kendi eklediği loglar
    logs_qs = ProductLog.objects.filter(representative=request.user).select_related('customer', 'product').order_by('-created_at')
    
    return render(request, 'core/list_product_logs.html', {'logs': logs_qs})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_product_logs(request):
    logs_qs = ProductLog.objects.select_related('representative', 'customer', 'product').order_by('-created_at')
    
    # Örn. Temsilci ID veya Ürün ID vs. için GET filtreleri eklenebilir
    rep_id = request.GET.get('rep')
    if rep_id:
        logs_qs = logs_qs.filter(representative__id=rep_id)
    
    return render(request, 'core/admin_product_logs.html', {'logs': logs_qs})

# core/views.py

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_product_list(request):
    products = Product.objects.all().order_by('-updated_at')
    return render(request, 'core/admin_product_list.html', {'products': products})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_product_list')
    else:
        form = ProductForm()
    return render(request, 'core/admin_product_create.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('admin_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/admin_product_edit.html', {
        'form': form,
        'product': product
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        # Ürün silme işlemi
        product.delete()
        return redirect('admin_product_list')  # Silindikten sonra listeye dön
    else:
        # GET isteği ise, önce bir onay sayfası göstermek isteyebilirsiniz
        return render(request, 'core/admin_product_delete_confirm.html', {'product': product})

# Generated by Django 5.1.4 on 2025-02-05 17:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RepresentativeProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.PositiveSmallIntegerField(choices=[(1, 'Kategori 1 (Harcama)'), (2, 'Kategori 2 (Harcama, Müşteri Ekleme)'), (3, 'Kategori 3 (Harcama, Müşteri Ekleme, Tahsilat Alma)'), (4, 'Kategori 4 (Harcama, Müşteri Ekleme, Tahsilat Alma, Araç Ekleme)')])),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='representative_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

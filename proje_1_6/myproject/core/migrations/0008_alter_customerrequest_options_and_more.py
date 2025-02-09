# Generated by Django 5.1.4 on 2025-02-10 10:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_customerrequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customerrequest',
            options={},
        ),
        migrations.AddField(
            model_name='customerrequest',
            name='solution',
            field=models.TextField(blank=True, null=True, verbose_name='Çözüm Notu'),
        ),
        migrations.AlterField(
            model_name='customerrequest',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='core.customer'),
        ),
        migrations.AlterField(
            model_name='customerrequest',
            name='description',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='customerrequest',
            name='representative',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='customerrequest',
            name='request_type',
            field=models.CharField(choices=[('talep', 'Talep'), ('istek', 'İstek'), ('sikayet', 'Şikayet')], max_length=20),
        ),
        migrations.AlterField(
            model_name='customerrequest',
            name='title',
            field=models.CharField(max_length=200),
        ),
    ]

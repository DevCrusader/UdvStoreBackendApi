# Generated by Django 4.1.1 on 2022-10-17 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_api', '0013_alter_balancereplenish_admin_id_alter_order_office'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='role',
        ),
        migrations.AddField(
            model_name='customer',
            name='admin_permissions',
            field=models.BooleanField(default=False),
        ),
    ]
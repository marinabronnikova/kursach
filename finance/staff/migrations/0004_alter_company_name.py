# Generated by Django 4.1.2 on 2022-10-25 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0003_alter_company_bank_detail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='name',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
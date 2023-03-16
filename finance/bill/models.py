from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from goods.models import Product
from staff.models import Employee, Company, BankDetails


class Organization(models.Model):
    name = models.CharField(max_length=300, verbose_name="Полное наименование предприятия")
    taxes_number = models.CharField(max_length=100, verbose_name="Учетный номер плательщика")
    address = models.TextField(verbose_name="Юридический адрес предприятия")
    phone_number = PhoneNumberField(verbose_name="Телефон предприятия")
    email = models.EmailField(verbose_name="Email предприятия")
    description = models.TextField(verbose_name="Описание предприятия")
    bank_detail = models.ForeignKey(BankDetails, null=True, on_delete=models.SET_NULL)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id} {self.name} {self.email}"


class Invoice(models.Model):
    ON_REVIEW = 'На проверке'
    APPLYED = 'Выставлен'
    PAID = 'Оплачен'
    CANCELED = 'Отменен'
    INCOME = 'Поступление'
    COST = 'Расходы'

    PAYMENT_TYPES = [
        (INCOME, 'Поступление'),
        (COST, 'Расходы')
    ]

    PAYMENT_CHOICES = [
        (APPLYED, 'Выставлен'),
        (PAID, 'Оплачен'),
        (CANCELED, 'Отменен'),
        (ON_REVIEW, 'На проверке'),
    ]
    type = models.CharField(max_length=15, choices=PAYMENT_TYPES, default=INCOME, verbose_name='Тип счета')
    status = models.CharField(max_length=100, choices=PAYMENT_CHOICES,  default=ON_REVIEW)
    created_at = models.DateTimeField(auto_now_add=True)
    pay_to = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    total_price = models.DecimalField(null=True, blank=True, max_digits=8, decimal_places=2)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    approver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.id} {self.type} {self.status} - {self.created_at}"


class PaymentItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payment_items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(verbose_name='Цена за одну единицу', max_digits=8, decimal_places=2)
    amount = models.PositiveIntegerField(verbose_name='Количество продуктов или услуг')






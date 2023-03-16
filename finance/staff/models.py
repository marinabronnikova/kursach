from django.db import models
from django.contrib.auth.models import User


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100, null=True, verbose_name="Должность работника")
    company = models.ForeignKey("Company", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.email} {self.position}"


class Company(models.Model):
    bank_detail = models.OneToOneField("BankDetails", on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.id} {self.name}"


class BankDetails(models.Model):
    name = models.CharField(max_length=300, verbose_name="Полное наименование банка")
    address = models.TextField(verbose_name="Aдрес Банка")
    bank_number = models.CharField(max_length=100, verbose_name="Банковский идентификационный код")
    settlement_account = models.CharField(max_length=100, verbose_name="Расчетный счет для оплаты")
    details = models.TextField(verbose_name="Дополнительные сведения", blank=True, null=True)

    def __str__(self):
        return f"{self.id} {self.name}"

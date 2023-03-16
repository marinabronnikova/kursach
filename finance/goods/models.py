from django.db import models

from staff.models import Company


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название категории продукта или услуги")

    def __str__(self):
        return f"{self.id} {self.name}"


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название продукта или услуги")
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    producer = models.CharField(max_length=200, verbose_name="Производителель продукта или услуги")
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id} {self.name} {self.producer}"

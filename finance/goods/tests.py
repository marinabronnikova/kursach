from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from goods.models import Category, Product
from staff.models import Company, Employee

User = get_user_model()


class ProductTestCase(TestCase):
    def setUp(self):
        # создаем данные в базе данные перед запуском тест кейса
        self.user = User.objects.create_user('test', 'test@mail.com', 'testingpassword')
        self.company = Company.objects.create(name="test", description="description")
        self.employee = Employee.objects.create(position="position", company=self.company,
                                                user=self.user)

        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()  # клиент через который делаются запросы на API

    def test_product_failed_auth(self):
        url = reverse('product-list-create')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + "failed-token")
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_product(self):
        test_category = Category.objects.create(name="test_category")
        url = reverse('product-list-create')
        test_data = {"name": "name", "description": "description",
                     "producer": "producer", "category": test_category.id}

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_product = Product.objects.get(id=response.data["id"])
        self.assertEqual(created_product.name, "name")
        self.assertEqual(created_product.category.id, test_category.id)

    def test_create_without_name_product(self):
        test_category = Category.objects.create(name="test_category")
        url = reverse('product-list-create')
        test_data = {"description": "description",
                     "producer": "producer", "category": test_category.id}

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.data["name"][0].title(), "This Field Is Required.")

    def test_product_list(self):
        # создаем тестовый продукт
        test_category = Category.objects.create(name="test_category")
        test_product = Product.objects.create(name="test", description="test desc",
                                              category=test_category, producer="test",
                                              company=self.company)

        url = reverse('product-list-create')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], test_product.name)
        self.assertEqual(response.data[0]["description"],
                         test_product.description)
        self.assertEqual(response.data[0]["producer"],
                         test_product.producer)
        self.assertEqual(response.data[0]["category"]["name"],
                         test_category.name)

    def test_update_product(self):
        test_category = Category.objects.create(name="test_category")
        test_product = Product.objects.create(name="test", description="test desc",
                                              category=test_category, producer="test",
                                              company=self.company)

        url = reverse('product-delete-update', args=[test_product.id])
        test_data = {"name": "updated", "description": "description",
                     "producer": "producer", "category": test_category.id}

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.put(url, test_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        created_product = Product.objects.get(id=test_product.id)
        self.assertEqual(created_product.name, "updated")

    def test_delete_product(self):
        test_category = Category.objects.create(name="test_category")
        test_product = Product.objects.create(name="test", description="test desc",
                                              category=test_category, producer="test",
                                              company=self.company)

        url = reverse('product-delete-update', args=[test_product.id])
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        product = Product.objects.filter(id=test_product.id)
        self.assertEqual(len(product), 0)

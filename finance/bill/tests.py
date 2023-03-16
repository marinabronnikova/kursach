import datetime
import decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token

from bill.models import Organization, Invoice, PaymentItem
from goods.models import Category, Product
from staff.models import Company, Employee, BankDetails
from rest_framework.test import APIClient

User = get_user_model()


class InvoiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@mail.com', 'testingpassword')
        self.company = Company.objects.create(name="test", description="description")
        self.employee = Employee.objects.create(position="position", company=self.company,
                                                user=self.user)

        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()  # клиент через который делаются запросы на API

    def test_create_invoice(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        url = reverse('invoices-list')  # создание урла по псевдониму из urls.py

        # создаем тестовый продукт
        test_category = Category.objects.create(name="test_category")
        test_product = Product.objects.create(name="test", description="test desc",
                                              category=test_category, producer="test",
                                              company=self.company)

        test_data = {"type": "Поступление",
                     "approver": self.employee.id, "organization": test_organization.id,
                     "payment_items": [{
                         "product_id": test_product.id,
                         "amount": 2,
                         "price": "10.00"
                     }]
                     }

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        actual_invoice = Invoice.objects.get(id=response.data.get("id"))
        self.assertIsNotNone(actual_invoice.created_at)
        self.assertEqual(actual_invoice.status, Invoice.ON_REVIEW)

        self.assertEqual(actual_invoice.total_price, decimal.Decimal("20.00"))
        self.assertEqual(len(PaymentItem.objects.all()), 1)
        self.assertEqual(PaymentItem.objects.first().invoice, actual_invoice)
        self.assertEqual(PaymentItem.objects.first().product, test_product)

    def test_create_invoice_without_approver(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        url = reverse('invoices-list')  # создание урла по псевдониму из urls.py

        # создаем тестовый продукт
        test_category = Category.objects.create(name="test_category")
        test_product = Product.objects.create(name="test", description="test desc",
                                              category=test_category, producer="test",
                                              company=self.company)

        test_data = {"type": "Поступление",
                    "organization": test_organization.id,
                     "payment_items": [{
                         "product_id": test_product.id,
                         "amount": 2,
                         "price": "10.00"
                     }]
                     }

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_invoice_with_wrong_approver(self):
        user = User.objects.create_user('test1', 't1est@mail.com', 'testingpassword')
        another_company = Company.objects.create(name="test", description="description")
        another_employee = Employee.objects.create(position="position", company=another_company,
                                                user=user)
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        url = reverse('invoices-list')  # создание урла по псевдониму из urls.py

        # создаем тестовый продукт
        test_category = Category.objects.create(name="test_category")
        test_product = Product.objects.create(name="test", description="test desc",
                                              category=test_category, producer="test",
                                              company=self.company)

        test_data = {"type": "Поступление",
                     "approver": another_employee.id, "organization": test_organization.id,
                     "payment_items": [{
                         "product_id": test_product.id,
                         "amount": 2,
                         "price": "10.00"
                     }]
                     }

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0].title(), "Проверяющий Должен Быть Из Той Же Компании!")

    def test_create_invoice_with_wrong_product(self):
        another_company = Company.objects.create(name="test", description="description")

        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        url = reverse('invoices-list')  # создание урла по псевдониму из urls.py

        # создаем тестовый продукт
        test_category = Category.objects.create(name="test_category")
        another_company_product = Product.objects.create(name="test", description="test desc",
                                              category=test_category, producer="test",
                                              company=another_company)

        test_data = {"type": "Поступление",
                     "approver": self.employee.id, "organization": test_organization.id,
                     "payment_items": [{
                         "product_id": another_company_product.id,
                         "amount": 2,
                         "price": "10.00"
                     }]
                     }

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0].title(), "Услуга В Счете Должна Быть Из Той Же Компании!")

    def test_change_status_invoice_to_applyed(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        test_invoice = Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company)
        url = reverse('invoice-status', args=[test_invoice.id])  # создание урла по псевдониму из urls.py

        test_data = {"status": "Выставлен"}

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_invoice = Invoice.objects.get(id=test_invoice.id)
        self.assertEqual(actual_invoice.status, "Выставлен")

    def test_change_status_applyed_invoice_to_paid(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        test_invoice = Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company,
                                              status="Выставлен")
        url = reverse('invoice-status', args=[test_invoice.id])  # создание урла по псевдониму из urls.py

        test_data = {"status": "Оплачен"}

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_invoice = Invoice.objects.get(id=test_invoice.id)
        self.assertEqual(actual_invoice.status, "Оплачен")

    def test_change_status_wrong_approver(self):
        user = User.objects.create_user('test1', 't1est@mail.com', 'testingpassword')
        another_employee = Employee.objects.create(position="position", company=self.company,
                                                user=user)
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        test_invoice = Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=another_employee, company=self.company,
                                              status='На проверке')
        url = reverse('invoice-status', args=[test_invoice.id])  # создание урла по псевдониму из urls.py

        test_data = {"status": "Выставлен"}

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"].title(), 'Только Начальник Может Подтвердить Или Отменить Заказ')

    def test_change_status_applyed_invoice_to_cancel(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        test_invoice = Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company,
                                              status="Выставлен")
        url = reverse('invoice-status', args=[test_invoice.id])  # создание урла по псевдониму из urls.py

        test_data = {"status": "Отменен"}

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_invoice = Invoice.objects.get(id=test_invoice.id)
        self.assertEqual(actual_invoice.status, "Отменен")

    def test_change_status_wrong_status(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        test_invoice = Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company,)
        url = reverse('invoice-status', args=[test_invoice.id])  # создание урла по псевдониму из urls.py

        test_data = {"status": "Оплачен"}

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(url, test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response.data["message"].title(), 'Статус не может быть обновлен на Оплачен'

    def test_get_invoice_report(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company, status=Invoice.PAID)
        url = reverse('invoice-report')  # создание урла по псевдониму из urls.py

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_invoice(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        url = reverse('invoices-list')  # создание урла по псевдониму из urls.py

        Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company, status=Invoice.PAID)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["type"], "Поступление")
        self.assertEqual(response.data[0]["status"], "Оплачен")
        self.assertIsNotNone(response.data[0]["created_at"])
        self.assertEqual(response.data[0]["organization"]["id"], test_organization.id)
        self.assertEqual(response.data[0]["approver"]["id"], self.employee.id)

    def test_list_review_invoice(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        invoice_on_review = Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company, status=Invoice.ON_REVIEW)
        invoice_paid = Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company, status=Invoice.PAID)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get("/api/invoices/review", format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], invoice_on_review.id)
        self.assertEqual(response.data[0]["type"], "Поступление")
        self.assertEqual(response.data[0]["status"], "На проверке")
        self.assertIsNotNone(response.data[0]["created_at"])
        self.assertEqual(response.data[0]["organization"]["id"], test_organization.id)
        self.assertEqual(response.data[0]["approver"]["id"], self.employee.id)

    def test_stats_invoice(self):
        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        test_category = Category.objects.create(name="test_category")
        test_product = Product.objects.create(name="test", description="test desc",
                                              category=test_category, producer="test",
                                              company=self.company)

        invoice_paid = Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company, status=Invoice.PAID,
                                              total_price="20.00", paid_at=datetime.datetime.now())

        PaymentItem.objects.create(invoice=invoice_paid, product=test_product, price="10.00", amount=2)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(reverse("daily-stats"), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["income"]["price"], decimal.Decimal("20.00"))
        self.assertEqual(response.data["income"]["amount"], 1)
        self.assertEqual(response.data["costs"]["price"], None)
        self.assertEqual(response.data["costs"]["amount"], 0)

    @patch("bill.views.send_customer_invoice")
    def test_send_customer_invoice(self, mock):
        mock.return_value = MagicMock()

        test_organization = Organization.objects.create(company=self.company,
                                                        name="name",
                                                        taxes_number="taxes_number",
                                                        address="address",
                                                        phone_number="+376291234567",
                                                        email="email@mail.com",
                                                        description="description")
        invoice = Invoice.objects.create(type="Поступление", organization=test_organization,
                                              approver=self.employee, company=self.company, status=Invoice.APPLYED,
                                              total_price="20.00", paid_at=datetime.datetime.now())
        details = BankDetails.objects.create(name="name", address="address",
                                   bank_number="bank_number", settlement_account="settlement_account")
        self.company.bank_detail = details
        self.company.save()

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(reverse("invoice-sending", args=[invoice.id]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["message"], "Email был отправлен!")
        mock.assert_called_once()

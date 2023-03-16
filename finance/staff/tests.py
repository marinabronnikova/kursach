from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from staff.models import Company, Employee

User = get_user_model()


class EmployeeTestCase(TestCase):
    def setUp(self): # метод для создания объектов базе данные нужных для каждого теста
        self.user = User.objects.create_user('test@mail.com', 'test@mail.com', 'testingpassword', is_staff=True)
        self.company = Company.objects.create(name="test", description="description")
        self.employee = Employee.objects.create(position="position", company=self.company,
                                                user=self.user)

        self.token = Token.objects.create(user=self.user) # создание токена нужного для авторизации пользователя
        self.client = APIClient()  # клиент через который делаются запросы на API

    #patch нужен не вызывать какую-то функцию, а просто вернуть какние данные
    @patch("staff.views.send_staff_invitation")
    def test_send_staff_invite(self, mock):
        mock.return_value = MagicMock()

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post("/api/employees/invite-staff", {"email": "test1@mail.com"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["message"], "Email был отправлен!")
        mock.assert_called_once()
        empl = User.objects.filter(email="test1@mail.com")
        self.assertEqual(len(empl), 1)

    def test_employee_list(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get("/api/employees/", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], self.employee.id)
        self.assertEqual(response.data[0]["position"], self.employee.position)
        self.assertEqual(response.data[0]["company"]["id"], self.company.id)
        self.assertEqual(response.data[0]["user"]["id"], self.user.id)

    def test_singup(self):
        response = self.client.post("/api/signup/", {
            "email": "testing@email.com", "password": "8gX^&k3s3118"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User created successfully")
        user = User.objects.filter(email="testing@email.com")
        self.assertEqual(len(user), 1)
        empl = Employee.objects.filter(user=user[0])
        self.assertEqual(len(empl), 1)

    def test_user_already_created_singup(self):
        response = self.client.post("/api/signup/", {
            "email": self.user.email, "password": "8gX^&k3s3118"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "Пользователь с таким email уже существует")

    def test_log_in(self):
        response = self.client.post("/api/login/", {
            "email": "test@mail.com", "password": "testingpassword"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["token"])
        self.assertEqual(response.data["user"]["id"], self.user.id)

    def test_log_in_failed(self):
        response = self.client.post("/api/login/", {
            "email": "wrong-email@mail.com", "password": "testingpassword"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print(response.data)
        self.assertEqual(response.data["non_field_errors"][0].title(), "Unable To Log In With Provided Credentials.")
from django.contrib.auth.models import User
from django.db.transaction import atomic
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from staff.models import Company, Employee
from staff.serializers import CompanySerializer, EmployeeSerializer, UserSerializer, \
    SignUpSerializer, LoginSerializer, StaffInvitationSerializer
from staff.services.emailing import send_staff_invitation


class IsEmployeeCompany(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.employee is None:
            return False
        return obj == request.user.employee.company


class CompanyViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                     mixins.DestroyModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(id=self.request.user.employee.company.id)


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        return super().get_queryset().filter(company=self.request.user.employee.company)

    @action(detail=False, methods=['post'])
    @atomic
    def send_staff_invite(self, request, pk=None):
        employer = request.user.employee
        if not employer.user.is_staff:
            raise ValidationError({"message": "Только менеджер может приглашать сотрудников"})

        serializer = StaffInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = User.objects.make_random_password(10)
        email = serializer.validated_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError({"message": "Пользователь уже существует"})
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        Employee.objects.create(user=user, company=employer.company)
        send_staff_invitation(user_email=email,
                              password=password,
                              company_name=employer.company.name
                              )
        return Response({'message': 'Email был отправлен!'})


class SignUpView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = ()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class LoginView(ObtainAuthToken):
    serializer_class = LoginSerializer
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": UserSerializer(instance=user).data}
        )

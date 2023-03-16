from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db.transaction import atomic
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from staff.models import Employee, Company, BankDetails


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    bank_detail = BankDetailsSerializer()

    class Meta:
        model = Company
        fields = '__all__'

    @atomic
    def update(self, instance, validated_data):
        bank_detail = validated_data.pop('bank_detail')

        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        bank_instance = instance.bank_detail if instance.bank_detail else BankDetails()
        bank_instance.name = bank_detail.get('name', bank_instance.name)
        bank_instance.address = bank_detail.get('address', bank_instance.address)
        bank_instance.bank_number = bank_detail.get('bank_number', bank_instance.bank_number)
        bank_instance.settlement_account = bank_detail.get('settlement_account',
                                                           bank_instance.settlement_account)
        bank_instance.details = bank_detail.get('details', bank_instance.details)

        bank_instance.save()
        if instance.bank_detail is None:
            instance.bank_detail = bank_instance
            instance.save()
        return instance


class EmployeeSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'company', 'position', 'user', ]

    @atomic
    def update(self, instance, validated_data):
        instance.position = validated_data.get('position', instance.position)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        label=_("email"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                username=email, email=email,  password=password)

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "password",
        ]

        extra_kwargs = {
            "email": {
                "write_only": True,
            },
            "password": {"write_only": True, "min_length": 8,
                         "style": {'input_type': 'password', 'placeholder': 'Password'}
                         },
        }

    @atomic
    def create(self, validated_data):
        if User.objects.filter(username=validated_data.get("email")).exists():
            raise ValidationError({"email": ["Пользователь с таким email уже существует"]})
        user = User.objects.create_user(username=validated_data.get("email"), is_staff=True, **validated_data, is_superuser=True)
        company = Company.objects.create()
        Employee.objects.create(user=user, company=company)
        return user


class StaffInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', )





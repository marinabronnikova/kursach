from decimal import Decimal

from django.db.transaction import atomic
from rest_framework import serializers

from bill.models import Organization, Invoice, PaymentItem
from bill.services.helpers import CurrentCompanyDefault
from goods.models import Product
from goods.serializers import ProductSerializer
from staff.models import BankDetails
from staff.serializers import EmployeeSerializer, BankDetailsSerializer, CompanySerializer


class OrganizationSerializer(serializers.ModelSerializer):
    bank_detail = BankDetailsSerializer()
    company = CompanySerializer(write_only=True, default=CurrentCompanyDefault())

    @atomic
    def create(self, validated_data):
        bank_details = validated_data.pop('bank_detail')
        users_company = validated_data.pop('company')
        bank_details_instance = BankDetails.objects.create(**bank_details)
        organization = Organization.objects.create(bank_detail=bank_details_instance,
                                                   company=users_company,
                                                   **validated_data)
        return organization

    @atomic
    def update(self, instance, validated_data):
        bank_details = validated_data.pop('bank_detail')

        instance.name = validated_data.get('name', instance.name)
        instance.taxes_number = validated_data.get('taxes_number', instance.taxes_number)
        instance.address = validated_data.get('address', instance.address)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.email = validated_data.get('email', instance.email)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        bank_details_instance = instance.bank_detail
        bank_details_instance.name = bank_details.get('name', bank_details_instance.name)
        bank_details_instance.address = bank_details.get('address', bank_details_instance.address)
        bank_details_instance.bank_number = bank_details.get('bank_number', bank_details_instance.bank_number)
        bank_details_instance.settlement_account = bank_details.get('settlement_account', bank_details_instance.settlement_account)
        bank_details_instance.details = bank_details.get('details', bank_details_instance.details)

        bank_details_instance.save()
        return instance

    class Meta:
        model = Organization
        fields = ['id', 'name', 'taxes_number', 'address', 'phone_number', 'email',
                  'description', 'bank_detail', 'company']


class PaymentItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = PaymentItem
        fields = ['id', 'price', 'amount', 'product', 'product_id']


class ReviewInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ('status', )


class InvoiceSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    approver = EmployeeSerializer(read_only=True)
    payment_items = PaymentItemSerializer(many=True)
    company = CompanySerializer(write_only=True, default=CurrentCompanyDefault())

    class Meta:
        model = Invoice
        fields = ['id', 'type', 'status', 'created_at', 'pay_to', 'paid_at',
                  'total_price', 'organization', 'approver', 'payment_items', 'company']

        extra_kwargs = {'total_price': {'read_only': True},
                        'status': {'read_only': True},
                        'created_at': {'read_only': True}}

    @atomic
    def create(self, validated_data):
        organization = validated_data.pop('organization')
        approver = validated_data.pop('approver')
        users_company = validated_data.pop('company')
        payments = validated_data.pop('payment_items')

        if approver.company != users_company:
            raise serializers.ValidationError("Проверяющий должен быть из той же компании!")
        if organization.company != users_company:
            raise serializers.ValidationError("Организация в счете должна быть из той же компании!")

        invoice = Invoice.objects.create(**validated_data, approver=approver, company=users_company,
                               organization=organization)

        total_price = Decimal(0)
        for item in payments:
            total_price += item['price'] * item['amount']
            product = Product.objects.get(pk=item.pop('product_id'))
            if product.company != users_company:
                raise serializers.ValidationError(
                    "Услуга в счете должна быть из той же компании!")
            PaymentItem.objects.create(product=product, invoice=invoice, **item)

        invoice.total_price = total_price
        invoice.save()

        return invoice
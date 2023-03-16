
from django.db.transaction import atomic
from rest_framework import serializers

from bill.services.helpers import CurrentCompanyDefault
from goods.models import Product, Category
from staff.serializers import CompanySerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', ]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    company = CompanySerializer(write_only=True, default=CurrentCompanyDefault())

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'category', 'producer', 'company']

    @atomic
    def create(self, validated_data):
        category = validated_data.pop('category')
        users_company = validated_data.pop('company')
        instance = Product.objects.create(**validated_data, category=category,
                                                       company=users_company)
        return instance

    # def update(self, instance, validated_data):
    #     category = validated_data.pop('category')
    #     users_company = validated_data.pop('company')
    #
    #     instance.category = category or instance.category
    #     instance.name = validated_data.get('name', instance.name)
    #     instance.producer = validated_data.get('producer', instance.producer)
    #     instance.description = validated_data.get('description', instance.description)
    #     instance.save()
    #
    #     return instance


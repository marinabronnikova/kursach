from django.contrib import admin

from goods.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    readonly_fields = ("company", )
    search_fields = ('name', 'description', 'category__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        company = request.user.employee.company
        return qs.filter(company=company)

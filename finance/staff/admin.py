from django.contrib import admin
from django.db.models import Q

from staff.models import Employee, Company, BankDetails


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('position', 'company', 'email_view')
    readonly_fields = ('company', 'user')
    search_fields = ('user__email', )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        company = request.user.employee.company
        return qs.filter(company=company)

    @admin.display(empty_value='-')
    def email_view(self, obj):
        return obj.user.email


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        company = request.user.employee.company
        return qs.filter(id=company.id)

    readonly_fields = ('bank_detail', )


@admin.register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        company = request.user.employee.company

        return qs.filter(Q(organization__company=company) | Q(company=company))




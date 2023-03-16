from django.contrib import admin

from bill.models import Invoice, Organization, PaymentItem
from staff.models import BankDetails


class PaymentItemInline(admin.TabularInline):
    model = PaymentItem
    readonly_fields = ['invoice', 'product', 'price', 'amount']


class BankDetailsItemInline(admin.TabularInline):
    model = BankDetails


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    readonly_fields = ('type', 'status', 'created_at', 'pay_to', 'paid_at', 'total_price',
                       'organization', 'approver', 'company')
    search_fields = ["organization__name"]
    list_filter = ('type', 'status')
    inlines = [PaymentItemInline, ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        company = request.user.employee.company
        return qs.filter(company=company)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    readonly_fields = ('company', 'bank_detail')
    search_fields = ["name"]
    # inlines = [BankDetailsItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        company = request.user.employee.company
        return qs.filter(company=company)

# @admin.register(PaymentItem)
# class PaymentItemAdmin(admin.ModelAdmin):
#     pass

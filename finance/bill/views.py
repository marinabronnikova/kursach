import datetime
from itertools import chain

from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncYear
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from bill.csv_stream import CSVStream
from bill.models import Invoice, Organization
from bill.serializers import InvoiceSerializer, OrganizationSerializer, ReviewInvoiceSerializer
from bill.services.emailing import send_customer_invoice
from staff.models import Employee


class InvoiceFilter(filters.FilterSet):
    paid_at = filters.DateFromToRangeFilter()

    class Meta:
        model = Invoice
        fields = ['paid_at', 'status', 'created_at', 'type']


class InvoiceViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filterset_class = InvoiceFilter
    search_fields = ["organization__name"]
    ordering = ['-created_at']

    def get_queryset(self):
        return super().get_queryset().filter(company=self.request.user.employee.company)

    def create(self, request, *args, **kwargs):
        organization = get_object_or_404(Organization, id=request.data.get('organization'))
        approver = get_object_or_404(Employee, id=request.data.get('approver'))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(organization=organization, approver=approver)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'])
    @atomic
    def change_invoice_status(self, request, pk=None):
        invoice = self.get_object()
        serializer = ReviewInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice_status = serializer.validated_data.get('status')

        if invoice.status == invoice.ON_REVIEW:
            if not request.user.employee == invoice.approver:
                raise ValidationError({"message": 'Только начальник может подтвердить или отменить заказ'})
            if invoice_status in (Invoice.CANCELED, Invoice.APPLYED):
                invoice.status = invoice_status
                invoice.save()
            else:
                raise ValidationError(
                    {"message": f'Статус не может быть обновлен на {invoice_status}'})

        elif invoice.status == invoice.APPLYED:
            if invoice_status in (Invoice.PAID, Invoice.CANCELED):
                if invoice_status == Invoice.PAID:
                    invoice.paid_at = datetime.datetime.now()
                invoice.status = invoice_status
                invoice.save()
            else:
                raise ValidationError(
                    {"message": f'Статус не может быть обновлен на {invoice_status}'})

        else:
            raise ValidationError(
                {"message": f'Статус не может быть обновлен на {invoice_status}'})

        return Response({'status': f'Статус счета был изменен на {invoice.status}'})

    @action(detail=False, methods=['get'])
    @atomic
    def get_invoice_report(self, request, pk=None):
        invoices = self.filter_queryset(self.get_queryset())\
            .select_related('approver', 'organization')\
            .filter(status=Invoice.PAID)\
            .filter(company=request.user.employee.company)\
            .values_list('id', 'created_at', 'pay_to', 'paid_at', 'total_price',
                                                'organization__name', 'approver__position',
                                                'approver__user__email')

        fieldnames = ['id', 'Создано', 'Оплатить до', 'Оплачено', 'Cумма счета',
                      'Организация, кому выставлен счет', 'Должность проверяющего',
                      'Email проверяющего']

        file_name = f'Report invoices {datetime.datetime.now()}'
        csv_stream = CSVStream()

        # Stream (download) the file
        return csv_stream.export(file_name, fieldnames, invoices)

    @action(detail=False, methods=['get'])
    @atomic
    def review_invoices(self, request, pk=None):
        q = self.get_queryset().filter(approver=request.user.employee, status=Invoice.ON_REVIEW)
        serializer = self.get_serializer(q, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    @atomic
    def daily_statistic(self, request, pk=None):
        now = datetime.date.today()
        q = self.get_queryset().filter(paid_at__year=now.year,
                                       paid_at__month=now.month,
                                       paid_at__day=now.day)
        costs = q.filter(status=Invoice.PAID, type=Invoice.COST)
        costs_price = costs.aggregate(costs=Sum('total_price'))
        amount_of_costs = costs.count()

        income = q.filter(status=Invoice.PAID, type=Invoice.INCOME)
        current_amount_paid_of_invoices = income.count()
        price = income.aggregate(income=Sum('total_price'))
        return Response({'income': {'price': price['income'], 'amount': current_amount_paid_of_invoices},
                         'costs': {'price': costs_price['costs'], 'amount': amount_of_costs}})

    @action(detail=True, methods=['post'])
    @atomic
    def send_customer_invoice(self, request, pk=None):
        bank_details = request.user.employee.company.bank_detail
        invoice = self.get_object()
        if bank_details is None:
            raise ValidationError({"message": "Заполните данные о компании!"})

        if invoice.type != Invoice.INCOME or invoice.status != Invoice.APPLYED:
            raise ValidationError({"message": "Неверный статус или тип!"})
        send_customer_invoice(request.user.employee.company, invoice)
        return Response({'message': 'Email был отправлен!'})

    @action(detail=False, methods=['get'])
    @atomic
    def stats_invoices(self, request, pk=None):
        date_from = datetime.datetime.now() - datetime.timedelta(days=365)

        income_data = self.get_queryset().filter(type=Invoice.INCOME, status=Invoice.PAID)\
            .filter(paid_at__gte=date_from)\
            .annotate(month=TruncMonth("paid_at")) \
            .values("month", year=TruncYear("month"))\
            .annotate(total_price=Sum("total_price"))
        costs_data = self.get_queryset().filter(type=Invoice.COST, status=Invoice.PAID)\
            .filter(paid_at__gte=date_from)\
            .annotate(month=TruncMonth("paid_at")) \
            .values("month", year=TruncYear("month"))\
            .annotate(total_price=Sum("total_price"))

        income_count_data = self.get_queryset().filter(type=Invoice.INCOME, status=Invoice.PAID)\
            .filter(paid_at__gte=date_from)\
            .annotate(month=TruncMonth("paid_at")) \
            .values("month", year=TruncYear("month"))\
            .annotate(counts=Count("total_price"))

        return Response({"income_data": income_data,
                         "costs_data": costs_data,
                         "income_count_data": income_count_data})


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    search_fields = ["name", "address"]

    def get_queryset(self):
        return super().get_queryset().filter(company=self.request.user.employee.company)

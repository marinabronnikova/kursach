from django.urls import path, include
from rest_framework import routers

from bill.views import InvoiceViewSet, OrganizationViewSet


urlpatterns = [
    path('invoices/', InvoiceViewSet.as_view({'get': 'list', 'post': 'create'}), name="invoices-list"),
    path('invoices/<int:pk>', InvoiceViewSet.as_view({'get': 'retrieve'}), name="invoice-detail"),

    path('invoices/<int:pk>/change-status', InvoiceViewSet.as_view({'post': 'change_invoice_status'}), name="invoice-status"),
    path('invoices/invoices-report',
         InvoiceViewSet.as_view({'get': 'get_invoice_report'}), name="invoice-report"),
    path('invoices/daily_stats',
         InvoiceViewSet.as_view({'get': 'daily_statistic'}), name="daily-stats"),
    path('invoices/stats',
         InvoiceViewSet.as_view({'get': 'stats_invoices'}), name="stats"),
    path('invoices/<int:pk>/send-customer-invoice',
         InvoiceViewSet.as_view({'post': 'send_customer_invoice'}), name="invoice-sending"),

    path('invoices/review', InvoiceViewSet.as_view({'get': 'review_invoices'})),
    path('organizations/', OrganizationViewSet.as_view({'post': 'create', 'get': 'list'})),
    path('organizations/<int:pk>', OrganizationViewSet.as_view({'delete': 'destroy', 'put': 'update', 'get': 'retrieve'}))
]

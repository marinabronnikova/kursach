from django.urls import path

from staff.views import CompanyViewSet, EmployeeViewSet, SignUpView, LoginView

urlpatterns = [
    path('companies/',
         CompanyViewSet.as_view({'get': 'list'})),

    path('companies/<int:pk>',
         CompanyViewSet.as_view({'delete': 'destroy', 'put': 'update', 'get': 'retrieve'})),
    path('employees/', EmployeeViewSet.as_view({'post': 'create', 'get': 'list'})),
    path('employees/<int:pk>',
         EmployeeViewSet.as_view({'delete': 'destroy', 'put': 'update', 'get': 'retrieve'})),
    path('employees/invite-staff', EmployeeViewSet.as_view({"post": "send_staff_invite"})),

    path('signup/', SignUpView.as_view({'post': 'create'})),
    path('login/', LoginView.as_view())

]

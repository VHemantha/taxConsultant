from django.urls import path
from .views import (
    RegisterClientView,
    ClientListView,
    ClientDetailView,
    MyProfileView,
    ConsultantDashboardStatsView,
    SuperAdminDashboardView,
    ConsultantListView,
    ClientAssessmentYearsView,
    CreateConsultantView,
    ConsultantDetailView,
    TransferClientsView,
    AccountsDivisionListView,
    CreateAccountsDivisionView,
    AccountsDivisionDetailView,
)

urlpatterns = [
    path('register/', RegisterClientView.as_view(), name='register_client'),
    path('', ClientListView.as_view(), name='client_list'),
    path('<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
    path('<int:pk>/assessment-years/', ClientAssessmentYearsView.as_view(), name='client_assessment_years'),
    path('my-profile/', MyProfileView.as_view(), name='my_profile'),
    path('dashboard/stats/', ConsultantDashboardStatsView.as_view(), name='dashboard_stats'),
    path('super-admin/stats/', SuperAdminDashboardView.as_view(), name='super_admin_stats'),
    path('consultants/', ConsultantListView.as_view(), name='consultant_list'),
    path('consultants/create/', CreateConsultantView.as_view(), name='create_consultant'),
    path('consultants/<int:pk>/', ConsultantDetailView.as_view(), name='consultant_detail'),
    path('consultants/transfer/', TransferClientsView.as_view(), name='transfer_clients'),
    path('accounts-division/', AccountsDivisionListView.as_view(), name='accounts_division_list'),
    path('accounts-division/create/', CreateAccountsDivisionView.as_view(), name='create_accounts_division'),
    path('accounts-division/<int:pk>/', AccountsDivisionDetailView.as_view(), name='accounts_division_detail'),
]

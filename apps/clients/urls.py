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
]

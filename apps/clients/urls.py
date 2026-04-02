from django.urls import path
from .views import (
    RegisterClientView,
    ClientListView,
    ClientDetailView,
    MyProfileView,
    ConsultantDashboardStatsView,
)

urlpatterns = [
    path('register/', RegisterClientView.as_view(), name='register_client'),
    path('', ClientListView.as_view(), name='client_list'),
    path('<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
    path('my-profile/', MyProfileView.as_view(), name='my_profile'),
    path('dashboard/stats/', ConsultantDashboardStatsView.as_view(), name='dashboard_stats'),
]

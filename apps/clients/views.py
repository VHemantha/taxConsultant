from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from .models import ClientProfile
from .serializers import ClientProfileSerializer, RegisterClientSerializer, ClientListSerializer
from apps.notifications.models import Notification

User = get_user_model()


class IsConsultant(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'consultant'


class RegisterClientView(APIView):
    permission_classes = [IsConsultant]

    def post(self, request):
        serializer = RegisterClientSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user, profile = serializer.save()
            Notification.objects.create(
                recipient=user,
                title='Welcome to Tax Automation Portal',
                message=f'Your account has been created. Please log in with your credentials and change your password.',
                notification_type='info',
            )
            return Response({
                'message': 'Client registered successfully.',
                'client_id': profile.id,
                'email': user.email,
                'username': user.username,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientListView(generics.ListAPIView):
    serializer_class = ClientListSerializer
    permission_classes = [IsConsultant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['full_name', 'tin', 'user__email']
    ordering_fields = ['full_name', 'created_at', 'status']

    def get_queryset(self):
        return ClientProfile.objects.filter(
            assigned_consultant=self.request.user
        ).select_related('user')


class ClientDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        client_id = self.kwargs.get('pk')
        if self.request.user.role == 'consultant':
            return ClientProfile.objects.get(id=client_id, assigned_consultant=self.request.user)
        else:
            return self.request.user.client_profile

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.client_profile


class ConsultantDashboardStatsView(APIView):
    permission_classes = [IsConsultant]

    def get(self, request):
        clients = ClientProfile.objects.filter(assigned_consultant=request.user)
        stats = {
            'total_clients': clients.count(),
            'not_started': clients.filter(status='not_started').count(),
            'in_progress': clients.filter(status='in_progress').count(),
            'pending_review': clients.filter(status='pending_review').count(),
            'awaiting_confirmation': clients.filter(status='awaiting_confirmation').count(),
            'archived': clients.filter(status='archived').count(),
        }
        return Response(stats)

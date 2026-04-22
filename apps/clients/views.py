from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from .models import ClientProfile, ClientAssessmentYear
from .serializers import ClientProfileSerializer, RegisterClientSerializer, ClientListSerializer
from apps.notifications.models import Notification

User = get_user_model()

CONSULTANT_ROLES = ('consultant', 'handling_person')


class IsConsultant(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in CONSULTANT_ROLES


class IsSuperAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'super_admin'


class IsConsultantOrSuperAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in (*CONSULTANT_ROLES, 'super_admin')


class RegisterClientView(APIView):
    permission_classes = [IsConsultantOrSuperAdmin]

    def post(self, request):
        serializer = RegisterClientSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user, profile = serializer.save()
            Notification.objects.create(
                recipient=user,
                title='Welcome to Tax Automation Portal',
                message='Your account has been created. Please log in with your credentials and change your password.',
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
    permission_classes = [IsConsultantOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['full_name', 'tin', 'user__email']
    ordering_fields = ['full_name', 'created_at', 'status']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            consultant_id = self.request.query_params.get('consultant_id')
            qs = ClientProfile.objects.all().select_related('user', 'assigned_consultant')
            if consultant_id:
                qs = qs.filter(assigned_consultant_id=consultant_id)
            return qs
        return ClientProfile.objects.filter(
            assigned_consultant=user
        ).select_related('user')


class ClientDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        client_id = self.kwargs.get('pk')
        user = self.request.user
        if user.role in CONSULTANT_ROLES:
            return ClientProfile.objects.get(id=client_id, assigned_consultant=user)
        if user.role == 'super_admin':
            return ClientProfile.objects.get(id=client_id)
        return user.client_profile

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


class SuperAdminDashboardView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        consultants = User.objects.filter(role__in=CONSULTANT_ROLES, is_active=True)
        all_clients = ClientProfile.objects.all()

        overall = {
            'total_consultants': consultants.count(),
            'total_clients': all_clients.count(),
            'not_started': all_clients.filter(status='not_started').count(),
            'in_progress': all_clients.filter(status='in_progress').count(),
            'pending_review': all_clients.filter(status='pending_review').count(),
            'awaiting_confirmation': all_clients.filter(status='awaiting_confirmation').count(),
            'archived': all_clients.filter(status='archived').count(),
        }

        consultant_stats = []
        for consultant in consultants:
            clients = ClientProfile.objects.filter(assigned_consultant=consultant)
            consultant_stats.append({
                'id': consultant.id,
                'name': consultant.get_full_name() or consultant.email,
                'email': consultant.email,
                'total_clients': clients.count(),
                'not_started': clients.filter(status='not_started').count(),
                'in_progress': clients.filter(status='in_progress').count(),
                'pending_review': clients.filter(status='pending_review').count(),
                'awaiting_confirmation': clients.filter(status='awaiting_confirmation').count(),
                'archived': clients.filter(status='archived').count(),
            })

        return Response({'overall': overall, 'consultants': consultant_stats})


class ConsultantListView(APIView):
    permission_classes = [IsConsultantOrSuperAdmin]

    def get(self, request):
        consultants = User.objects.filter(role__in=CONSULTANT_ROLES, is_active=True)
        data = [
            {'id': c.id, 'name': c.get_full_name() or c.email, 'email': c.email}
            for c in consultants
        ]
        return Response(data)


class ClientAssessmentYearsView(APIView):
    """GET/POST assessment years assigned to a client."""
    permission_classes = [IsConsultantOrSuperAdmin]

    def _get_profile(self, pk, user):
        try:
            if user.role == 'super_admin':
                return ClientProfile.objects.get(pk=pk)
            return ClientProfile.objects.get(pk=pk, assigned_consultant=user)
        except ClientProfile.DoesNotExist:
            return None

    def get(self, request, pk):
        from apps.tax_forms.models import TaxSubmission
        profile = self._get_profile(pk, request.user)
        if not profile:
            return Response({'error': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

        assignments = ClientAssessmentYear.objects.filter(
            client=profile.user
        ).select_related('tax_year')

        data = []
        for a in assignments:
            submission = TaxSubmission.objects.filter(
                client=profile.user, tax_year=a.tax_year
            ).first()
            data.append({
                'id': a.id,
                'year_id': a.tax_year.id,
                'year_label': a.tax_year.label,
                'year': a.tax_year.year,
                'assessment_year_start': a.tax_year.assessment_year_start,
                'form_sent': a.form_sent,
                'notification_sent': a.notification_sent,
                'assigned_at': a.assigned_at,
                'submission_id': submission.id if submission else None,
                'submission_status': submission.status if submission else None,
            })
        return Response(data)

    def post(self, request, pk):
        from apps.tax_forms.models import TaxYear
        profile = self._get_profile(pk, request.user)
        if not profile:
            return Response({'error': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

        year_ids = request.data.get('year_ids', [])
        if not year_ids:
            return Response({'error': 'year_ids is required.'}, status=status.HTTP_400_BAD_REQUEST)

        years = TaxYear.objects.filter(id__in=year_ids)
        assigned = []
        for year in years:
            obj, created = ClientAssessmentYear.objects.get_or_create(
                client=profile.user, tax_year=year,
                defaults={'assigned_by': request.user}
            )
            assigned.append({'year_id': year.id, 'year_label': year.label, 'created': created})

        return Response({'assigned': assigned}, status=status.HTTP_201_CREATED)

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.http import FileResponse, Http404
from django.conf import settings
import os
import shutil

from .models import (
    TaxYear, TaxSubmission, LocalEmploymentIncome, ForeignIncome,
    TerminalBenefit, RentIncome, InterestIncome, DividendIncome,
    SoleProprietorshipIncome, OtherIncome, QualifyingPayments,
    SelfAssessmentPayment, TaxCredits, ImmovableProperty, MotorVehicle,
    BankBalance, SharesStocks, CashInHand, LoansGiven, GoldSilverJewellery,
    BusinessProperty, OtherAsset, DisposalOfAsset, Liability, DeclarantDetails,
    SubmissionEditLog,
)
from .serializers import (
    SubmissionEditLogSerializer,
    TaxYearSerializer, TaxSubmissionSerializer, TaxSubmissionListSerializer,
    LocalEmploymentIncomeSerializer, ForeignIncomeSerializer,
    TerminalBenefitSerializer, RentIncomeSerializer, InterestIncomeSerializer,
    DividendIncomeSerializer, SoleProprietorshipIncomeSerializer, OtherIncomeSerializer,
    QualifyingPaymentsSerializer, SelfAssessmentPaymentSerializer,
    TaxCreditsSerializer, ImmovablePropertySerializer, MotorVehicleSerializer,
    BankBalanceSerializer, SharesStocksSerializer, CashInHandSerializer,
    LoansGivenSerializer, GoldSilverJewellerySerializer, BusinessPropertySerializer,
    OtherAssetSerializer, DisposalOfAssetSerializer, LiabilitySerializer,
    DeclarantDetailsSerializer,
)
from .tax_calculator import calculate_full_tax
from .pdf_generator import generate_tax_submission_pdf
from apps.notifications.models import Notification
from apps.clients.models import ClientProfile
from django.contrib.auth import get_user_model

User = get_user_model()


class IsConsultant(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'consultant'


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _get_submission_for_user(submission_id, user):
    """Return TaxSubmission accessible by client or consultant (incl. orphaned clients)."""
    from django.db.models import Q
    try:
        if user.role == 'consultant':
            assigned_ids = ClientProfile.objects.filter(
                assigned_consultant=user
            ).values_list('user_id', flat=True)
            profiled_ids = ClientProfile.objects.values_list('user_id', flat=True)
            orphan_ids = User.objects.filter(
                role='client'
            ).exclude(id__in=profiled_ids).values_list('id', flat=True)
            return TaxSubmission.objects.get(
                id=submission_id,
                client_id__in=[*assigned_ids, *orphan_ids]
            )
        return TaxSubmission.objects.get(id=submission_id, client=user)
    except TaxSubmission.DoesNotExist:
        return None


def _log_edit(submission, user, section, action, old_data=None, new_data=None, description=''):
    SubmissionEditLog.objects.create(
        submission=submission,
        edited_by=user,
        section=section,
        action=action,
        old_data=old_data,
        new_data=new_data,
        description=description or f'Consultant {action} {section}',
    )


class TaxYearListView(generics.ListAPIView):
    serializer_class = TaxYearSerializer
    queryset = TaxYear.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]


class TaxSubmissionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'consultant':
            from django.db.models import Q
            # Clients assigned to this consultant
            assigned_client_ids = ClientProfile.objects.filter(
                assigned_consultant=request.user
            ).values_list('user_id', flat=True)
            # Clients with NO ClientProfile at all (orphaned — visible to all consultants)
            profiled_user_ids = ClientProfile.objects.values_list('user_id', flat=True)
            unassigned_client_ids = User.objects.filter(
                role='client'
            ).exclude(id__in=profiled_user_ids).values_list('id', flat=True)
            submissions = TaxSubmission.objects.filter(
                Q(client_id__in=assigned_client_ids) | Q(client_id__in=unassigned_client_ids)
            )
        else:
            submissions = TaxSubmission.objects.filter(client=request.user)

        serializer = TaxSubmissionListSerializer(submissions, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Client creates a new submission
        tax_year_id = request.data.get('tax_year')
        if not tax_year_id:
            return Response({'error': 'tax_year is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tax_year = TaxYear.objects.get(id=tax_year_id)
        except TaxYear.DoesNotExist:
            return Response({'error': 'Invalid tax year.'}, status=status.HTTP_404_NOT_FOUND)

        if TaxSubmission.objects.filter(client=request.user, tax_year=tax_year).exists():
            return Response({'error': 'Submission for this tax year already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        submission = TaxSubmission.objects.create(
            client=request.user,
            tax_year=tax_year,
            status='draft',
        )

        # Ensure client has a profile; auto-create linked to first consultant if missing
        profile = getattr(request.user, 'client_profile', None)
        if not profile:
            consultant = User.objects.filter(role='consultant').first()
            if consultant:
                profile = ClientProfile.objects.create(
                    user=request.user,
                    assigned_consultant=consultant,
                    full_name=request.user.get_full_name() or request.user.email,
                    status='in_progress',
                )
        if profile:
            profile.status = 'in_progress'
            profile.save(update_fields=['status'])

        return Response(TaxSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)


class TaxSubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_submission(self, pk, user):
        try:
            if user.role == 'consultant':
                client_ids = ClientProfile.objects.filter(
                    assigned_consultant=user
                ).values_list('user_id', flat=True)
                return TaxSubmission.objects.get(id=pk, client_id__in=client_ids)
            else:
                return TaxSubmission.objects.get(id=pk, client=user)
        except TaxSubmission.DoesNotExist:
            return None

    def get(self, request, pk):
        submission = self.get_submission(pk, request.user)
        if not submission:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TaxSubmissionSerializer(submission).data)

    def patch(self, request, pk):
        submission = self.get_submission(pk, request.user)
        if not submission:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Only consultants can update certain fields
        if request.user.role == 'consultant':
            allowed_fields = ['consultant_notes', 'info_request_message', 'status']
            data = {k: v for k, v in request.data.items() if k in allowed_fields}
            for field, value in data.items():
                setattr(submission, field, value)
            if 'status' in data:
                if data['status'] == 'under_review':
                    submission.reviewed_by = request.user
                    submission.reviewed_at = timezone.now()
            submission.save()
        return Response(TaxSubmissionSerializer(submission).data)


class SubmitTaxFormView(APIView):
    """Client submits the completed form."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            submission = TaxSubmission.objects.get(id=pk, client=request.user)
        except TaxSubmission.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if submission.status not in ['draft', 'info_requested']:
            return Response({'error': 'Cannot submit in current status.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate declarant details are present
        if not hasattr(submission, 'declarant_details'):
            return Response({'error': 'Declarant details are required before submission.'}, status=status.HTTP_400_BAD_REQUEST)

        submission.status = 'submitted'
        submission.submitted_at = timezone.now()
        submission.save()

        # Ensure client has a profile; auto-create linked to first consultant if missing
        profile = getattr(request.user, 'client_profile', None)
        if not profile:
            consultant = User.objects.filter(role='consultant').first()
            if consultant:
                profile = ClientProfile.objects.create(
                    user=request.user,
                    assigned_consultant=consultant,
                    full_name=request.user.get_full_name() or request.user.email,
                    status='pending_review',
                )
        if profile:
            profile.status = 'pending_review'
            profile.save(update_fields=['status'])

        # Notify consultant
        if profile and profile.assigned_consultant:
            Notification.objects.create(
                recipient=profile.assigned_consultant,
                title='New Tax Form Submission',
                message=f'{profile.full_name} has submitted their tax form for {submission.tax_year.label}. Please review.',
                notification_type='action_required',
                related_submission_id=submission.id,
            )

        return Response({'message': 'Form submitted successfully.', 'status': 'submitted'})


class RequestInfoView(APIView):
    """Consultant requests additional information from client."""
    permission_classes = [IsConsultant]

    def post(self, request, pk):
        client_ids = ClientProfile.objects.filter(
            assigned_consultant=request.user
        ).values_list('user_id', flat=True)

        try:
            submission = TaxSubmission.objects.get(id=pk, client_id__in=client_ids)
        except TaxSubmission.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        message = request.data.get('message', '')
        if not message:
            return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)

        submission.status = 'info_requested'
        submission.info_request_message = message
        submission.save()

        # Update client profile status
        profile = getattr(submission.client, 'client_profile', None)
        if profile:
            profile.status = 'in_progress'
            profile.save(update_fields=['status'])

        # Notify client
        Notification.objects.create(
            recipient=submission.client,
            title='Additional Information Required',
            message=f'Your tax consultant has requested additional information for {submission.tax_year.label}: {message}',
            notification_type='action_required',
            related_submission_id=submission.id,
        )

        return Response({'message': 'Information request sent.'})


class ConfirmCalculationView(APIView):
    """Consultant confirms calculation and notifies client."""
    permission_classes = [IsConsultant]

    def post(self, request, pk):
        client_ids = ClientProfile.objects.filter(
            assigned_consultant=request.user
        ).values_list('user_id', flat=True)

        try:
            submission = TaxSubmission.objects.get(id=pk, client_id__in=client_ids)
        except TaxSubmission.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Calculate tax
        result = calculate_full_tax(submission)

        # Update submission with calculated values
        submission.total_assessable_income = result['total_assessable_income']
        submission.total_qualifying_payments = result['total_qualifying_payments']
        submission.personal_relief = result['personal_relief']
        submission.rent_relief = result['rent_relief']
        submission.net_taxable_income = result['net_taxable_income']
        submission.gross_tax = result['gross_tax']
        submission.total_tax_credits = result['total_tax_credits']
        submission.net_tax_payable = result['net_tax_payable']
        submission.status = 'awaiting_confirmation'
        submission.reviewed_by = request.user
        submission.reviewed_at = timezone.now()
        submission.save()

        # Update client profile
        profile = getattr(submission.client, 'client_profile', None)
        if profile:
            profile.status = 'awaiting_confirmation'
            profile.save(update_fields=['status'])

        # Notify client
        Notification.objects.create(
            recipient=submission.client,
            title='Tax Calculation Ready for Review',
            message=f'Your tax calculation for {submission.tax_year.label} is ready. Net Tax Payable: Rs. {result["net_tax_payable"]:,.2f}. Please review and confirm.',
            notification_type='action_required',
            related_submission_id=submission.id,
        )

        return Response({
            'message': 'Calculation confirmed. Client notified.',
            'calculation': result,
        })


class ClientConfirmView(APIView):
    """Client confirms the final tax calculation."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            submission = TaxSubmission.objects.get(id=pk, client=request.user, status='awaiting_confirmation')
        except TaxSubmission.DoesNotExist:
            return Response({'error': 'Not found or not in awaiting confirmation status.'}, status=status.HTTP_404_NOT_FOUND)

        submission.status = 'confirmed'
        submission.confirmed_at = timezone.now()
        submission.save()

        # Archive documents
        _archive_submission(submission)

        # Update client profile
        profile = getattr(request.user, 'client_profile', None)
        if profile:
            profile.status = 'archived'
            profile.save(update_fields=['status'])

        # Notify consultant
        if profile and profile.assigned_consultant:
            Notification.objects.create(
                recipient=profile.assigned_consultant,
                title='Client Confirmed Tax Submission',
                message=f'{profile.full_name} has confirmed their tax submission for {submission.tax_year.label}. Documents have been archived.',
                notification_type='info',
                related_submission_id=submission.id,
            )

        return Response({'message': 'Tax submission confirmed and archived successfully.'})


def _archive_submission(submission):
    """Archive documents following the required folder structure."""
    profile = getattr(submission.client, 'client_profile', None)
    client_name = profile.full_name if profile else submission.client.email
    year_label = submission.tax_year.label.replace('/', '-')

    archive_path = os.path.join(
        str(settings.ARCHIVE_ROOT),
        _sanitize_folder_name(client_name),
        year_label,
        'Final TAX Submission',
    )
    os.makedirs(archive_path, exist_ok=True)

    # Copy all documents
    for doc in submission.documents.all():
        if doc.file and os.path.exists(doc.file.path):
            dest = os.path.join(archive_path, os.path.basename(doc.file.name))
            shutil.copy2(doc.file.path, dest)

    # Generate and save PDF
    pdf_buffer = generate_tax_submission_pdf(submission)
    pdf_path = os.path.join(archive_path, f'Tax_Return_{year_label}.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf_buffer.read())

    submission.status = 'archived'
    submission.archived_at = timezone.now()
    submission.save(update_fields=['status', 'archived_at'])


def _sanitize_folder_name(name):
    """Remove characters not suitable for folder names."""
    import re
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


class GeneratePDFView(APIView):
    """Generate and download the tax submission PDF."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            if request.user.role == 'consultant':
                client_ids = ClientProfile.objects.filter(
                    assigned_consultant=request.user
                ).values_list('user_id', flat=True)
                submission = TaxSubmission.objects.get(id=pk, client_id__in=client_ids)
            else:
                submission = TaxSubmission.objects.get(id=pk, client=request.user)
        except TaxSubmission.DoesNotExist:
            raise Http404

        pdf_buffer = generate_tax_submission_pdf(submission)
        filename = f"Tax_Return_{submission.tax_year.label.replace('/', '-')}_{submission.client.email}.pdf"

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf',
        )


# ── Section-specific CRUD views ───────────────────────────────────────────────

class SectionUpdateView(APIView):
    """Generic view for updating specific form sections (client + consultant)."""
    permission_classes = [IsAuthenticated]
    model_class = None
    serializer_class = None
    section_name = ''

    def get_or_create_section(self, submission):
        obj, _ = self.model_class.objects.get_or_create(submission=submission)
        return obj

    def get(self, request, submission_id):
        submission = _get_submission_for_user(submission_id, request.user)
        if not submission:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            obj = self.model_class.objects.get(submission=submission)
            return Response(self.serializer_class(obj).data)
        except self.model_class.DoesNotExist:
            return Response({})

    def post(self, request, submission_id):
        submission = _get_submission_for_user(submission_id, request.user)
        if not submission:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if submission.status == 'archived':
            return Response({'error': 'Cannot edit archived submission.'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.role != 'consultant' and submission.status not in ['draft', 'info_requested']:
            return Response({'error': 'Cannot edit in current status.'}, status=status.HTTP_400_BAD_REQUEST)

        obj = self.get_or_create_section(submission)
        old_data = dict(self.serializer_class(obj).data) if obj.pk else {}
        serializer = self.serializer_class(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if request.user.role == 'consultant':
                _log_edit(
                    submission, request.user,
                    section=self.section_name or self.model_class.__name__,
                    action='update',
                    old_data=old_data,
                    new_data=dict(serializer.data),
                )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocalEmploymentView(SectionUpdateView):
    model_class = LocalEmploymentIncome
    serializer_class = LocalEmploymentIncomeSerializer
    section_name = 'Local Employment Income'


class ForeignIncomeView(SectionUpdateView):
    model_class = ForeignIncome
    serializer_class = ForeignIncomeSerializer
    section_name = 'Foreign Income'


class TerminalBenefitView(SectionUpdateView):
    model_class = TerminalBenefit
    serializer_class = TerminalBenefitSerializer
    section_name = 'Terminal Benefit'


class RentIncomeView(SectionUpdateView):
    model_class = RentIncome
    serializer_class = RentIncomeSerializer
    section_name = 'Rent Income'


class InterestIncomeView(SectionUpdateView):
    model_class = InterestIncome
    serializer_class = InterestIncomeSerializer
    section_name = 'Interest Income'


class DividendIncomeView(SectionUpdateView):
    model_class = DividendIncome
    serializer_class = DividendIncomeSerializer
    section_name = 'Dividend Income'


class SoleProprietorshipView(SectionUpdateView):
    model_class = SoleProprietorshipIncome
    serializer_class = SoleProprietorshipIncomeSerializer
    section_name = 'Sole Proprietorship'


class OtherIncomeView(SectionUpdateView):
    model_class = OtherIncome
    serializer_class = OtherIncomeSerializer
    section_name = 'Other Income'


class QualifyingPaymentsView(SectionUpdateView):
    model_class = QualifyingPayments
    serializer_class = QualifyingPaymentsSerializer
    section_name = 'Qualifying Payments'


class TaxCreditsView(SectionUpdateView):
    model_class = TaxCredits
    serializer_class = TaxCreditsSerializer
    section_name = 'Tax Credits'


class CashInHandView(SectionUpdateView):
    model_class = CashInHand
    serializer_class = CashInHandSerializer
    section_name = 'Cash in Hand'


class GoldJewelleryView(SectionUpdateView):
    model_class = GoldSilverJewellery
    serializer_class = GoldSilverJewellerySerializer
    section_name = 'Gold & Jewellery'


class DeclarantDetailsView(SectionUpdateView):
    model_class = DeclarantDetails
    serializer_class = DeclarantDetailsSerializer
    section_name = 'Declarant Details'


# ── List/Create/Delete for multi-row sections ─────────────────────────────────

class MultiRowSectionView(APIView):
    permission_classes = [IsAuthenticated]
    model_class = None
    serializer_class = None
    section_name = ''

    def get(self, request, submission_id):
        submission = _get_submission_for_user(submission_id, request.user)
        if not submission:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        objects = self.model_class.objects.filter(submission=submission)
        return Response(self.serializer_class(objects, many=True).data)

    def post(self, request, submission_id):
        submission = _get_submission_for_user(submission_id, request.user)
        if not submission:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if submission.status == 'archived':
            return Response({'error': 'Cannot edit archived submission.'}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.role != 'consultant' and submission.status not in ['draft', 'info_requested']:
            return Response({'error': 'Cannot edit in current status.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            obj = serializer.save(submission=submission)
            if request.user.role == 'consultant':
                _log_edit(
                    submission, request.user,
                    section=self.section_name or self.model_class.__name__,
                    action='add',
                    new_data=dict(serializer.data),
                    description=f'Added row to {self.section_name or self.model_class.__name__}',
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MultiRowItemView(APIView):
    permission_classes = [IsAuthenticated]
    model_class = None
    serializer_class = None
    section_name = ''

    def get_object(self, pk, user):
        try:
            obj = self.model_class.objects.select_related('submission').get(id=pk)
            # Clients can only access their own; consultants can access assigned clients
            if user.role == 'consultant':
                allowed = _get_submission_for_user(obj.submission_id, user)
                if not allowed:
                    return None
            elif obj.submission.client != user:
                return None
            return obj
        except self.model_class.DoesNotExist:
            return None

    def patch(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if obj.submission.status == 'archived':
            return Response({'error': 'Cannot edit archived submission.'}, status=status.HTTP_400_BAD_REQUEST)
        old_data = dict(self.serializer_class(obj).data)
        serializer = self.serializer_class(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if request.user.role == 'consultant':
                _log_edit(
                    obj.submission, request.user,
                    section=self.section_name or self.model_class.__name__,
                    action='update',
                    old_data=old_data,
                    new_data=dict(serializer.data),
                )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if obj.submission.status == 'archived':
            return Response({'error': 'Cannot delete from archived submission.'}, status=status.HTTP_400_BAD_REQUEST)
        old_data = dict(self.serializer_class(obj).data)
        if request.user.role == 'consultant':
            _log_edit(
                obj.submission, request.user,
                section=self.section_name or self.model_class.__name__,
                action='delete',
                old_data=old_data,
                description=f'Deleted row from {self.section_name or self.model_class.__name__}',
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Immovable Properties
class ImmovablePropertyListView(MultiRowSectionView):
    model_class = ImmovableProperty
    serializer_class = ImmovablePropertySerializer
    section_name = 'Immovable Property'


class ImmovablePropertyItemView(MultiRowItemView):
    model_class = ImmovableProperty
    serializer_class = ImmovablePropertySerializer
    section_name = 'Immovable Property'


# Motor Vehicles
class MotorVehicleListView(MultiRowSectionView):
    model_class = MotorVehicle
    serializer_class = MotorVehicleSerializer
    section_name = 'Motor Vehicles'


class MotorVehicleItemView(MultiRowItemView):
    model_class = MotorVehicle
    serializer_class = MotorVehicleSerializer
    section_name = 'Motor Vehicles'


# Bank Balances
class BankBalanceListView(MultiRowSectionView):
    model_class = BankBalance
    serializer_class = BankBalanceSerializer
    section_name = 'Bank Balances'


class BankBalanceItemView(MultiRowItemView):
    model_class = BankBalance
    serializer_class = BankBalanceSerializer
    section_name = 'Bank Balances'


# Shares
class SharesListView(MultiRowSectionView):
    model_class = SharesStocks
    serializer_class = SharesStocksSerializer
    section_name = 'Shares & Stocks'


class SharesItemView(MultiRowItemView):
    model_class = SharesStocks
    serializer_class = SharesStocksSerializer
    section_name = 'Shares & Stocks'


# Loans Given
class LoansGivenListView(MultiRowSectionView):
    model_class = LoansGiven
    serializer_class = LoansGivenSerializer
    section_name = 'Loans Given'


class LoansGivenItemView(MultiRowItemView):
    model_class = LoansGiven
    serializer_class = LoansGivenSerializer
    section_name = 'Loans Given'


# Business Properties
class BusinessPropertyListView(MultiRowSectionView):
    model_class = BusinessProperty
    serializer_class = BusinessPropertySerializer
    section_name = 'Business Property'


class BusinessPropertyItemView(MultiRowItemView):
    model_class = BusinessProperty
    serializer_class = BusinessPropertySerializer
    section_name = 'Business Property'


# Other Assets
class OtherAssetListView(MultiRowSectionView):
    model_class = OtherAsset
    serializer_class = OtherAssetSerializer
    section_name = 'Other Assets'


class OtherAssetItemView(MultiRowItemView):
    model_class = OtherAsset
    serializer_class = OtherAssetSerializer
    section_name = 'Other Assets'


# Disposals
class DisposalListView(MultiRowSectionView):
    model_class = DisposalOfAsset
    serializer_class = DisposalOfAssetSerializer
    section_name = 'Disposal of Assets'


class DisposalItemView(MultiRowItemView):
    model_class = DisposalOfAsset
    serializer_class = DisposalOfAssetSerializer
    section_name = 'Disposal of Assets'


# Liabilities
class LiabilityListView(MultiRowSectionView):
    model_class = Liability
    serializer_class = LiabilitySerializer
    section_name = 'Liabilities'


class LiabilityItemView(MultiRowItemView):
    model_class = Liability
    serializer_class = LiabilitySerializer
    section_name = 'Liabilities'


# Self Assessment Payments
class SelfAssessmentListView(MultiRowSectionView):
    model_class = SelfAssessmentPayment
    serializer_class = SelfAssessmentPaymentSerializer
    section_name = 'Self-Assessment Payments'


class SelfAssessmentItemView(MultiRowItemView):
    model_class = SelfAssessmentPayment
    serializer_class = SelfAssessmentPaymentSerializer
    section_name = 'Self-Assessment Payments'


# Consultant update tax calculation view
class ConsultantUpdateCalculationView(APIView):
    permission_classes = [IsConsultant]

    def patch(self, request, pk):
        submission = _get_submission_for_user(pk, request.user)
        if not submission:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        allowed = [
            'total_assessable_income', 'total_qualifying_payments', 'personal_relief',
            'rent_relief', 'net_taxable_income', 'gross_tax', 'total_tax_credits', 'net_tax_payable',
        ]
        changed = {f: request.data[f] for f in allowed if f in request.data}
        old_data = {f: str(getattr(submission, f, '')) for f in changed}
        for field, value in changed.items():
            setattr(submission, field, value)
        submission.save()

        if changed:
            _log_edit(
                submission, request.user,
                section='Tax Computation',
                action='update',
                old_data=old_data,
                new_data={f: str(request.data[f]) for f in changed},
                description=f'Updated tax computation fields: {", ".join(changed.keys())}',
            )
        return Response(TaxSubmissionSerializer(submission).data)


# ── Archive tree view ──────────────────────────────────────────────────────────

class ArchiveTreeView(APIView):
    """Returns archived submissions grouped by client → year for the consultant."""
    permission_classes = [IsConsultant]

    def get(self, request):
        from apps.documents.models import Document
        client_ids = ClientProfile.objects.filter(
            assigned_consultant=request.user
        ).values_list('user_id', flat=True)

        archived = TaxSubmission.objects.filter(
            client_id__in=client_ids,
            status='archived',
        ).select_related('client', 'client__client_profile', 'tax_year').order_by(
            'client__client_profile__full_name', '-tax_year__year'
        )

        tree = {}
        for sub in archived:
            profile = getattr(sub.client, 'client_profile', None)
            client_name = profile.full_name if profile else sub.client.email
            client_email = sub.client.email
            client_profile_id = profile.id if profile else None

            if client_name not in tree:
                tree[client_name] = {
                    'client_name': client_name,
                    'client_email': client_email,
                    'client_profile_id': client_profile_id,
                    'years': [],
                }

            docs = Document.objects.filter(submission=sub).order_by('section', 'uploaded_at')
            tree[client_name]['years'].append({
                'submission_id': sub.id,
                'tax_year_label': sub.tax_year.label,
                'archived_at': sub.archived_at,
                'submitted_at': sub.submitted_at,
                'net_tax_payable': str(sub.net_tax_payable),
                'total_assessable_income': str(sub.total_assessable_income),
                'net_taxable_income': str(sub.net_taxable_income),
                'documents': [
                    {
                        'id': doc.id,
                        'original_filename': doc.original_filename,
                        'file_url': request.build_absolute_uri(doc.file.url) if doc.file else None,
                        'document_type_display': doc.get_document_type_display(),
                        'section': doc.section,
                        'is_verified': doc.is_verified,
                        'file_size_kb': doc.file_size_kb,
                    }
                    for doc in docs
                ],
            })

        return Response(list(tree.values()))


# ── Edit log view ──────────────────────────────────────────────────────────────

class SubmissionEditLogsView(APIView):
    """Returns the edit audit log for a submission."""
    permission_classes = [IsConsultant]

    def get(self, request, pk):
        submission = _get_submission_for_user(pk, request.user)
        if not submission:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        logs = submission.edit_logs.select_related('edited_by').all()
        return Response(SubmissionEditLogSerializer(logs, many=True).data)

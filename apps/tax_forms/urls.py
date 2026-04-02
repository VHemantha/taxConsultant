from django.urls import path
from .views import (
    TaxYearListView, TaxSubmissionListCreateView, TaxSubmissionDetailView,
    SubmitTaxFormView, RequestInfoView, ConfirmCalculationView,
    ClientConfirmView, GeneratePDFView, ConsultantUpdateCalculationView,
    ArchiveTreeView, SubmissionEditLogsView,
    # Income sections
    LocalEmploymentView, ForeignIncomeView, TerminalBenefitView,
    RentIncomeView, InterestIncomeView, DividendIncomeView,
    SoleProprietorshipView, OtherIncomeView,
    # Qualifying / Credits
    QualifyingPaymentsView, TaxCreditsView,
    SelfAssessmentListView, SelfAssessmentItemView,
    # Assets
    ImmovablePropertyListView, ImmovablePropertyItemView,
    MotorVehicleListView, MotorVehicleItemView,
    BankBalanceListView, BankBalanceItemView,
    SharesListView, SharesItemView,
    CashInHandView, LoansGivenListView, LoansGivenItemView,
    GoldJewelleryView,
    BusinessPropertyListView, BusinessPropertyItemView,
    OtherAssetListView, OtherAssetItemView,
    DisposalListView, DisposalItemView,
    # Liabilities
    LiabilityListView, LiabilityItemView,
    # Declarant
    DeclarantDetailsView,
)

urlpatterns = [
    path('years/', TaxYearListView.as_view(), name='tax_years'),
    path('submissions/', TaxSubmissionListCreateView.as_view(), name='submissions_list'),
    path('submissions/<int:pk>/', TaxSubmissionDetailView.as_view(), name='submission_detail'),
    path('submissions/<int:pk>/submit/', SubmitTaxFormView.as_view(), name='submit_form'),
    path('submissions/<int:pk>/request-info/', RequestInfoView.as_view(), name='request_info'),
    path('submissions/<int:pk>/confirm-calculation/', ConfirmCalculationView.as_view(), name='confirm_calculation'),
    path('submissions/<int:pk>/client-confirm/', ClientConfirmView.as_view(), name='client_confirm'),
    path('submissions/<int:pk>/pdf/', GeneratePDFView.as_view(), name='generate_pdf'),
    path('submissions/<int:pk>/update-calculation/', ConsultantUpdateCalculationView.as_view(), name='update_calculation'),

    # Income sections
    path('submissions/<int:submission_id>/income/local-employment/', LocalEmploymentView.as_view()),
    path('submissions/<int:submission_id>/income/foreign/', ForeignIncomeView.as_view()),
    path('submissions/<int:submission_id>/income/terminal-benefit/', TerminalBenefitView.as_view()),
    path('submissions/<int:submission_id>/income/rent/', RentIncomeView.as_view()),
    path('submissions/<int:submission_id>/income/interest/', InterestIncomeView.as_view()),
    path('submissions/<int:submission_id>/income/dividend/', DividendIncomeView.as_view()),
    path('submissions/<int:submission_id>/income/sole-proprietorship/', SoleProprietorshipView.as_view()),
    path('submissions/<int:submission_id>/income/other/', OtherIncomeView.as_view()),

    # Qualifying payments & tax credits
    path('submissions/<int:submission_id>/qualifying-payments/', QualifyingPaymentsView.as_view()),
    path('submissions/<int:submission_id>/tax-credits/', TaxCreditsView.as_view()),
    path('submissions/<int:submission_id>/self-assessment/', SelfAssessmentListView.as_view()),
    path('self-assessment/<int:pk>/', SelfAssessmentItemView.as_view()),

    # Assets
    path('submissions/<int:submission_id>/assets/immovable/', ImmovablePropertyListView.as_view()),
    path('assets/immovable/<int:pk>/', ImmovablePropertyItemView.as_view()),
    path('submissions/<int:submission_id>/assets/vehicles/', MotorVehicleListView.as_view()),
    path('assets/vehicles/<int:pk>/', MotorVehicleItemView.as_view()),
    path('submissions/<int:submission_id>/assets/bank-balances/', BankBalanceListView.as_view()),
    path('assets/bank-balances/<int:pk>/', BankBalanceItemView.as_view()),
    path('submissions/<int:submission_id>/assets/shares/', SharesListView.as_view()),
    path('assets/shares/<int:pk>/', SharesItemView.as_view()),
    path('submissions/<int:submission_id>/assets/cash/', CashInHandView.as_view()),
    path('submissions/<int:submission_id>/assets/loans-given/', LoansGivenListView.as_view()),
    path('assets/loans-given/<int:pk>/', LoansGivenItemView.as_view()),
    path('submissions/<int:submission_id>/assets/gold/', GoldJewelleryView.as_view()),
    path('submissions/<int:submission_id>/assets/business/', BusinessPropertyListView.as_view()),
    path('assets/business/<int:pk>/', BusinessPropertyItemView.as_view()),
    path('submissions/<int:submission_id>/assets/other/', OtherAssetListView.as_view()),
    path('assets/other/<int:pk>/', OtherAssetItemView.as_view()),
    path('submissions/<int:submission_id>/assets/disposals/', DisposalListView.as_view()),
    path('assets/disposals/<int:pk>/', DisposalItemView.as_view()),

    # Liabilities
    path('submissions/<int:submission_id>/liabilities/', LiabilityListView.as_view()),
    path('liabilities/<int:pk>/', LiabilityItemView.as_view()),

    # Declarant
    path('submissions/<int:submission_id>/declarant/', DeclarantDetailsView.as_view()),

    # Consultant-only
    path('archive/', ArchiveTreeView.as_view(), name='archive_tree'),
    path('submissions/<int:pk>/edit-logs/', SubmissionEditLogsView.as_view(), name='edit_logs'),
]

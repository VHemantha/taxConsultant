from django.urls import path
from .views import DocumentListView, DocumentDetailView, VerifyDocumentView

urlpatterns = [
    path('submission/<int:submission_id>/', DocumentListView.as_view(), name='document_list'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document_detail'),
    path('<int:pk>/verify/', VerifyDocumentView.as_view(), name='verify_document'),
]

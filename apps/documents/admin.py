from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'document_type', 'section', 'uploaded_by', 'uploaded_at', 'is_verified']
    list_filter = ['document_type', 'section', 'is_verified']
    search_fields = ['original_filename', 'description']

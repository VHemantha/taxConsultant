from rest_framework import serializers
from django.conf import settings
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    section_display = serializers.CharField(source='get_section_display', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'submission', 'document_type', 'document_type_display',
            'section', 'section_display', 'file', 'file_url', 'original_filename',
            'file_size', 'file_size_kb', 'description', 'uploaded_at',
            'is_verified', 'uploaded_by',
        ]
        read_only_fields = ['id', 'uploaded_at', 'original_filename', 'file_size', 'uploaded_by']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    document_type = serializers.ChoiceField(choices=Document.DOCUMENT_TYPE_CHOICES)
    section = serializers.ChoiceField(choices=Document.SECTION_CHOICES, default='general')
    description = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def validate_file(self, value):
        max_size = settings.MAX_UPLOAD_SIZE
        if value.size > max_size:
            raise serializers.ValidationError(f"File size cannot exceed {max_size // (1024 * 1024)}MB.")

        allowed_types = settings.ALLOWED_DOCUMENT_TYPES
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Only PDF, JPEG, and PNG files are allowed."
            )
        return value

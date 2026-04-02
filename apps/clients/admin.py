from django.contrib import admin
from .models import ClientProfile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'tin', 'status', 'assigned_consultant', 'created_at']
    list_filter = ['status']
    search_fields = ['full_name', 'tin', 'user__email']
    ordering = ['-created_at']

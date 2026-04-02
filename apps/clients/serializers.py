from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import ClientProfile

User = get_user_model()


class ClientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    consultant_name = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            'id', 'user_id', 'email', 'username', 'full_name', 'tin', 'pin', 'nic_passport',
            'telephone', 'mobile', 'address', 'status', 'notes',
            'assigned_consultant', 'consultant_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_consultant_name(self, obj):
        if obj.assigned_consultant:
            return obj.assigned_consultant.get_full_name() or obj.assigned_consultant.email
        return None


class RegisterClientSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    tin = serializers.CharField(max_length=50, required=False, allow_blank=True)
    pin = serializers.CharField(max_length=50, required=False, allow_blank=True)
    nic_passport = serializers.CharField(max_length=50, required=False, allow_blank=True)
    telephone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    mobile = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        consultant = self.context['request'].user

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            role='client',
            must_change_password=True,
        )

        profile = ClientProfile.objects.create(
            user=user,
            assigned_consultant=consultant,
            full_name=f"{validated_data['first_name']} {validated_data['last_name']}",
            tin=validated_data.get('tin', ''),
            pin=validated_data.get('pin', ''),
            nic_passport=validated_data.get('nic_passport', ''),
            telephone=validated_data.get('telephone', ''),
            mobile=validated_data.get('mobile', ''),
            address=validated_data.get('address', ''),
        )

        return user, profile


class ClientListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    current_submission_status = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = ['id', 'email', 'full_name', 'tin', 'status', 'current_submission_status', 'created_at']

    def get_current_submission_status(self, obj):
        latest = obj.user.tax_submissions.order_by('-created_at').first()
        if latest:
            return latest.status
        return None

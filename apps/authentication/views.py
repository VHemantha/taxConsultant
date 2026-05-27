from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class LoginView(APIView):
    """
    Accepts either email or username in the 'email' field.
    When multiple client accounts share the same email, the client must log in
    with their unique username instead.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        credential = (request.data.get('email') or '').strip()
        password   = request.data.get('password', '')

        if not credential or not password:
            return Response(
                {'detail': 'Email/username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if '@' in credential:
            users = User.objects.filter(email__iexact=credential, is_active=True)
            count = users.count()
            if count > 1:
                return Response(
                    {
                        'detail': (
                            'Multiple accounts share this email address. '
                            'Please log in using your username instead.'
                        ),
                        'use_username': True,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif count == 0:
                return Response(
                    {'detail': 'No active account found with this email.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            user_obj = users.first()
        else:
            try:
                user_obj = User.objects.get(username=credential, is_active=True)
            except User.DoesNotExist:
                return Response(
                    {'detail': 'No active account found with this username.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        if not user_obj.check_password(password):
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = CustomTokenObtainPairSerializer.get_token(user_obj)

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        user_obj.last_login_ip = ip
        user_obj.save(update_fields=['last_login_ip'])

        return Response({
            'access':               str(refresh.access_token),
            'refresh':              str(refresh),
            'role':                 user_obj.role,
            'email':                user_obj.email,
            'full_name':            user_obj.get_full_name(),
            'user_id':              user_obj.id,
            'must_change_password': user_obj.must_change_password,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.must_change_password = False
            request.user.save()
            return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

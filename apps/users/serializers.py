"""
===========================================
Users App — Serializers
===========================================
DRF serializers for authentication, user management,
and custom JWT token claims.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser, Role, ActivityLog


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes role and permissions
    in the token claims. This allows the frontend to know the user's
    role without making an additional API call.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to the JWT payload
        token['email'] = user.email
        token['full_name'] = user.get_full_name()
        token['role'] = user.role.name if user.role else None

        return token

    def validate(self, attrs):
        """Override to use email field for authentication."""
        data = super().validate(attrs)

        # Include extra user info in the response body (not the token)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'full_name': self.user.get_full_name(),
            'role': self.user.role.name if self.user.role else None,
        }
        return data


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model."""

    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """
    Full user serializer for admin user management.
    Includes role details and handles password hashing.
    """

    role_name = serializers.CharField(source='role.get_name_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'department', 'role', 'role_name',
            'is_active', 'is_locked', 'date_joined', 'last_login',
        ]
        read_only_fields = ['date_joined', 'last_login']

    def create(self, validated_data):
        """Create a new user with hashed password."""
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)  # Hash the password
            user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for users viewing/updating their own profile."""

    role_name = serializers.CharField(source='role.get_name_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone', 'department', 'role_name', 'date_joined',
        ]
        read_only_fields = ['email', 'role_name', 'date_joined']


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for the audit trail / activity log."""

    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_email', 'action', 'model_name',
            'object_id', 'description', 'changes', 'ip_address',
            'user_agent', 'request_path', 'request_method', 'timestamp',
        ]
        read_only_fields = ['__all__']

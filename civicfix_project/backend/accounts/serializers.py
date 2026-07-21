from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from departments.models import Department

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "phone",
            "role", "department", "department_name", "created_at",
        ]
        read_only_fields = ["id", "role", "created_at"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Public self-registration for BOTH citizens and department staff.
    The signer picks their role; if they pick "department" they must also
    pick which department they belong to (from the departments already
    set up by an admin). Admin accounts are never self-registered.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=[User.Role.CITIZEN, User.Role.DEPARTMENT])
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True), required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "phone", "role", "department"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs.get("role") == User.Role.DEPARTMENT and not attrs.get("department"):
            raise serializers.ValidationError({"department": "Please select which department you belong to."})
        if attrs.get("role") == User.Role.CITIZEN:
            attrs["department"] = None
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """Login with email + password; embeds the user profile in the token response."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class CreateStaffSerializer(serializers.ModelSerializer):
    """Admin-only: create a Department-staff or Admin account directly."""

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "phone", "role", "department"]

    def validate(self, attrs):
        role = attrs.get("role")
        department = attrs.get("department")
        if role == User.Role.DEPARTMENT and not department:
            raise serializers.ValidationError({"department": "Department is required for department staff."})
        if role == User.Role.CITIZEN:
            raise serializers.ValidationError({"role": "Use the public register endpoint for citizens."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])

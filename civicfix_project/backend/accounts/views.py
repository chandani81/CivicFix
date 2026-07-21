from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import IsAdmin
from .serializers import (
    ChangePasswordSerializer,
    CreateStaffSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/ - self sign-up for citizens OR department staff
    (role + department chosen on the form). No email verification step --
    the account is active immediately and this endpoint logs them straight
    in, returning the same {access, refresh, user} shape as /login/.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/  {email, password} -> access, refresh, user"""

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/"""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"old_password": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"message": "Password updated successfully."})


class StaffListCreateView(generics.ListCreateAPIView):
    """
    Admin-only.
    GET  /api/auth/staff/   -> list department staff & admins
    POST /api/auth/staff/   -> create a department-staff or admin account directly
    """

    permission_classes = [IsAdmin]
    queryset = User.objects.exclude(role=User.Role.CITIZEN).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateStaffSerializer
        return UserSerializer


class StaffDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin-only: manage (update/delete) a staff account."""

    permission_classes = [IsAdmin]
    queryset = User.objects.exclude(role=User.Role.CITIZEN)
    serializer_class = UserSerializer


class CitizenListView(generics.ListAPIView):
    """Admin-only: view all citizen accounts."""

    permission_classes = [IsAdmin]
    serializer_class = UserSerializer
    queryset = User.objects.filter(role=User.Role.CITIZEN).order_by("-created_at")

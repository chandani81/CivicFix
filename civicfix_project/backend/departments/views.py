from rest_framework import generics, permissions

from accounts.permissions import IsAdmin

from .models import Department
from .serializers import DepartmentSerializer


class DepartmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/departments/       -> public (the signup form needs this to let a
                                     "department" role pick which department they belong to,
                                     before they're logged in)
    POST /api/departments/       -> admin only
    """

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [permissions.AllowAny()]


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin-only update/delete; authenticated read."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

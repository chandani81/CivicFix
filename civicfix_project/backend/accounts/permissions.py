from rest_framework.permissions import BasePermission


class IsCitizen(BasePermission):
    message = "Only citizens can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_citizen)


class IsDepartmentStaff(BasePermission):
    message = "Only department staff can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_department_staff)


class IsAdmin(BasePermission):
    message = "Only admins can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin_role)


class IsAdminOrDepartment(BasePermission):
    message = "Only admins or department staff can perform this action."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_admin_role or u.is_department_staff))

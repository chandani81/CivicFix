from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsComplaintParticipant(BasePermission):
    """
    Object-level: the citizen who filed it, the staff of the assigned
    department, or an admin, can view/act on a complaint.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin_role:
            return True
        if user.is_citizen:
            return obj.citizen_id == user.id
        if user.is_department_staff:
            return obj.department_id == user.department_id
        return False


class CanUpdateStatus(BasePermission):
    """Only department staff (of the assigned department) or admin can change status/post updates."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_admin_role or user.is_department_staff))

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin_role:
            return True
        return user.is_department_staff and obj.department_id == user.department_id

"""Permission classes ask the user's helper properties, never role strings."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsInternalStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_internal_staff)


class IsLeadership(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_leadership)


class IsFinance(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.can_record_payments)


class StaffReadFinanceWrite(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated and u.is_internal_staff):
            return False
        return request.method in SAFE_METHODS or u.can_record_payments


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_teacher)


class IsParent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_parent)

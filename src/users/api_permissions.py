from rest_framework import permissions


class IsAdminOrOwnsAccount(permissions.BasePermission):
    """
    Custom permission to only allow admin users or the owner of the account
    to view and edit their own account.
    """

    def has_object_permission(self, request, view, obj):
        # Allow access to admin users or the user themselves
        return request.user.is_staff or obj == request.user

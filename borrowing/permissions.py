from rest_framework.permissions import BasePermission


class IsAdminOrIfAuthenticatedReadOrCreateOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_staff or (
                request.user
                and request.user.is_authenticated
                and request.method in ("GET", "POST")
            )
        )

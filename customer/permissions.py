from rest_framework.permissions import BasePermission


class SuperUserPermission(BasePermission):
    """
    Use Django's permission framework for permission of super users.
    """
    message = 'Adding customers not allowed.'

    def has_permission(self, request, view):
        """
        Returns True if the request is from superuser.
        Otherwise returns `False`.
        """

        # Get the underlying HttpRequest object
        request = request._request
        user = getattr(request, 'user', None)

        return user.is_superuser
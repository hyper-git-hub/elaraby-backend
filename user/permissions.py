from rest_framework.permissions import BasePermission
from hypernet.utils import get_user_from_request
from user.enums import RoleTypeEnum
from hypernet.utils import exception_handler, generic_response
from hypernet.constants import *

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        safe_method = ['POST', 'PATCH', 'PUT', 'GET']
        if request.method in safe_method:
            user = get_user_from_request(request,None)
            if user.role.id != RoleTypeEnum.ADMIN:
                return False
            return True
        return False

class IsManager(BasePermission):

    def has_permission(self, request, view):
        user = get_user_from_request(request, None)
        if user.role.id != RoleTypeEnum.MANAGER:
            return False
        return True
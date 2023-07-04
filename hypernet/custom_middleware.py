from django.utils.deprecation import MiddlewareMixin
from .utils import get_customer_from_request, get_module_from_request, get_user_from_request


class TemperRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Rewrites the proxy headers so that only the most
        recent proxy is used.
        """
        try:
            if request.user.is_authenticated():
                request.POST._mutable = True
                request.POST['modified_by'] = get_user_from_request(request, None)
                request.POST['customer'] = get_customer_from_request(request, None)
                request.POST['module'] = get_module_from_request(request, None)
                request.POST._mutable = False
        except Exception as e:
            return str(e)





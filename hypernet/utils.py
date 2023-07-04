# **************** Other Util Methods ****************
import gc
import json
from django.http import HttpResponse
import logging
from hypernet.constants import ERROR_PARAMS_MISSING_BODY, RESPONSE_MESSAGE, RESPONSE_STATUS
from user.enums import RoleTypeEnum

logger = logging.getLogger('hypernet')


def get_param(request, key, default):
    key = request.query_params.get(key, default)
    return key or default


def get_request_param(request, key, default):
    key = json.loads(request.GET['data'])[key]
    return key or default


def get_data_param(request, key, default):
    if hasattr(request, 'data'):
        key = request.data.get(key, default)
        return key or default
    else:
        return default


def get_customer_from_request(request, default):
    customer = request.user.customer.id
    return customer or default


def get_module_from_request(request, default):
    m_id = request.user.preferred_module
    return m_id or default


def get_user_from_request(request, default):
    user = request.user
    return user or default


def get_default_param(request, key, default):
    key = request.query_params.get(key, request.data.get(key, default))
    return key or default


def get_list_param(request, key, default):
    key = request.GET.getlist(key)
    return key or default


def error_message_serializers(serializer_errors):
    return serializer_errors[next(iter(serializer_errors))][0]


def response_json(status, data, message=None):
    if message:
        data = {
        "status": status,
        "message": message,
        }
    else:
        data = {
            "response": data,
            "status": status,
        }
    return data


def response_post(success, data, message=None):
    data = {
        "data": data,
        "success": success,
        "message": message,
    }
    return data


def queryset_iterator(queryset, chunksize=1000):
    '''''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    '''
    pk = 0
    last_pk = queryset.order_by('-pk')[0]['pk']
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row['pk']
            yield row
        gc.collect()


def exception_handler(def_value=None):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as err:
                # traceback.print_exc(5)
                logger.error(err, exc_info=True)
                return def_value
        return applicator
    return decorate


def verify_request_params(params):
    def decorator(func):
        def inner(request, *args, **kwargs):
            if not all(param in request.query_params for param in params):
                return generic_response(response_body=ERROR_PARAMS_MISSING_BODY, http_status=200)
            return func(request, *args, **kwargs)
        return inner
    return decorator


def async_util(f):
    from threading import Thread
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def append_post_request_params(function):
    def wrap(request):
        if request.user.is_authenticated():
            request.POST._mutable = True
            request.POST['customer'] = get_customer_from_request(request, None)
            request.POST['modified_by'] = get_user_from_request(request, None)
            request.POST['module'] = get_module_from_request(request, None)
            request.POST._mutable = False
        else:
            return function(request)
    return wrap


def verify_user_privileges(params):
    def decorator(func):
        def inner(request, *args, **kwargs):
            if request.user.role_id not in params:
                response_body = {RESPONSE_MESSAGE: "You dont have enough privileges", RESPONSE_STATUS: 403}
                return generic_response(response_body=response_body, http_status=200)
            return func(request, *args, **kwargs)
        return inner
    return decorator


# Generic failure/success Response
from django.core.serializers.json import DjangoJSONEncoder
def generic_response(response_body, http_status=200, header_dict={}, mime='application/json'):
    msg = json.dumps(response_body, cls=DjangoJSONEncoder)
    resp = HttpResponse(msg, status=http_status, content_type=mime)
    for name, value in header_dict.items():
        resp[name] = value
    return resp

# ------- IOA UTIL FUNCTION FOR ESTRUS ALERT CRITERIA -------------
def estrus_datetime_init():
    """
        Initializes datetime fields keeping in consideration the
        estrus_gap - the time between last off and next onset

        TODO: make it a general datetime.now() with delta utility.
    :return:
    """
    from django.utils import timezone
    from hypernet.constants import IOA_ESTRUS_CRITERIA
    return timezone.now() - timezone.timedelta(seconds=IOA_ESTRUS_CRITERIA.get('estrus_gap'))


# Hypernet data ingestion for different keys

def get_value_from_data(key, data, type, default=None):
    if data.get(key):
        if type == 'float':
            return float(data.get(key))
        elif type == 'string':
            return str(data.get(key))
        elif type == 'int':
            return int(data.get(key))
    else:
        return default
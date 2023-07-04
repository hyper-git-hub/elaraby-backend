from customer.models import Customer
from hypernet.models import DeviceType
from hypernet.serializers import *
#TODO Remove * import of constatns
from hypernet.constants import *
from hypernet.enums import OptionsEnum, DeviceTypeEntityEnum, DeviceTypeAssignmentEnum, IOFOptionsEnum
from hypernet.utils import generic_response, exception_handler, get_default_param
import hypernet.utils as h_utils
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from iof.utils import get_entity
from options.models import Options
from user.models import Module, User
from iof.models import ActivityData

@api_view(['POST'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def add_job(request):
    from hypernet.enums import DeviceTypeEntityEnum

    type_id = int(h_utils.get_data_param(request, 'type', None))
    truck = h_utils.get_data_param(request, 'truck', None)
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_ERROR, RESPONSE_DATA: []}
    http_status = HTTP_ERROR_CODE
    if type_id:
        if (type_id) == DeviceTypeEntityEnum.JOB:
            request.POST._mutable = True
            request.data['job_status'] = IOFOptionsEnum.PENDING
            request.data['status'] = OptionsEnum.ACTIVE
            request.data['customer'] = h_utils.get_customer_from_request(request, None)
            request.data['module'] = h_utils.get_module_from_request(request,None)
            request.data['modified_by'] = 1 #h_utils.get_user_from_request(request, None)
            request.POST._mutable = False
            serializer = JobSerializer(data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            if truck:
                job_assignment = Assignment(
                    name="Job Assigned to" + str(Entity.objects.get(id=truck).name),
                    child=Entity.objects.get(id=serializer.data['id']),
                    parent=Entity.objects.get(id=truck),
                    customer=Customer.objects.get(id=serializer.data['customer']),
                    module=Module.objects.get(id=serializer.data['module']),
                    type=DeviceType.objects.get(id=DeviceTypeAssignmentEnum.JOB_ASSIGNMENT),
                    status=Options.objects.get(id=OptionsEnum.ACTIVE),
                    end_datetime=serializer.data['job_end_datetime'],
                    modified_by=User.objects.get(id=1),
                )
                print(job_assignment)
                job_assignment.save()
            response_body[RESPONSE_DATA] = {TEXT_OPERATION_SUCCESSFUL: True}
            http_status = HTTP_SUCCESS_CODE
            response_body[RESPONSE_STATUS] = STATUS_OK

        else:
            error_list = []
            for errors in serializer.errors:
                error_list.append("invalid  " + errors + "  given.")
            response_body[RESPONSE_MESSAGE] = error_list

    return generic_response(response_body=response_body, http_status=http_status)


@api_view(['PATCH'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=HTTP_ERROR_CODE))
def edit_job(request):
    from hypernet.enums import DeviceTypeEntityEnum
    pk = h_utils.get_data_param(request, 'id', None)
    customer = h_utils.get_customer_from_request(request, None)
    type_id = int(h_utils.get_data_param(request, 'type', None))
    new_truck = h_utils.get_data_param(request, 'new_truck', None)

    request.POST._mutable = True
    request.data['job_status'] = IOFOptionsEnum.PENDING
    request.data['status'] = OptionsEnum.ACTIVE
    request.data['customer'] = h_utils.get_customer_from_request(request, None)
    request.data['module'] = h_utils.get_module_from_request(request, None)
    request.data['modified_by'] = 1  # h_utils.get_user_from_request(request, None)
    request.POST._mutable = False
    print(request.user.customer.id)
    # print(request.data)

    if type_id == DeviceTypeEntityEnum.JOB:
        if Entity.objects.get(pk=pk, customer=customer, status=OptionsEnum.ACTIVE):
            entity_obj = Entity.objects.get(pk=pk, customer=customer, status=OptionsEnum.ACTIVE)
            print(request.user.customer)
            serializer = JobSerializer(entity_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                print(serializer.data)
                if new_truck:
                    job_assignment = Assignment(
                        name="Job Assigned to" + str(entity_obj.name),
                        child=Entity.objects.get(id=pk),
                        parent=Entity.objects.get(id=new_truck),
                        customer=Customer.objects.get(id=serializer.data['customer']),
                        module=Module.objects.get(id=serializer.data['module']),
                        type=DeviceType.objects.get(id=DeviceTypeAssignmentEnum.JOB_ASSIGNMENT),
                        status=Options.objects.get(id=OptionsEnum.ACTIVE),
                        end_datetime=serializer.data['job_end_datetime'],
                        modified_by=User.objects.get(id=serializer.data['modified_by']),
                    )

                    old_assignment = Assignment.objects.filter(parent__type=DeviceTypeEntityEnum.TRUCK,
                                                               child_id=pk, status=OptionsEnum.ACTIVE,
                                                               child__type=DeviceTypeEntityEnum.JOB). \
                        values_list('parent_id', flat=True)
                    print(old_assignment)
                    if old_assignment:
                        Assignment.objects.filter(parent_id__in=old_assignment). \
                            update(status=Options.objects.get(id=OptionsEnum.INACTIVE))
                    job_assignment.save()
                    return generic_response(response_body="New Assignment added", http_status=200)
                else:
                    return generic_response(response_body="New Assignment added Old Assignment didn't exist",
                                            http_status=200)
            else:
                return generic_response(response_body=serializer.errors, http_status=500)
    return generic_response(response_body=TEXT_OPERATION_SUCCESSFUL, http_status=200)
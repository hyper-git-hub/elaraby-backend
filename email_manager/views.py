import datetime as dt
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from hypernet.utils import generic_response, verify_request_params
from ioa.utils import *
import csv


# TEST CALL TO SAVE LIST OF DICT TO CSV
# ---------------------------------------------------------------------------------------------------------------------
@csrf_exempt
@api_view(['GET'])
@permission_classes(permission_classes=[IsAdminUser])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def send_email(self):
    from email_manager.email_util import extended_email_with_title
    response_body = {RESPONSE_MESSAGE: "Data Added to File", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    # animals = util_get_animal_details(customer_id=1, animal_id=None, herd_id=11)
    # for animal in animals:
    #     response_body[RESPONSE_DATA].append(animal.animal_details_to_dict())
    #     columns = ['group', 'type', 'age', 'weight', 'lactation_days'
    #         , 'name', 'last_breeding_performed(date)']
    #     with open('new_csv', 'w', newline='') as CSV_FILE:
    #         csv_writer = csv.DictWriter(CSV_FILE, fieldnames=columns, dialect='excel')
    #         csv_writer.writeheader()
    #         for data in response_body[RESPONSE_DATA]:
    #             csv_writer.writerow(data)
    # from email_manager.email_util import extended_email_with_title
    # extended_email_with_title(title='junk')
    # send_sms_util()
    # response_body[RESPONSE_DATA] = cron_job_IOA_alerts()
    return generic_response(response_body=response_body, http_status=200)

# -------------------------------------------------------------------------------------------------------------

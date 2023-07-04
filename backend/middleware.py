from django import http
from customer.models import Customer
from django.core.exceptions import ValidationError
import pytz, json
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.shortcuts import render
from hypernet.utils import get_data_param, get_param, response_json, get_request_param
from hypernet.models import Entity, RoleAssignment

class IOFMiddleware(object):
    # Check if client IP is allowed
    def process_request(self, request):
        if not request.user.is_anonymous():
            if request.user.email and request.user.role.id > 2:
                if request.user.role.id == 3:
                    # This logic is to filled when the driver or player logs into the system
                    pass
                else:
                    try:
                        e_id =  get_request_param(request, 'id', None)
                    except:
                        e_id = None
                    destination = request.path
                    role = request.user.role

                    if e_id:
                        try:
                            RoleAssignment.objects.get(entity__id=e_id, role__id=role.id)
                            pass
                        except:
                            return http.HttpResponseRedirect(reverse('not_authorized'))
                    else:
                        # Total assets to b retrieved here somehow or a flag ought to be set
                        entities = RoleAssignment.objects.filter(role=role.id).values('entity')
                        request.entities = entities
                        pass
            else:
                pass

from django.http import JsonResponse
from rest_framework.decorators import  APIView
from ioa.crons.scheduler import testing
from ioa.serializer import ActivityListSerializer
from hypernet.utils import generic_response, get_data_param, get_default_param, exception_handler
from hypernet.constants import *
import datetime as dt
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from ioa.serializer import SchedulingSerializer
from datetime import datetime,timedelta
from ioa.utils import *
from hypernet.constants import COMPLETE
from django.utils import dateparse
import ast
# from ioa.activity.activity_utils import *
import ioa.activity.activity_utils as utils


class ActivityListView(APIView):
    # CALL NO LONGER USED.. CRON JOB POST'S ACTIVITIES FROM SCHEDULING

    # def post(self, request):
    #     serializer = ActivityListSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         data = serializer.data
    #         return generic_response(data, http_status=200)
    #     return JsonResponse(serializer.errors, status=400)

    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        response = {RESPONSE_STATUS: STATUS_OK,
                    RESPONSE_MESSAGE: ""}
        http_status = 200
        response[RESPONSE_DATA] = []
        pk = (get_default_param(request, 'pk', None))
        customer = (get_default_param(request, 'customer', None))
        status = (get_default_param(request, 'status', None))
        activity_type = (get_default_param(request, 'activity_type', None))
        activity_priority = (get_default_param(request, 'priority', None))
        animal = (get_default_param(request, 'animal', None))
        if not customer:
            response[RESPONSE_MESSAGE] = constants.TEXT_PARAMS_MISSING
            response[RESPONSE_STATUS] = STATUS_ERROR
            http_status = 400
        elif pk:
            response[RESPONSE_DATA] = utils.get_activity_by_group(int(customer), int(pk))
        elif status:
            response[RESPONSE_DATA] = utils.get_activities_by_status(int(customer), (status))
        elif activity_type:
            response[RESPONSE_DATA] = utils.get_activities_by_type(int(customer), activity_type)
        elif animal:
            response[RESPONSE_DATA] = utils.get_activities_by_animal(int(customer), int(animal))
        elif activity_priority:
            response[RESPONSE_DATA] = utils.get_activities_by_priority(int(customer), activity_priority)
        else:
            response[RESPONSE_DATA] = utils.util_get_all_activities(int(customer))

        return generic_response(response_body=response, http_status=http_status)

    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def patch(self, request):
        response = {RESPONSE_STATUS: STATUS_OK,
                    RESPONSE_MESSAGE: ""}
        http_status = 200
        id = get_data_param(request, 'id', None)
        group_value = get_data_param(request, 'group_value', None)
        individual_value = (get_data_param(request, 'individual_value', None))
        if individual_value:
            individual_value = str(individual_value)
            individual_value.replace("'", "\"")
        performed_start_time = (get_data_param(request, 'performed_start_time', None))
        performed_end_time = get_data_param(request, 'performed_end_time', None)
        performed_comments = get_data_param(request, 'performed_comments', None)
        if not performed_start_time or not performed_end_time or not id:
            response[RESPONSE_MESSAGE] = constants.TEXT_PARAMS_MISSING
            http_status = 400
            response[RESPONSE_STATUS] = STATUS_ERROR
            return generic_response(response_body=response, http_status=http_status)
        activity_list = ActivityList.objects.filter(group=int(id))
        if activity_list[0].perform_individually:
            if not individual_value:
                response[RESPONSE_MESSAGE] = constants.TEXT_PARAMS_MISSING
                http_status = 400
                response[RESPONSE_STATUS] = STATUS_ERROR
                return generic_response(response_body=response, http_status=http_status)
        else:
            if not group_value:
                response[RESPONSE_MESSAGE] = constants.TEXT_PARAMS_MISSING
                http_status = 400
                response[RESPONSE_STATUS] = STATUS_ERROR
                return generic_response(response_body=response, http_status=http_status)
        performed_start_time = dateparse.parse_datetime(performed_start_time).astimezone()
        performed_end_time = dateparse.parse_datetime(performed_end_time).astimezone()

        if activity_list:
            if activity_list[0].perform_individually:
                individual_value = ast.literal_eval(individual_value)
            for obj in activity_list:
                obj.performed_start_time = performed_start_time
                obj.performed_end_time = performed_end_time
                obj.performed_comments = performed_comments
                if obj.perform_individually:
                    obj.individual_value = individual_value.get(str(obj.animal_id))
                else:
                    obj.group_value = group_value

                obj.is_on_time = (obj.scheduled_start_time >= performed_start_time)
                obj.action_status=Options.objects.get(key=obj.action_status.key, value=COMPLETE)
                obj.save()

            response[RESPONSE_MESSAGE] = "Updated"
            http_status = 200
            response[RESPONSE_STATUS] = STATUS_OK
            return generic_response(response_body=response, http_status=http_status)
        else:
            response[RESPONSE_MESSAGE] = DEFAULT_ERROR_MESSAGE
            http_status = 404
            response[RESPONSE_STATUS] = STATUS_ERROR
            return generic_response(response_body=response, http_status=http_status)


class SchedulingActivityView(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def post(self, request):
        import ast
        from django.utils import dateparse
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: constants.DEFAULT_ERROR_MESSAGE}
        http_status = 400
        comments = get_data_param(request, 'comments', None)
        customer = get_data_param(request, 'customer', None)
        routine_type = get_data_param(request, 'routine_type', None)
        activity_type = get_data_param(request, 'activity_type', None)
        activity_priority = get_data_param(request, 'activity_priority', None)
        scheduled_start_time = dateparse.parse_time(get_data_param(request, 'scheduled_start_time', '00:00:00'))
        scheduled_end_time = dateparse.parse_time(get_data_param(request, 'scheduled_end_time', '00:00:00'))
        scheduled_start_date = dateparse.parse_date(get_data_param(request, 'scheduled_start_date', '2017-11-08'))
        scheduled_end_date = dateparse.parse_date(get_data_param(request, 'scheduled_end_date', '2017-11-08'))
        perform_individually = bool(get_data_param(request, 'perform_individually', True))
        user_assigned = int(get_data_param(request, 'user_assigned', 1))
        animals = (get_data_param(request, 'animals', None))
        herds = (get_data_param(request, 'herds', None))
        if (not herds and not animals) or not customer:
            response[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        else:
            scheduling = Scheduling()
            scheduling.comments = comments
            scheduling.routine_type_id = int(routine_type)
            scheduling.activity_type_id = int(activity_type)
            scheduling.activity_priority_id = int(activity_priority)
            scheduling.scheduled_start_time = scheduled_start_time
            scheduling.scheduled_end_time = scheduled_end_time
            scheduling.scheduled_start_date = scheduled_start_date
            scheduling.scheduled_end_date = scheduled_end_date
            scheduling.perform_individually = perform_individually
            scheduling.is_active = True
            scheduling.scheduled_next_date = scheduled_start_date
            scheduling.assigned_to_id = user_assigned
            scheduling.customer_id = int(customer)
            scheduling.save()
            if animals:
                animal_list = [int(i) for i in (ast.literal_eval(animals))]
                for i in animal_list:
                    scheduling.animal.add(Entity.objects.get(pk=i))
                scheduling.save()
            elif herds:
                herd_list = [int(i) for i in (ast.literal_eval(herds))]
                for i in herd_list:
                    obj = Entity.objects.get(pk=i)
                    list = obj.assignment_parent.first().get_all_childs()
                    for o in list:
                        scheduling.animal.add(Entity.objects.get(pk=int(o['child_id'])))
                scheduling.save()

            response[RESPONSE_MESSAGE] = "Inserted"
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
        return generic_response(response_body=response, http_status=http_status)

    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        response = {RESPONSE_STATUS: STATUS_OK,
                    RESPONSE_MESSAGE: ""}
        http_status = 200
        pk = (get_default_param(request, 'pk', None))
        customer = (get_default_param(request, 'customer', None))
        activity_type = (get_default_param(request, 'activity_type', None))
        routine_type = (get_default_param(request, 'routine_type', None))
        staff_assigned = (get_default_param(request, 'staff_assigned', None))
        start_date = (get_default_param(request, 'start_date', None))
        end_date = (get_default_param(request, 'end_date', None))
        start_time = (get_default_param(request, 'start_time', None))
        end_time = (get_default_param(request, 'end_time', None))
        cow_id = (get_default_param(request, 'cow_id', None))
        if not customer:
            response[RESPONSE_MESSAGE] = TEXT_OPERATION_SUCCESSFUL
            response[RESPONSE_STATUS] = STATUS_ERROR
            http_status = 400
        elif pk:
            data = (Scheduling.objects.filter(pk=pk))
            if data:
                response[RESPONSE_DATA] = data[0].to_dict()
        elif activity_type:
            list = Scheduling.objects.filter(activity_type_id=activity_type, customer_id=int(customer))
            response[RESPONSE_DATA] = [obj.to_dict() for obj in list]
        elif routine_type:
            list = Scheduling.objects.filter(routine_type_id=routine_type, customer_id=int(customer))
            response[RESPONSE_DATA] = [obj.to_dict() for obj in list]
        elif staff_assigned:
            list = Scheduling.objects.filter(assigned_to_id=staff_assigned, customer_id=int(customer))
            response[RESPONSE_DATA] = [obj.to_dict() for obj in list]
        elif cow_id:
            list = Scheduling.objects.filter(animal__id=cow_id, customer_id=int(customer))
            response[RESPONSE_DATA] = [obj.to_dict() for obj in list]
        elif start_date and end_date:
            start_date = dateparse.parse_date(start_date)
            end_date = dateparse.parse_date(end_date)
            if start_time and end_time:
                start_time = dateparse.parse_time(start_time)
                end_time = dateparse.parse_time(end_time)
                list = Scheduling.objects.filter(scheduled_start_date__gte=start_date,
                                                 scheduled_start_time__gte=start_time,
                                                 scheduled_end_date__lte=end_date,
                                                 scheduled_end_time__lte=end_time, customer_id=int(customer))
                response[RESPONSE_DATA] = [obj.to_dict() for obj in list]
            else:
                list = Scheduling.objects.filter(scheduled_start_date__gte=start_date,
                                                 scheduled_end_date__lte=end_date, customer_id=int(customer))
                response[RESPONSE_DATA] = [obj.to_dict() for obj in list]
        else:
            list = Scheduling.objects.filter(customer_id=int(customer))
            response[RESPONSE_DATA] = [obj.to_dict() for obj in list]
        return generic_response(response_body=response, http_status=http_status)

    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def patch(self, request):
        from django.utils import dateparse
        import ast
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: constants.DEFAULT_ERROR_MESSAGE}
        http_status = 400
        id = get_data_param(request, 'id', None)
        comments = get_data_param(request, 'comments', None)
        routine_type = get_data_param(request, 'routine_type', None)
        activity_type = get_data_param(request, 'activity_type', None)
        activity_priority = get_data_param(request, 'activity_priority', None)
        scheduled_start_time = (get_data_param(request, 'scheduled_start_time', None))
        scheduled_end_time = (get_data_param(request, 'scheduled_end_time', None))
        scheduled_start_date = (get_data_param(request, 'scheduled_start_date', None))
        scheduled_end_date = (get_data_param(request, 'scheduled_end_date', None))
        perform_individually = (get_data_param(request, 'perform_individually', None))
        user_assigned = (get_data_param(request, 'user_assigned', None))
        animals = (get_data_param(request, 'animals', None))
        if id:
            id = int(id)
            schedule = Scheduling.objects.get(pk=id)
            schedule.comments = comments if comments else schedule.comments
            schedule.routine_type = int(routine_type) if routine_type else schedule.routine_type
            schedule.activity_type = int(activity_type) if activity_type else schedule.activity_type
            schedule.activity_priority = int(activity_priority) if activity_priority else schedule.activity_priority
            schedule.scheduled_start_time = dateparse.parse_time(
                scheduled_start_time) if scheduled_start_time else schedule.scheduled_start_time
            schedule.scheduled_end_time = dateparse.parse_time(
                scheduled_end_time) if scheduled_end_time else schedule.scheduled_end_time
            schedule.scheduled_start_date = dateparse.parse_date(
                scheduled_start_date) if scheduled_start_date else schedule.scheduled_start_date
            schedule.scheduled_end_date = dateparse.parse_date(
                scheduled_end_date) if scheduled_end_date else schedule.scheduled_end_date
            schedule.perform_individually = bool(
                perform_individually) if perform_individually else schedule.perform_individually
            schedule.assigned_to = int(user_assigned) if user_assigned else schedule.assigned_to
            if animals:
                try:
                    results = [int(i) for i in (ast.literal_eval(animals))]
                    schedule.animal.clear()
                    for i in results:
                        schedule.animal.add(Entity.objects.get(pk=i))
                except Exception as e:
                    response[RESPONSE_MESSAGE] = DEFAULT_ERROR_MESSAGE + str(e)
                    response[RESPONSE_STATUS] = STATUS_ERROR
                    http_status = 400
                    return generic_response(response_body=response, http_status=http_status)
            schedule.save()
            response[RESPONSE_MESSAGE] = "Activity Scheduled Successfully"
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
        else:
            response[RESPONSE_MESSAGE] = constants.TEXT_PARAMS_MISSING

        return generic_response(response_body=response, http_status=http_status)


class GroupActivities(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        SCHEDULED = "scheduled"
        from ioa.utils import get_complete_activities, get_incomplete_activities,\
            get_pending_activities, get_scheduled_activities
        response = {RESPONSE_STATUS: STATUS_OK,
                    RESPONSE_MESSAGE: ""}
        http_status = 200
        print('calling')
        response[RESPONSE_DATA] = {}
        activities = {
            COMPLETE: [],
            PENDING: [],
            INCOMPLETE: [],
            SCHEDULED: [],
            OBJECT_DETAILS: {}
        }
        customer_id = (get_default_param(request, 'customer', None))
        animal_id = (get_default_param(request, 'animal', None))
        herd_id = (get_default_param(request, 'herd', None))
        assigned_to_id = (get_default_param(request, 'staff', None))
        if not customer_id:
            response[RESPONSE_MESSAGE] = constants.TEXT_PARAMS_MISSING
        else:
            activities[COMPLETE] = get_complete_activities(customer_id, animal_id, assigned_to_id)
            activities[PENDING] = get_pending_activities(customer_id, animal_id, assigned_to_id)
            activities[INCOMPLETE] = get_incomplete_activities(customer_id, animal_id, assigned_to_id)
            activities[SCHEDULED] = get_scheduled_activities(customer_id, animal_id, assigned_to_id)


            if animal_id:
                activities[OBJECT_DETAILS] = Entity.objects.get(id=animal_id).animal_details_to_dict()
            elif assigned_to_id:
                activities[OBJECT_DETAILS] = User.objects.get(id=assigned_to_id).user_as_json()
            activity_priority = utils.get_activities_count_priority(customer_id=customer_id,
                                                                    h_id=herd_id, a_id=animal_id, s_id=assigned_to_id)
            response[RESPONSE_DATA][ACTIVITY_ACTION_STATUS] = activities
            response[RESPONSE_DATA][ACTIVITY_PRIORITY] = activity_priority
        return generic_response(response_body=response, http_status=http_status)


class ScheduleAnActivity(APIView):

    def post(self, request,format=None):
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        serializer = SchedulingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            response_body[RESPONSE_DATA] = data
            return generic_response(response_body=response_body, http_status=200)
        return generic_response(response_body=serializer.errors, http_status=400)

    def get(self, request):
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        scheduled_start_date = request.GET.get('scheduled_start_date')
        scheduled_end_date = request.GET.get('scheduled_end_date')

        obj = Scheduling.objects.all().filter(scheduled_start_date__range=
                                    (scheduled_start_date, scheduled_end_date)
                                    ,scheduled_end_date__range= (scheduled_start_date,
                                    scheduled_end_date))
        date_dict = {}
        for d in obj:
            date_dict[d.comments, d.scheduled_start_time,
            d.scheduled_end_time, d.scheduled_start_date,
            d.scheduled_end_date]= d
        response_body[RESPONSE_DATA] = list(date_dict)
        return generic_response(response_body=response_body, http_status=200)

    def delete(self, request, pk, format=None):
        obj = Scheduling.objects.filter(pk=pk)
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        if obj:
            obj = obj[0]
            obj.delete()
            data = obj.id
            response_body[RESPONSE_DATA] = data
            return generic_response(response_body=response_body, http_status=200)
        return response_body

    def patch(self, request, pk):
        obj = Scheduling.objects.filter(pk=pk)
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
        if obj:
            obj = obj[0]
            serializer = SchedulingSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response_body[RESPONSE_DATA] = data
                return generic_response(response_body=response_body, http_status=200)
            return response_body


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_activity(self, pk):
    obj = Scheduling.objects.filter(pk=pk)
    response_msg = {RESPONSE_MESSAGE: DEFAULT_ERROR_MESSAGE}
    resp = generic_response(response_body=response_msg, http_status=200,
                            header_dict={})
    if obj:
        obj = obj[0]
        serializer = SchedulingSerializer(obj)
        data = serializer.data
        return generic_response(data, http_status=200)
    return resp


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_activity_details_list(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: {}}
    customer = self.query_params["customer"]
    action_type = self.query_params["action_type"]
    out_res=[]
    if action_type == SCHEDULED:
        out_res = get_scheduled_activities(customer)
    elif action_type == COMPLETE:
        out_res = get_complete_activities(customer)
    elif action_type == INCOMPLETE:
        out_res = get_incomplete_activities(customer)
    elif action_type == PENDING:
        out_res = get_pending_activities(customer)

    response_body[RESPONSE_DATA][action_type] = out_res

    return generic_response(response_body=response_body, http_status=200)


class GroupActivitiesCount(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        from ioa.utils import get_complete_activities, get_incomplete_activities,\
            get_pending_activities, get_scheduled_activities
        response = {RESPONSE_STATUS: STATUS_OK,
                    RESPONSE_MESSAGE: ""}
        http_status = 200
        response[RESPONSE_DATA] = {}
        activities = {
            "completed": {
                MILKING: 0,
                FEEDING: 0,
                BREEDING: 0,
                TOTAL: 0,
            },
            "pending": {
                MILKING: 0,
                FEEDING: 0,
                BREEDING: 0,
                TOTAL: 0,
            },
            "incomplete": {
                MILKING: 0,
                FEEDING: 0,
                BREEDING: 0,
                TOTAL: 0,
            },
            "scheduled": {
                MILKING: 0,
                FEEDING: 0,
                BREEDING: 0,
                TOTAL: 0,
            }
        }
        customer_id = (get_default_param(request, 'customer', None))
        herd_id = (get_default_param(request, 'herd', None))
        animal_id = (get_default_param(request, 'animal', None))
        staff_id = (get_default_param(request, 'staff', None))
        start_date = (get_default_param(request, 'start_date', None))
        if not customer_id :
            response[RESPONSE_MESSAGE] = constants.TEXT_PARAMS_MISSING
        else:
            start_date = start_date if start_date else str((datetime.now()-timedelta(days=10)).date())
            prev_date = datetime.combine(dateparse.parse_date(start_date), datetime.min.time())
            created_date = str(datetime.now().date())
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
            customer_id = int(customer_id)
            activities["completed"][MILKING] = get_completed_activities_count(customer_id,
                                                                              next_date,prev_date,
                                                                              MILKING)
            activities["completed"][FEEDING] = get_completed_activities_count(customer_id,
                                                                              next_date, prev_date,
                                                                              FEEDING)
            activities["completed"][BREEDING] = get_completed_activities_count(customer_id,
                                                                              next_date, prev_date,
                                                                              BREEDING)
            activities["completed"][TOTAL] = activities["completed"][MILKING] +\
                                             activities["completed"][FEEDING] + activities["completed"][BREEDING]
            activities["incomplete"][MILKING] = get_incomplete_activities_count(customer_id,
                                                                                next_date, prev_date,
                                                                                MILKING)
            activities["incomplete"][FEEDING] = get_incomplete_activities_count(customer_id,
                                                                                next_date, prev_date,
                                                                                FEEDING)
            activities["incomplete"][BREEDING] = get_incomplete_activities_count(customer_id,
                                                                                 next_date, prev_date,
                                                                                 BREEDING)
            activities["incomplete"][TOTAL] = activities["incomplete"][MILKING] + \
                                             activities["incomplete"][FEEDING] + activities["incomplete"][BREEDING]
            activities["scheduled"][MILKING] = get_scheduled_activities_count(customer_id,
                                                                              next_date, prev_date,
                                                                              MILKING)
            activities["scheduled"][FEEDING] = get_scheduled_activities_count(customer_id,
                                                                              next_date, prev_date,
                                                                              FEEDING)
            activities["scheduled"][BREEDING] = get_scheduled_activities_count(customer_id,
                                                                               next_date, prev_date,
                                                                               BREEDING)
            activities["scheduled"][TOTAL] = activities["scheduled"][MILKING] + \
                                             activities["scheduled"][FEEDING] + activities["scheduled"][BREEDING]

            activities["priority"] = utils.get_activities_count_priority \
                (customer_id=customer_id, h_id=herd_id, a_id=animal_id, s_id=staff_id)
            response[RESPONSE_DATA] = activities
        return generic_response(response_body=response, http_status=http_status)


class ActivityGraphStatistics(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        response = {RESPONSE_STATUS: STATUS_ERROR,
                    RESPONSE_MESSAGE: constants.DEFAULT_ERROR_MESSAGE}
        http_status = 400
        customer_id = (get_default_param(request, 'customer', None))
        herd_id = (get_default_param(request, 'herd', None))
        activity_type = (get_default_param(request, 'activity_type', None))
        days = (get_default_param(request, 'days', None))
        if not customer_id:
            response[RESPONSE_MESSAGE] = constants.TEXT_PARAMS_MISSING
        else:
            days = int(days) if days else LAST_WEEK
            customer_id = int(customer_id)
            response[RESPONSE_MESSAGE] = ""
            response[RESPONSE_STATUS] = STATUS_OK
            http_status = 200
            response[RESPONSE_DATA] = {FEEDING: [], MILKING: []}
            created_date = str(datetime.now().date())
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            prev_date = created_date_time - timedelta(days=days)  # , hours=23, minutes=59, seconds=59)
            next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
            if activity_type in [FEEDING, MILKING]:
                if activity_type == FEEDING:
                    response[RESPONSE_DATA][FEEDING] = utils.get_feeding_aggregation(customer_id, prev_date, next_date,
                                                                                     herd_id)
                elif activity_type == MILKING:
                    response[RESPONSE_DATA][MILKING] = utils.get_milking_aggregation(customer_id, prev_date, next_date,
                                                                                     herd_id)
            else:
                response[RESPONSE_DATA][FEEDING] = utils.get_feeding_aggregation(customer_id, prev_date, next_date,
                                                                                 herd_id)
                response[RESPONSE_DATA][MILKING] = utils.get_milking_aggregation(customer_id, prev_date, next_date,
                                                                                 herd_id)
        return generic_response(response_body=response, http_status=http_status)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_milking_feeding_value_total(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    activity_type = self.query_params.get("activity_type")
    time_range = datetime.date.today() - timedelta(days=float(self.query_params.get("days")))
    response_body[RESPONSE_DATA] = list(get_total_milk_feed(act_type=activity_type, time_range=time_range))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def last_week_max_milk_yield(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    curr_date = dt.date.today()
    curr_start_date = curr_date - timedelta(days=LAST_WEEK)
    curr_end_date = curr_date
    pre_start_date = curr_date - timedelta(days=LAST_2WEEKS)
    pre_end_date = curr_date - timedelta(days=LAST_WEEK)
    q_customer_id = self.query_params.get("customer")
    data = {"current_week": list(util_get_max_milk_yield(q_customer_id, s_date=curr_start_date, e_date=curr_end_date)),
            "previous_week": list(util_get_max_milk_yield(q_customer_id, s_date=pre_start_date, e_date=pre_end_date))}
    response_body[RESPONSE_DATA] = data
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def last_week_feed_consumed(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    curr_date = dt.date.today()
    curr_start_date = curr_date - timedelta(days=LAST_WEEK)
    curr_end_date = curr_date
    pre_start_date = curr_date - timedelta(days=LAST_2WEEKS)
    pre_end_date = curr_date - timedelta(days=LAST_WEEK)
    q_customer_id = self.query_params.get("customer")

    data = {"current_week": list(util_get_feed_consumed(q_customer_id, s_date=curr_start_date, e_date=curr_end_date)),
            "previous_week": list(util_get_feed_consumed(q_customer_id, s_date=pre_start_date, e_date=pre_end_date))}
    response_body[RESPONSE_DATA] = data
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_expected_milk_yield(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    data = {"current_month_milk_yield": str(100.50),
            "previous_month_milk_yield": str(152.9),
            "next_week_expected": [
                {'date': '2017-Oct-01', 'expected_milk': str(4)},
                                   {'date': '2017-Oct-02', 'expected_milk': str(5)},
                                   {'date': '2017-Oct-03', 'expected_milk': str(8)},
                                   {'date': '2017-Oct-04', 'expected_milk': str(10)},
                                   {'date': '2017-Oct-05', 'expected_milk': str(12)},
                                   {'date': '2017-Oct-06', 'expected_milk': str(14)},
                                   {'date': '2017-Oct-07', 'expected_milk': str(8)},
                                   {'date': '2017-Dec-08', 'expected_milk': str(10)},
                                   {'date': '2017-Dec-09', 'expected_milk': str(12)},
                                   {'date': '2017-Dec-11', 'expected_milk': str(14)},
                                   ]
            }
    response_body[RESPONSE_DATA] = data
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_milking_values(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    cust = self.query_params["customer"]
    time_range = datetime.date.today() - timedelta(days=float(self.query_params.get("days")))
    response_body[RESPONSE_DATA] = list(get_activity_stats(c_id=cust, from_dtm=time_range))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_feeding_value_today(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    customer = self.query_params["customer"]
    days = float(self.query_params.get("days"))
    last_month = days + LAST_THIRTY_DAYS
    time_range = datetime.date.today() - timedelta(days=days)
    response_body[RESPONSE_DATA] = list(util_get_feed_consumed_today(c_id=customer, s_date=time_range))
    return generic_response(response_body=response_body, http_status=200)


@csrf_exempt
@api_view(['GET'])
@exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
def get_aggregations(self):
    response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: STATUS_OK, RESPONSE_DATA: []}
    time_range = datetime.date.today() - timedelta(days=float(self.query_params.get("days")))
    response_body[RESPONSE_DATA] = list(testing(date_range=time_range))
    return generic_response(response_body=response_body, http_status=200)


class GetActivitiesStatistics(APIView):
    @exception_handler(generic_response(response_body=ERROR_RESPONSE_BODY, http_status=500))
    def get(self, request):
        from django.utils import dateparse
        from datetime import datetime
        from ioa.utils import get_complete_activities, get_incomplete_activities, \
            get_pending_activities, get_scheduled_activities
        response = {RESPONSE_STATUS: STATUS_OK,
                    RESPONSE_MESSAGE: ""}
        http_status = 200
        response[RESPONSE_DATA] = {}
        # activity_status = {}
        activity_priorities = {}
        activities = {
            "completed": {
                MILKING: 0,
                FEEDING: 0,
                BREEDING: 0,
                TOTAL: 0,
            },
            "pending": {
                MILKING: 0,
                FEEDING: 0,
                BREEDING: 0,
                TOTAL: 0,
            },
            "incomplete": {
                MILKING: 0,
                FEEDING: 0,
                BREEDING: 0,
                TOTAL: 0,
            },
            "scheduled": {
                MILKING: 0,
                FEEDING: 0,
                BREEDING: 0,
                TOTAL: 0,
            }
        }
        customer_id = (get_default_param(request, 'customer', None))
        herd_id = (get_default_param(request, 'herd', None))
        animal_id = (get_default_param(request, 'animal', None))
        staff_id = (get_default_param(request, 'staff', None))
        start_date = (get_default_param(request, 'start_date', None))
        if not customer_id:
            response[RESPONSE_MESSAGE] = constants.TEXT_PARAMS_MISSING
        else:
            start_date = start_date if start_date else str((datetime.now() - timedelta(days=10)).date())
            prev_date = datetime.combine(dateparse.parse_date(start_date), datetime.min.time())
            created_date = str(datetime.now().date())
            created_date_time = datetime.combine(dateparse.parse_date(created_date), datetime.min.time())
            next_date = created_date_time + timedelta(hours=23, minutes=59, seconds=59)
            customer_id = int(customer_id)
            activities["completed"][MILKING] = get_completed_activities_count(customer_id,
                                                                              next_date, prev_date,
                                                                              MILKING)
            activities["completed"][FEEDING] = get_completed_activities_count(customer_id,
                                                                              next_date, prev_date,
                                                                              FEEDING)
            activities["completed"][BREEDING] = get_completed_activities_count(customer_id,
                                                                               next_date, prev_date,
                                                                               BREEDING)
            activities["completed"][TOTAL] = activities["completed"][MILKING] + \
                                             activities["completed"][FEEDING] + activities["completed"][BREEDING]
            activities["incomplete"][MILKING] = get_incomplete_activities_count(customer_id,
                                                                                next_date, prev_date,
                                                                                MILKING)
            activities["incomplete"][FEEDING] = get_incomplete_activities_count(customer_id,
                                                                                next_date, prev_date,
                                                                                FEEDING)
            activities["incomplete"][BREEDING] = get_incomplete_activities_count(customer_id,
                                                                                 next_date, prev_date,
                                                                                 BREEDING)
            activities["incomplete"][TOTAL] = activities["incomplete"][MILKING] + \
                                              activities["incomplete"][FEEDING] + activities["incomplete"][BREEDING]
            activities["scheduled"][MILKING] = get_scheduled_activities_count(customer_id,
                                                                              next_date, prev_date,
                                                                              MILKING)
            activities["scheduled"][FEEDING] = get_scheduled_activities_count(customer_id,
                                                                              next_date, prev_date,
                                                                              FEEDING)
            activities["scheduled"][BREEDING] = get_scheduled_activities_count(customer_id,
                                                                               next_date, prev_date,
                                                                               BREEDING)
            activities["scheduled"][TOTAL] = activities["scheduled"][MILKING] + \
                                             activities["scheduled"][FEEDING] + activities["scheduled"][BREEDING]

            activity_priorities = utils.get_activities_count_priority \
                (customer_id=customer_id, h_id=herd_id, a_id=animal_id, s_id=staff_id)

            response[RESPONSE_DATA]['activity_status'] = activities
            response[RESPONSE_DATA]['activity_priority'] = activity_priorities
        return generic_response(response_body=response, http_status=http_status)

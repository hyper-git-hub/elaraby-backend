from django.db.models import Count, F
from hypernet.models import Assignment
from ioa.models import ActivityList, Aggregation


def get_activity_by_group(customer_id, group_id):
    data = []
    activity_list = ActivityList.objects.filter(group=group_id, customer_id=customer_id)
    if activity_list.count() > 1:
        if activity_list[0].perform_individually:
            animal_data = [{"animal_id": o.animal_id,
                            "individual_value": o.individual_value} for o in activity_list]
        else:
            animal_data = [{"animal_id": o.animal.id} for o in activity_list]
        data.append(activity_list[0].to_dict(animal_data))
    return data


def get_activities_by_status(customer_id, status_id):
    data = []
    activities = ActivityList.objects.filter(action_status__value=status_id, customer_id=customer_id)
    groups = activities.order_by().values('group').distinct()
    for g in groups:
        activity_list = ActivityList.objects.filter(group=int(g['group']), action_status__value=status_id)
        if activity_list[0].perform_individually:
            animal_data = [{"animal_id": o.animal.id,
                            "individual_value": o.individual_value} for o in activity_list]
        else:
            animal_data = [{"animal_id": o.animal.id} for o in activity_list]
        data.append(activity_list[0].to_dict(animal_data))
    return data


def get_activities_by_type(customer_id, activity_type_id):
    data = []
    activities = ActivityList.objects.filter(activity_type__value=activity_type_id, customer_id=customer_id)
    groups = activities.order_by().values('group').distinct()
    for g in groups:
        activity_list = ActivityList.objects.filter(group=int(g['group']))
        if activity_list[0].perform_individually:
            animal_data = [{"animal_id": o.animal.id,
                            "individual_value": o.individual_value} for o in activity_list]
        else:
            animal_data = [{"animal_id": o.animal.id} for o in activity_list]
        data.append(activity_list[0].to_dict(animal_data))
    return data


def get_activities_by_animal(customer_id, animal_id):
    data = []
    activities = ActivityList.objects.filter(animal_id=animal_id, customer_id=customer_id)
    groups = activities.order_by().values('group').distinct()
    for g in groups:
        activity_list = ActivityList.objects.filter(group=int(g['group']))
        if activity_list[0].perform_individually:
            animal_data = [{"animal_id": o.animal.id,
                            "individual_value": o.individual_value} for o in activity_list]
        else:
            animal_data = [{"animal_id": o.animal.id} for o in activity_list]
        data.append(activity_list[0].to_dict(animal_data))
    return data


def get_activities_by_priority(customer_id, priority_id):
    data = []
    activities = ActivityList.objects.filter(activity_priority__value=priority_id, customer_id=customer_id)
    groups = activities.order_by().values('group').distinct()
    for g in groups:
        activity_list = ActivityList.objects.filter(group=int(g['group']), activity_priority__value=priority_id)
        if activity_list[0].perform_individually:
            animal_data = [{"animal_id": o.animal.id,
                            "individual_value": o.individual_value} for o in activity_list]
        else:
            animal_data = [{"animal_id": o.animal.id} for o in activity_list]
        data.append(activity_list[0].to_dict(animal_data))
    return data


def util_get_all_activities(customer_id):
    data = []
    groups = ActivityList.objects.filter(customer_id=customer_id).order_by().values('group').distinct()
    for g in groups:
        activity_list = ActivityList.objects.filter(group=int(g['group']))
        if activity_list[0].perform_individually:
            animal_data = [{"animal_id": o.animal.id,
                            "individual_value": o.individual_value} for o in activity_list]
        else:
            animal_data = [{"animal_id": o.animal.id} for o in activity_list]
        data.append(activity_list[0].to_dict(animal_data))
    return data

# TODO: same func in aggregation_utils - with filter flag diff
def get_feeding_aggregation(customer_id, prev_date, next_date, h_id=None):
    if h_id:
        data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                          herd_id__exact=h_id,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=False,
                                      avg_milk_yield__isnull=True,
                                      created_datetime__gte=prev_date,
                                      created_datetime__lt=next_date)
    else:
        data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                          herd_id__isnull=True,
                                          animal_id__isnull=True,
                                          feeding_value__isnull=False,
                                          avg_milk_yield__isnull=True,
                                          created_datetime__gte=prev_date,
                                          created_datetime__lt=next_date)
    result = [obj.customer_graph_feeding() for obj in data]
    return result

# TODO: same func in aggregation_utils - with filter flag diff
def get_milking_aggregation(customer_id, prev_date, next_date, h_id=None):
    if h_id:
        data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                          herd_id__exact=h_id,
                                      animal_id__isnull=True,
                                      feeding_value__isnull=True,
                                      avg_milk_yield__isnull=False,
                                      created_datetime__gte=prev_date,
                                      created_datetime__lt=next_date).order_by('created_datetime')
    else:
        data = Aggregation.objects.filter(customer_aggregations_id=customer_id,
                                          herd_id__isnull=True,
                                          animal_id__isnull=True,
                                          feeding_value__isnull=True,
                                          avg_milk_yield__isnull=False,
                                          created_datetime__gte=prev_date,
                                          created_datetime__lt=next_date).order_by('created_datetime')
    result = [obj.customer_graph_milking() for obj in data]
    return result


def get_activities_count(customer_id, a_id):
    return ActivityList.objects.filter(customer=customer_id, animal=a_id).values('activity_type').annotate(
        total=Count('activity_type'))


def get_activities_count_priority(customer_id, h_id=None, a_id=None, s_id=None):
    if h_id:
        herd = Assignment.objects.filter(parent=h_id).values('child__id')
        print(herd)
        q_set = ActivityList.objects.filter(customer=customer_id, animal_id__in=herd)
    elif s_id:
        q_set = ActivityList.objects.filter(customer=customer_id, assigned_to_activity=s_id)
    elif a_id:
        q_set = ActivityList.objects.filter(customer=customer_id, animal=a_id)
    else:
        q_set = ActivityList.objects.filter(customer=customer_id)
    print(len(q_set))

    # activity_list = []
    # activity_dict = {}
    # for activity in q_set:
    #     activity_dict[activity.activity_priority.value] = q_set.filter(activity_priority=activity.activity_priority).count()
    # activity_list.append(activity_dict)
    # return activity_list
    return list(q_set.values(type=F('activity_priority__value')).annotate(total=Count('activity_priority')))

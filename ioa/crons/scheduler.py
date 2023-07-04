from asyncio import async
from ioa.models import ActivityList, Aggregation, AnimalStates
from user.models import *
from .cron_utils import *
# from djutils.decorators import async

def testing(date_range):
    instance = ActivityList.objects.filter(performed_end_time__gte=date_range)
    for d in instance:
        agg_data = [
            Aggregation
                (
                animal=d.animal,
                avg_milk_yield=d.individual_value,
                avg_standing_time=d.individual_value,
                avg_rumination_time=d.individual_value,
                avg_sitting_time=d.individual_value,
                avg_temperature=d.individual_value,
                created_datetime=datetime.date.today(),
                created_by=User.objects.filter(customer_id=1)[0],
                modified_by=User.objects.filter(customer_id=1)[0],
            )
        ]
        aggregation = Aggregation.objects.bulk_create(agg_data)
        return list(aggregation)


# @async

def cron_job_IOA_alerts():
    # try:
    predata_set = get_pre_data_set()
    if predata_set:
        for values in predata_set:
            result = ML_service_IOA(pre_data=values)
            if result:
                insertion_post_data(predata_obj=predata_set)
                animal_states = json.loads(result.decode('utf'))
                state = animal_states['Results']['output1']['value']['Values'][0][0]
                save_animal_state(values=values, state=state)
                delete_pre(pre_data_id=values.id)
                # except Exception as e:
                #   print('Failed' + str(e))
    async(cron_job_IOA_alerts())

__author__ = 'nahmed'

import datetime
from django.utils import timezone

from hypernet.models import HypernetNotification, DeviceViolation
from hypernet.constants import IOA_VIOLATION_THRESHOLD, RUMINATION, ESTRUS, LAMENESS, IOA_ESTRUS_CRITERIA, \
    IOA_VIOLATION_INTERVAL
from hypernet.enums import IOAOPTIONSEnum, ModuleEnum, OptionsEnum
from ioa.models import AnimalStates, EstrusCriteria



def animal_state_cron():
    """
    Separate cron for each state - good if Django runs them in parallel (test results with async).

    :return:
    """
    # TODO move it to scheduler, cron_utils - discuss
    # TODO use prefetch_related
    violations_all = DeviceViolation.objects.filter(enabled=True, module=ModuleEnum.IOA,
                                                    next_trigger_datetime__lt=timezone.now())  # all the active alerts
    print("Total violations - {0}".format(violations_all.count()))
    """
    Lactation Status: Don't generate the alert for Pregnant Cows, Dry-Pre-calving, Dry Post Calving, Only Bred and
    Non-Bred Cows or Heifers can have an Estrus Alert.
    Exclude - group->CALF; lactation_status->PREGNANT.
    """
    # an elegant solution than chained filters - is using Q objects
    estrus_alerts = violations_all.filter(violation_type=IOAOPTIONSEnum.ALERT_TYPE_ESTRUS).\
        exclude(device__group=IOAOPTIONSEnum.ANIMAL_GROUP_IN_CALFS).\
        exclude(device__lactation_status=IOAOPTIONSEnum.LACTATION_STATUS_PREGNANT)

    lameness_alerts = violations_all.filter(violation_type=IOAOPTIONSEnum.ALERT_TYPE_LAMENESS)
    rumination_alerts = violations_all.filter(violation_type=IOAOPTIONSEnum.ALERT_TYPE_RUMINATION)

    # TODO have the entry saved individually
    # notification_list = []  # append all the notifications here, and bulk insert
    time_24_hours_ago = timezone.now() - datetime.timedelta(days=1)
    # ---------------- Rumination ---------------
    if rumination_alerts:
        print("Rumination alerts - {0}".format(rumination_alerts.count()))
        for alert in rumination_alerts:
            rumination_state_time = AnimalStates.objects.filter(animal=alert.device,
                                                                # alert_state=IOAOPTIONSEnum.ALERT_TYPE_RUMINATION,
                                                                animal_state__icontains=RUMINATION,
                                                                created_datetime__gt=time_24_hours_ago
                                                                # consider states within last 24 hours
                                                                ).exclude(created_datetime__lt=alert.trigger_datetime
                                                                          # skip previously used states
                                                                          ).values_list('frequency', flat=True)
            if rumination_state_time:
                print("Rumination states - {0}".format(rumination_state_time.count()))
                # summing up 'frequency', as number of seconds entity was in rumination state
                if sum(rumination_state_time) < IOA_VIOLATION_THRESHOLD[RUMINATION]:
                    print("Rumination Threshold reached for alert - {0}".format(alert.id))
                    # notification = HypernetNotification(
                    #     device=alert.device,
                    #     timestamp=datetime.datetime.now(),
                    #     violation_type=IOAOPTIONSEnum.ALERT_TYPE_RUMINATION,
                    #     threshold=IOA_VIOLATION_THRESHOLD['rumination_threshold'],
                    #     value=sum(rumination_state_time),
                    #     customer=alert.customer,
                    #     module=ModuleEnum.IOA
                    #     )
                    # notification_list.append(notification)  # as per HypernetNotification
                    notification = HypernetNotification()
                    notification.device = alert.device
                    notification.timestamp = timezone.now()  # TODO use the one from AnimalStates/sensor
                    notification.violation_type_id = IOAOPTIONSEnum.ALERT_TYPE_RUMINATION
                    notification.threshold = IOA_VIOLATION_THRESHOLD[RUMINATION]
                    notification.value = sum(rumination_state_time)
                    notification.customer = alert.customer
                    notification.module_id = ModuleEnum.IOA
                    notification.status_id = OptionsEnum.ACTIVE
                    notification.save()
                    # --- Update the last trigger time --
                    t_delta = 24 / IOA_VIOLATION_INTERVAL.get(RUMINATION)  # set forward as per max alerts per day
                    alert.next_trigger_datetime = timezone.now() + datetime.timedelta(hours=t_delta)
                    alert.trigger_datetime = timezone.now()
                    alert.save(update_fields=['trigger_datetime',
                                              'next_trigger_datetime'])  # update the last trigger timestamp for the alert
            else:
                pass  # log a WARN here.
    # --------------- Lameness ----------------
    if lameness_alerts:
        print("Lameness alerts - {0}".format(lameness_alerts.count()))
        for alert in lameness_alerts:
            lameness_state_time = AnimalStates.objects.filter(animal=alert.device,
                                                              # alert_state=IOAOPTIONSEnum.ALERT_TYPE_LAMENESS,
                                                              animal_state__icontains=LAMENESS,
                                                              created_datetime__gt=time_24_hours_ago
                                                              ).exclude(created_datetime__lt=alert.trigger_datetime
                                                                        ).values_list('frequency', flat=True)
            if lameness_state_time:
                print("Lameness states - {0}".format(lameness_state_time.count()))
                # lameness is more than 1 hour in last 24 hours.
                if sum(lameness_state_time) > IOA_VIOLATION_THRESHOLD[LAMENESS]:
                    print("Threshold reached for alert - {0}".format(alert.id))
                    notification = HypernetNotification()
                    notification.device = alert.device
                    notification.timestamp = timezone.now()  # use the one from AnimalStates/sensor
                    notification.violation_type_id = IOAOPTIONSEnum.ALERT_TYPE_LAMENESS
                    notification.threshold = IOA_VIOLATION_THRESHOLD[LAMENESS]
                    notification.value = sum(lameness_state_time)
                    notification.customer = alert.customer
                    notification.module_id = ModuleEnum.IOA
                    notification.status_id = OptionsEnum.ACTIVE
                    notification.save()
                    # --- Update the last trigger time --
                    t_delta = 24 / IOA_VIOLATION_INTERVAL.get(LAMENESS)
                    alert.next_trigger_datetime = timezone.now() + datetime.timedelta(hours=t_delta)
                    alert.trigger_datetime = timezone.now()
                    alert.save(update_fields=['trigger_datetime', 'next_trigger_datetime'])
            else:
                pass  # log a WARN here.
    # ----------------- Estrus -----------------
    if estrus_alerts:
        print("Estrus alert - {0}".format(estrus_alerts.count()))
        # get the superset, and filter it for subset i.e. onset time range is smaller then the end time range
        end_time_range = timezone.now() - datetime.timedelta(seconds=IOA_ESTRUS_CRITERIA['range_for_end'])
        for alert in estrus_alerts:
            estrus_states = AnimalStates.objects.filter(animal=alert.device,
                                                        # alert_state=IOAOPTIONSEnum.ALERT_TYPE_ESTRUS,
                                                        # animal_state__iexact=ESTRUS,
                                                        animal_state__icontains=ESTRUS,
                                                        created_datetime__gt=end_time_range
                                                        ).exclude(created_datetime__lt=alert.trigger_datetime
                                                                  ).values_list('frequency', flat=True)
            if estrus_states:
                ec = EstrusCriteria.objects.get(animal=alert.device)
                onset_time_range = timezone.now() - \
                                   datetime.timedelta(seconds=IOA_ESTRUS_CRITERIA['range_for_onset'])
                # --- IF ONSET ---
                # if more than 10 estrus states in last 10 minutes.
                if len(estrus_states.filter(created_datetime__gte=onset_time_range)) > IOA_ESTRUS_CRITERIA[
                    'onset_threshold']:
                    if ec.estrus_onset:  # already True
                        pass
                    # if it's been 15 days since last estrus ended - so probably it's the new onset.
                    elif ec.current_off_datetime < timezone.now() - datetime.timedelta(
                            seconds=IOA_ESTRUS_CRITERIA['estrus_gap']):
                        # --- update EstrusCriteria timestamps ---
                        ec.last_onset_datetime = ec.current_onset_datetime
                        ec.last_off_datetime = ec.current_off_datetime
                        ec.current_onset_datetime = timezone.now()  # or get timestamp from the back-end.
                        # setting the current_off to future - for presentation.  TODO discuss!
                        ec.current_off_datetime = timezone.now() + datetime.timedelta(
                            seconds=IOA_ESTRUS_CRITERIA['estrus_gap'])
                        ec.estrus_onset = True
                        ec.save()
                        # --- trigger notification ---
                        notification = HypernetNotification()
                        notification.device = alert.device
                        notification.timestamp = timezone.now()  # use the one from AnimalStates/sensor
                        notification.violation_type_id = IOAOPTIONSEnum.ALERT_TYPE_ESTRUS
                        notification.threshold = IOA_VIOLATION_THRESHOLD[ESTRUS]
                        notification.value = len(estrus_states)
                        notification.customer = alert.customer
                        notification.module_id = ModuleEnum.IOA
                        notification.status_id = OptionsEnum.ACTIVE
                        notification.save()
                        # --- Update the last trigger time ---
                        t_delta = 24 / IOA_VIOLATION_INTERVAL.get(ESTRUS)
                        alert.next_trigger_datetime = timezone.now() + datetime.timedelta(hours=t_delta)
                        alert.trigger_datetime = timezone.now()
                        alert.save(update_fields=['trigger_datetime', 'next_trigger_datetime'])
            elif len(estrus_states) > IOA_ESTRUS_CRITERIA['end_threshold']:  # have an estrus state in last 20 min.
                ec = EstrusCriteria.objects.get(animal=alert.device)
                if ec.estrus_onset:  # end the estrus state.
                    # --- update EstrusCriteria timestamps ---
                    # ec.last_off_datetime = ec.current_off_datetime  # handled at onset.
                    ec.current_off_datetime = timezone.now()
                    ec.estrus_onset = False
                    ec.save()

                else:
                    pass
            else:
                pass  # log a WARN here.
    # ------------------- HypernetNotification insertion ----------------
    # or, create it per iteration.
                # print("Number of notifications - {0}".format(len(notification_list)))
    # HypernetNotification.objects.bulk_create(notification_list)
    # log success!


# ------------------------------------------------------------------
def rumination_violations_cron():
    """
    Separate cron for rumination violations.

    :return:
    """
    rumination_alerts = DeviceViolation.objects.filter(enabled=True, module=ModuleEnum.IOA,
                                                       next_trigger_datetime__lt=timezone.now(),
                                                       violation_type=IOAOPTIONSEnum.ALERT_TYPE_RUMINATION
                                                       )
    time_24_hours_ago = timezone.now() - datetime.timedelta(days=1)
    if rumination_alerts:
        for alert in rumination_alerts:
            rumination_state_time = AnimalStates.objects.filter(animal=alert.device,
                                                                animal_state__icontains=RUMINATION,
                                                                created_datetime__gt=time_24_hours_ago
                                                                # consider states within last 24 hours
                                                                ).exclude(created_datetime__lt=alert.trigger_datetime
                                                                          # skip previously used states
                                                                          ).values_list('frequency', flat=True)
            if rumination_state_time:
                # summing up 'frequency', as number of seconds entity was in rumination state
                if sum(rumination_state_time) < IOA_VIOLATION_THRESHOLD[RUMINATION]:
                    notification = HypernetNotification()
                    notification.device = alert.device
                    notification.timestamp = timezone.now()  # TODO use the one from AnimalStates/sensor
                    notification.violation_type_id = IOAOPTIONSEnum.ALERT_TYPE_RUMINATION
                    notification.threshold = IOA_VIOLATION_THRESHOLD[RUMINATION]
                    notification.value = sum(rumination_state_time)
                    notification.customer = alert.customer
                    notification.module_id = ModuleEnum.IOA
                    notification.status_id = OptionsEnum.ACTIVE
                    notification.save()
                    # --- Update the last trigger time --
                    t_delta = 24 / IOA_VIOLATION_INTERVAL.get(RUMINATION)  # set forward as per max alerts per day
                    alert.next_trigger_datetime = timezone.now() + datetime.timedelta(hours=t_delta)
                    alert.trigger_datetime = timezone.now()
                    alert.save(update_fields=['trigger_datetime',
                                              'next_trigger_datetime'])  # update the last trigger timestamp for the alert
            else:
                pass  # log a WARN here.
    else:
        pass  # log a WARN here.


def lamesness_violations_cron():
    """

    :return:
    """
    lameness_alerts = DeviceViolation.objects.filter(enabled=True, module=ModuleEnum.IOA,
                                                     next_trigger_datetime__lt=timezone.now(),
                                                     violation_type=IOAOPTIONSEnum.ALERT_TYPE_LAMENESS
                                                     )
    time_24_hours_ago = timezone.now() - datetime.timedelta(days=1)
    if lameness_alerts:
        for alert in lameness_alerts:
            lameness_state_time = AnimalStates.objects.filter(animal=alert.device,
                                                              animal_state__icontains=LAMENESS,
                                                              created_datetime__gt=time_24_hours_ago
                                                              ).exclude(created_datetime__lt=alert.trigger_datetime
                                                                        ).values_list('frequency', flat=True)
            if lameness_state_time:
                # lameness is more than 1 hour in last 24 hours.
                if sum(lameness_state_time) > IOA_VIOLATION_THRESHOLD[LAMENESS]:
                    notification = HypernetNotification()
                    notification.device = alert.device
                    notification.timestamp = timezone.now()  # use the one from AnimalStates/sensor
                    notification.violation_type_id = IOAOPTIONSEnum.ALERT_TYPE_LAMENESS
                    notification.threshold = IOA_VIOLATION_THRESHOLD[LAMENESS]
                    notification.value = sum(lameness_state_time)
                    notification.customer = alert.customer
                    notification.module_id = ModuleEnum.IOA
                    notification.status_id = OptionsEnum.ACTIVE
                    notification.save()
                    # --- Update the last trigger time ---
                    t_delta = 24 / IOA_VIOLATION_INTERVAL.get(LAMENESS)
                    alert.next_trigger_datetime = timezone.now() + datetime.timedelta(hours=t_delta)
                    alert.trigger_datetime = timezone.now()
                    alert.save(update_fields=['trigger_datetime', 'next_trigger_datetime'])
            else:
                pass  # log a WARN here.
    else:
        pass  # log a WARN here.


def estrus_violations_cron():
    """
    Criteria:
    Lactation Status: Don't generate the alert for Pregnant Cows, Dry-Pre-calving, Dry Post Calving, Only Bred and
    Non-Bred Cows or Heifers can have an Estrus Alert.

    Exclude - group->CALF; lactation_status->PREGNANT.

    :return:
    """
    estrus_alerts = DeviceViolation.objects.filter(enabled=True, module=ModuleEnum.IOA,
                                                   next_trigger_datetime__lt=timezone.now(),
                                                   violation_type=IOAOPTIONSEnum.ALERT_TYPE_ESTRUS,
                                                   ).exclude(device__group=IOAOPTIONSEnum.ANIMAL_GROUP_IN_CALFS). \
        exclude(device__lactation_status=IOAOPTIONSEnum.LACTATION_STATUS_PREGNANT
                )

    time_24_hours_ago = timezone.now() - datetime.timedelta(days=1)
    if estrus_alerts:
        # get the superset, and filter it for subset i.e. onset time range is smaller then the end time range
        end_time_range = timezone.now() - datetime.timedelta(seconds=IOA_ESTRUS_CRITERIA['range_for_end'])
        for alert in estrus_alerts:
            estrus_states = AnimalStates.objects.filter(animal=alert.device,
                                                        animal_state__icontains=ESTRUS,
                                                        created_datetime__gt=end_time_range
                                                        ).exclude(created_datetime__lt=alert.trigger_datetime
                                                                  ).values_list('frequency', flat=True)
            if estrus_states:
                ec = EstrusCriteria.objects.get(animal=alert.device)
                onset_time_range = timezone.now() - \
                                   datetime.timedelta(seconds=IOA_ESTRUS_CRITERIA['range_for_onset'])
                # --- IF ONSET ---
                # if more than 10 estrus states in last 10 minutes.
                if len(estrus_states.filter(created_datetime__gte=onset_time_range)) > IOA_ESTRUS_CRITERIA[
                    'onset_threshold']:
                    if ec.estrus_onset:  # already True
                        pass
                    # if it's been 15 days since last estrus ended - so probably it's the new onset.
                    elif ec.current_off_datetime < timezone.now() - datetime.timedelta(
                            seconds=IOA_ESTRUS_CRITERIA['estrus_gap']):
                        # --- update EstrusCriteria timestamps ---
                        ec.last_onset_datetime = ec.current_onset_datetime
                        ec.last_off_datetime = ec.current_off_datetime
                        ec.current_onset_datetime = timezone.now()  # or get timestamp from the back-end.
                        # setting the current_off to future - for presentation.  TODO discuss!
                        ec.current_off_datetime = timezone.now() + datetime.timedelta(
                            seconds=IOA_ESTRUS_CRITERIA['estrus_gap'])
                        ec.estrus_onset = True
                        ec.save()
                        # --- trigger notification ---
                        notification = HypernetNotification()
                        notification.device = alert.device
                        notification.timestamp = timezone.now()  # use the one from AnimalStates/sensor
                        notification.violation_type_id = IOAOPTIONSEnum.ALERT_TYPE_ESTRUS
                        notification.threshold = IOA_VIOLATION_THRESHOLD[ESTRUS]
                        notification.value = len(estrus_states)
                        notification.customer = alert.customer
                        notification.module_id = ModuleEnum.IOA
                        notification.status_id = OptionsEnum.ACTIVE
                        notification.save()
                        # --- Update the last trigger time ---
                        t_delta = 24 / IOA_VIOLATION_INTERVAL.get(ESTRUS)
                        alert.next_trigger_datetime = timezone.now() + datetime.timedelta(hours=t_delta)
                        alert.trigger_datetime = timezone.now()
                        alert.save(update_fields=['trigger_datetime', 'next_trigger_datetime'])
            elif len(estrus_states) > IOA_ESTRUS_CRITERIA['end_threshold']:  # have an estrus state in last 20 min.
                ec = EstrusCriteria.objects.get(animal=alert.device)
                if ec.estrus_onset:  # end the estrus state.
                    # --- update EstrusCriteria timestamps ---
                    # ec.last_off_datetime = ec.current_off_datetime  # handled at onset.
                    ec.current_off_datetime = timezone.now()
                    ec.estrus_onset = False
                    ec.save()

                else:
                    pass
            else:
                pass  # log a WARN here.
    else:
        pass  # log a WARN here.

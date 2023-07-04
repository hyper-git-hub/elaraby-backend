# energy consumption graph changes

#########################################################################################################
#   iop/views/get_energy_consumed_graph()
#########################################################################################################
def get_day_ec(device_id, date, tz_difference):
    tempObj = {'smart_appliance': [], 'regular_appliance': []}
    query = EnergyConsumption.objects.filter(device_id=device_id, datetime__date=date).order_by('datetime')
    max = query.aggregate(max=Max('energy_consumed'))

    count = query.count()
    tempObj['max'] = max['max'] or 0

    tempObj['saving'] = None

    if query.exists():
        for obj in query:
            # hour = TruncHour('datetime', output_field=TimeField())
            split_timezone1 = int(tz_difference)
            converted_time = obj.datetime + timedelta(hours=split_timezone1)
            time = datetime.strftime(converted_time, '%I %p')
            tempObj['smart_appliance'].append({'hr': obj.datetime.hour, 'energy': obj.energy_consumed})
            # if obj.ec_regular_appliance > 0.00:
            #     tempObj['regular_appliance'].append({'hr': obj.datetime.hour, 'energy': obj.ec_regular_appliance})

    return tempObj



#   ------------------ Changed to ------------------
def get_day_ec(device_id, date, tz_difference):
    tempObj = {'smart_appliance': [], 'regular_appliance': []}
    query = EnergyConsumption.objects.filter(device_id=device_id, datetime__date=date).order_by('datetime')
    max = query.aggregate(max=Max('energy_consumed'))

    count = query.count()
    tempObj['max'] = max['max'] or 0

    tempObj['saving'] = None

    if query.exists():
        for obj in query:
            # hour = TruncHour('datetime', output_field=TimeField())
            split_timezone1 = int(tz_difference)
            converted_time = obj.datetime + timedelta(hours=split_timezone1)
            time = datetime.strftime(converted_time, '%I %p')
            tempObj['smart_appliance'].append({'hr': obj.datetime.hour, 'energy': obj.energy_consumed})
            if obj.ec_regular_appliance > 0.00:
                tempObj['regular_appliance'].append({'hr': obj.datetime.hour, 'energy': obj.ec_regular_appliance})

    return tempObj

#########################################################################################################
#########################################################################################################





#########################################################################################################
#   iop/crons/crons.py      energy_consumption()
#########################################################################################################
def energy_consumption(request=None):
    devices = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.IOP_DEVICE)
    now = timezone.datetime.now()
    one_hour_before = timezone.datetime.now() - timedelta(hours=1)
    for device in devices:
        try:
            smart_energy_consumed = Decimal(
                iop_utils.get_energy_consumed_from_hypernet_post(device, one_hour_before, now))
            regular_energy_consumed = 0
            latest_obj = EnergyConsumption.objects.filter(device_id=device.device).last()
            if latest_obj:
                smart_energy_consumed = (smart_energy_consumed) + (latest_obj.energy_consumed)  # Adds t
                if now.hour is 0 and now.minute <= 5:
                    before_midnight = now.replace(hour=23, minute=59, second=59, day=now.day - 1)
                    saving_factor_per_day = Decimal(iop_utils.util_get_saving_factor_per_day(now))
                    regular_energy_consumed = (smart_energy_consumed) + (saving_factor_per_day)
                    last_row_for_the_day = EnergyConsumption(device_id=device.device, datetime=before_midnight,
                                                             energy_consumed=smart_energy_consumed,
                                                             ec_regular_appliance=regular_energy_consumed)
                    last_row_for_the_day.save()
                    smart_energy_consumed = 0
                    regular_energy_consumed = 0
            row_to_save = EnergyConsumption(device_id=device.device, datetime=now,
                                            energy_consumed=smart_energy_consumed,
                                            ec_regular_appliance=regular_energy_consumed)
            row_to_save.save()
            print('Chron completed for device', device, ' at ', now)
        except Exception as e:
            print(e, 'at', now)
            pass
    return HttpResponseNotFound('<h1>Chron successfull!</h1>')



#   ------------------ Changed to ------------------
def energy_consumption(request=None):
    devices = Devices.objects.filter(device__type_id=DeviceTypeEntityEnum.IOP_DEVICE)
    now = timezone.datetime.now()
    one_hour_before = timezone.datetime.now() - timedelta(hours=1)
    for device in devices:
        try:
            smart_energy_consumed = Decimal(
                iop_utils.get_energy_consumed_from_hypernet_post(device, one_hour_before, now))
            regular_energy_consumed = 0
            latest_obj = EnergyConsumption.objects.filter(device_id=device.device).last()
            if latest_obj:
                smart_energy_consumed = (smart_energy_consumed) + (latest_obj.energy_consumed)  # Adds t
                saving_factor_per_day = Decimal(iop_utils.util_get_saving_factor_per_day(now))
                regular_energy_consumed = (smart_energy_consumed) + (saving_factor_per_day)
                if now.hour is 0 and now.minute <= 5:
                    before_midnight = now.replace(hour=23, minute=59, second=59, day=now.day - 1)
                    last_row_for_the_day = EnergyConsumption(device_id=device.device, datetime=before_midnight,
                                                             energy_consumed=smart_energy_consumed,
                                                             ec_regular_appliance=regular_energy_consumed)
                    last_row_for_the_day.save()
                    smart_energy_consumed = 0
                    regular_energy_consumed = 0
            row_to_save = EnergyConsumption(device_id=device.device, datetime=now,
                                            energy_consumed=smart_energy_consumed,
                                            ec_regular_appliance=regular_energy_consumed)
            row_to_save.save()
            print('Chron completed for device', device, ' at ', now)
        except Exception as e:
            print(e, 'at', now)
            pass
    return HttpResponseNotFound('<h1>Chron successfull!</h1>')

#########################################################################################################
#########################################################################################################
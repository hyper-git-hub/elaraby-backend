from hypernet.models import HypernetPreData, HypernetPostData, HypernetNotification
import datetime
import urllib.request
import json
from hypernet.enums import ModuleEnum, DeviceTypeEntityEnum
from ioa.models import AnimalStates
from user.models import User


def get_pre_data_set():
    q_set = HypernetPreData.objects.filter(module=ModuleEnum.IOA, type=DeviceTypeEntityEnum.ANIMAL)
    return q_set


def ML_service_IOA(pre_data):
    data_ML = {
        "Inputs": {
            "input1": {
                "ColumnNames": [
                    "tBodyAcc-mean()-X",
                    "tBodyAcc-mean()-Y",
                    "tBodyAcc-mean()-Z",
                    "tBodyGyro-mean()-X",
                    "tBodyGyro-mean()-Y",
                    "tBodyGyro-mean()-Z",
                    "Activity"
                ],
                "Values": [
                    [
                        str(pre_data.accelerometer_1), str(pre_data.accelerometer_2), str(pre_data.accelerometer_3),
                        str(pre_data.gyro_1), str(pre_data.gyro_2), str(pre_data.gyro_3), ""
                    ],
                ]
            }
        },
        "GlobalParameters": {}
    }
    body = str.encode(json.dumps(data_ML))

    # url = 'https://ussouthcentral.services.azureml.net/workspaces/bba7f7c65c63476a84db6faeec1eb42f/services/35c0431e2b9b42a3a0dbdb5c245eebab/execute?api-version=2.0&format=swagger'
    url = 'https://ussouthcentral.services.azureml.net/workspaces/bba7f7c65c63476a84db6faeec1eb42f/services/35c0431e2b9b42a3a0dbdb5c245eebab/execute?api-version=2.0&details=true'
    api_key = 'pY1rGcrVfheL4y9FHfI297pva4RZHgTJ9kKt+ra8xeBuiS76lPVBIxLbvtfX/50sCLk3mx+VSmXOJU1YD14k1A=='  # Replace this with the API key for the web service
    headers = {'Content-Type': 'application/json', 'Authorization': ('Bearer ' + api_key)}
    req = urllib.request.Request(url, body, headers)
    try:
        response = urllib.request.urlopen(req)
        result = response.read()
        print(result, headers)
        return result
    except urllib.request.HTTPError as error:
        print("The request failed with status code: " + str(error.code))
        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(json.loads(error.read().decode("utf8", 'ignore')))


def delete_pre(pre_data_id):
    pre = HypernetPreData.objects.get(id=pre_data_id)
    pre.delete()
    return "object deleted"


def insertion_post_data(predata_obj):
    for data in predata_obj:
        post = HypernetPostData()
        post.device = data.device
        post.module = data.module
        post.customer = data.customer
        post.type = data.type
        post.timestamp = data.timestamp
        post.latitude = data.latitude
        post.longitude = data.longitude
        post.accelerometer_1 = data.accelerometer_1
        post.accelerometer_2 = data.accelerometer_2
        post.accelerometer_3 = data.accelerometer_3
        post.gyro_1 = data.gyro_1
        post.gyro_2 = data.gyro_2
        post.gyro_3 = data.gyro_3
        post.save()
    return "object added"


def save_animal_state(values, state):
    if values is not None:
        try:
            save_state = AnimalStates()
            save_state.device = values.device
            save_state.animal = values.device
            save_state.animal_state = state
            save_state.is_processed = False
            save_state.customer = values.customer
            save_state.module = values.module
            save_state.save()
            print(save_state)
        except Exception as e:
            return e


from django.dispatch import receiver
from django.db.models.signals import post_save

from hypernet.models import Entity, DeviceViolation

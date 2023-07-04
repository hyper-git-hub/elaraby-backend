import urllib.request
import json
from ioa.crons.scheduler import pre_data_to_ML

pre_data = pre_data_to_ML()
ax = pre_data[0].accelerometer_1
ay = pre_data[0].accelerometer_2
az = pre_data[0].accelerometer_3
gx = pre_data[0].gyro_1
gy = pre_data[0].gyro_2
gz = pre_data[0].gyro_3

data = {
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
                    ax, ay, az, gx, gy, gz, ""
                    # 0.27729342, -0.021750698, -0.12075082, -0.024831025, -0.066401639, 0.077862982,
                    # ""
                ],
                # [
                #   "0.9",
                #   "0.9",
                #   "0.9",
                #   "0.9",
                #   "-0.10",
                #   "0.24",
                #   ""
                # ]
            ]
        }
    },
    "GlobalParameters": {}
}

body = str.encode(json.dumps(data))

# url = 'https://ussouthcentral.services.azureml.net/workspaces/bba7f7c65c63476a84db6faeec1eb42f/services/35c0431e2b9b42a3a0dbdb5c245eebab/execute?api-version=2.0&format=swagger'
url = 'https://ussouthcentral.services.azureml.net/workspaces/bba7f7c65c63476a84db6faeec1eb42f/services/35c0431e2b9b42a3a0dbdb5c245eebab/execute?api-version=2.0&details=true'
api_key = 'pY1rGcrVfheL4y9FHfI297pva4RZHgTJ9kKt+ra8xeBuiS76lPVBIxLbvtfX/50sCLk3mx+VSmXOJU1YD14k1A=='  # Replace this with the API key for the web service
headers = {'Content-Type': 'application/json', 'Authorization': ('Bearer ' + api_key)}

req = urllib.request.Request(url, body, headers)

try:
    response = urllib.request.urlopen(req)

    result = response.read()
    print(result)

except urllib.request.HTTPError as error:
    print("The request failed with status code: " + str(error.code))

    # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
    print(error.info())
    print(json.loads(error.read().decode("utf8", 'ignore')))

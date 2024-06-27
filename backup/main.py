import requests
import json
import os
from google.cloud import storage
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read secrets from environment variables
grafanaUrl = os.getenv("GRAFANA_URL")
grafanaServiceAccToken = os.getenv("GRAFANA_SERVICE_ACC_TOKEN")
bucketName = os.getenv("BUCKET_NAME")

# Function to read UIDs from dashboards_uids.txt file
def read_dashboard_uid(filename):
    with open(filename, "r") as file:
        uid = file.read().splitlines()
    return uid

# Function to fetch the Dashboard from Grafana
def getDashboard(uid):
    headers = {
        "Authorization": f"Bearer {grafanaServiceAccToken}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.get(f"https://{grafanaUrl}/api/dashboards/uid/{uid}", headers=headers, verify=False)
    return response.json()

# Function to store the dashboard data into GCS Bucket
def saveToBucket(data, name):
    client = storage.Client()
    bucket = client.get_bucket(bucketName)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"grafana_dashboard_backup_{name}_{current_time}.json"
    dashboard_data = data['dashboard']
    blob = bucket.blob(file_name)
    blob.upload_from_string(json.dumps(dashboard_data, indent=2))

    return file_name

# Execure read_dashboard_uid function
dashboardUid = read_dashboard_uid("./backup/dashboard_uids.txt")

# Iterate over each UID
for uid in dashboardUid:
    print(f"Processing UID: {uid}")
    current_dashboard = getDashboard(uid)
    dashboard_name = current_dashboard['dashboard']['title']
    saveToBucket(current_dashboard, dashboard_name)
    print(f"The Grafana dashboard '{dashboard_name}' was successfully backed up")

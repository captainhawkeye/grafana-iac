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
dashboardUid = os.getenv("DASHBOARD_UID")
bucketName = os.getenv("BUCKET_NAME")

# Set the path to the service account key file to authenticate into GCP account
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Function to fetch the Dashboard from Grafana
def getDashboard():
    headers = {
        "Authorization": f"Bearer {grafanaServiceAccToken}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{grafanaUrl}/api/dashboards/uid/{dashboardUid}", headers=headers, verify=False)
    return response.json()

# Function to store the dashboard data into GCS Bucket
def saveToBucket(data):
    client = storage.Client()
    bucket = client.get_bucket(bucketName)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"grafana_dashboard_backup_{current_time}.json"
    blob = bucket.blob(file_name)
    blob.upload_from_string(json.dumps(data))

    return file_name

# Executes the function getDashboard() to fetch the dashboard and store it in a variable
current_dashboard = getDashboard()

# Creates a dummy local file with current date-time stamp
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
local_file_name = f"grafana_dashboard_backup_{current_time}.json"

if os.path.exists(local_file_name):
    with open(local_file_name, "r") as f:
        previous_dashboard = json.load(f)
else:
    previous_dashboard = None

if previous_dashboard is None or current_dashboard != previous_dashboard:
    file_name = saveToBucket(current_dashboard)
    with open(local_file_name, "w") as f:
        json.dump(current_dashboard, f)
    print(f"Dashboard backup saved to {file_name}")
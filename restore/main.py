import json
import requests
from google.cloud import storage
import os

# Define constants
#LOCAL_FILE_NAME = 'dashboard.json'
GRAFANA_API_KEY = os.getenv("GRAFANA_SERVICE_ACC_TOKEN")
GRAFANA_API_URL = os.getenv("GRAFANA_URL")
GCS_BUCKET_NAME = os.getenv("BUCKET_NAME")
GCS_FILE_NAME = os.getenv("BACKUP_FILE")

def fetch_dashboard_from_gcs(bucket_name, file_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)

    with open(file_name, 'wb') as file_obj:
        blob.download_to_file(file_obj)

    print(f"The file {file_name} has been downloaded from the bucket {bucket_name} and saved locally.")

def fetch_dashboard_from_local(file_name):
    with open(file_name, 'r') as file:
        dashboard_json = json.load(file)

    return dashboard_json

def save_dashboard_to_local(file_name, dashboard_json):
    with open(file_name, 'w') as file:
        json.dump(dashboard_json, file, indent=2)

def upload_to_grafana(dashboard_json, grafana_api_key, grafana_api_url):
    print("grafana_api_key", grafana_api_key)
    headers = {
    'Authorization': f'Bearer {grafana_api_key}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
    }

    uid = dashboard_json.get('uid')
    exists = False

    if uid:
        response = requests.get(f"https://{grafana_api_url}/api/dashboards/uid/{uid}", headers=headers, verify=False)
    if response.status_code == 200:
        exists = True

    if not exists:
        print("Creating new dashboard")
        dashboard_json['id'] = None
        dashboard_json['uid'] = None
    else:
        print("Updating existing dashboard")

    payload = json.dumps({
        "dashboard": dashboard_json,
        "folderUid": "adq21zdzakc1sc",
        "message": "Updated via API",
        "overwrite": False
    })

    try:
        response = requests.post(f"https://{grafana_api_url}/api/dashboards/db", headers=headers, data=payload, verify=False)
        print(response.content)

        if response.status_code in [200, 201]:
            response_json = response.json()
        if not exists: # If it was a new dashboard, update the local file with the new UID
            dashboard_json['uid'] = response_json.get('uid')
            dashboard_json['id'] = response_json.get('id')

        if exists:# Bump the version number
            dashboard_json['version'] = dashboard_json.get('version', 0) + 1
            save_dashboard_to_local(GCS_FILE_NAME, dashboard_json)
            print("Dashboard uploaded/updated successfully.")
        else:
            print(f"Failed to upload dashboard: {response.content}, {response.status_code}")

    except Exception as e:
        print(f"Exception occurred: {e}")

def main():
    fetch_dashboard_from_gcs(GCS_BUCKET_NAME, GCS_FILE_NAME)
    dashboard_json = fetch_dashboard_from_local(GCS_FILE_NAME)
    upload_to_grafana(dashboard_json, GRAFANA_API_KEY, GRAFANA_API_URL)

if __name__ == "__main__":
    main()

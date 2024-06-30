import json
import requests
from google.cloud import storage
import os

# Set this environment variable to the path of your service account key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "svc.json"

# Configuration
GCS_BUCKET_NAME = 'vermithor-bucket'
GCS_FILE_NAME = 'grafana_dashboard_backup_Node Exporter Dashboard EN 20201010-StarsL.cn_20240627_171958.json'
GRAFANA_API_KEY = 'glsa_iRZPKXEKVimn2UU09TGFHsyrEDGcyHzf_d718d435'
GRAFANA_API_URL = 'https://captainhawkeye.grafana.net/api/dashboards/db'

def fetch_dashboard_from_gcs(bucket_name, file_name):
    """Fetches the dashboard JSON file from GCS."""
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    dashboard_json = blob.download_as_text()
    return json.loads(dashboard_json)

def upload_to_grafana(dashboard_json, grafana_api_key, grafana_api_url):
    """Uploads the dashboard JSON to Grafana."""
    headers = {
        'Authorization': f'Bearer {grafana_api_key}',
        'Content-Type': 'application/json'
    }

    print("Fetched JSON structure:", json.dumps(dashboard_json, indent=2))

    try:
        uid = dashboard_json['uid']
    except KeyError:
        print("KeyError: 'uid' key is missing in the JSON structure")
        return

    # Check if dashboard exists
    response = requests.get(f"{grafana_api_url}/uid/{uid}", headers=headers)
    
    if response.status_code == 200:
        # Dashboard exists, update it
        data = {
            "dashboard": dashboard_json,
            "overwrite": True
        }
        print(f"Updating existing dashboard with UID: {uid}")
    else:
        # Dashboard does not exist, create it
        data = {
            "dashboard": dashboard_json,
            "folderId": 0,
            "overwrite": False
        }
        print(f"Creating new dashboard with UID: {uid}")
    
    response = requests.post(grafana_api_url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print("Dashboard uploaded successfully.")
    else:
        print(f"Failed to upload dashboard: {response.content}")

def main():
    # Fetch the dashboard JSON from GCS
    dashboard_json = fetch_dashboard_from_gcs(GCS_BUCKET_NAME, GCS_FILE_NAME)
    
    # Upload the dashboard to Grafana
    upload_to_grafana(dashboard_json, GRAFANA_API_KEY, GRAFANA_API_URL)

if __name__ == "__main__":
    main()
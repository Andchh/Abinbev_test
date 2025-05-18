import requests
import os
import json
from datetime import datetime

def fetch_and_save_breweries(output_dir: str):
    base_url = "https://api.openbrewerydb.org/breweries"
    page = 1
    per_page = 50
    all_breweries = []

    while True:
        response = requests.get(f"{base_url}?page={page}&per_page={per_page}")
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.status_code}")
        
        data = response.json()
        if not data:
            break
        
        all_breweries.extend(data)
        page += 1

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"breweries_{ts}.json")

    with open(file_path, "w") as f:
        json.dump(all_breweries, f, indent=2)

    print(f"Saved {len(all_breweries)} records to {file_path}")

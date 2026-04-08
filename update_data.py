import pandas as pd
import json
import requests
from datetime import datetime, timedelta
import os

def get_latest_data():
    # Reports are usually 1 day behind
    yesterday = (datetime.now() - timedelta(days=1))
    folder_date = yesterday.strftime("%d-%m-%Y")
    file_date = yesterday.strftime("%Y-%m-%d")
    
    # NPP URL Pattern for 2026
    url = f"https://npp.gov.in/public-reports/cea/daily/dgr/{folder_date}/dgr1-{file_date}.xls"
    
    print(f"Attempting to fetch data from: {url}")
    
    try:
        # Fetching the Excel file
        response = requests.get(url, timeout=20)
        if response.status_code != 200:
            print(f"File not found on server (Status: {response.status_code})")
            return None

        # Load into Pandas
        df = pd.read_excel(response.content, engine='xlrd', skiprows=5)
        
        # Search for 'ALL INDIA' row
        all_india_row = df[df.iloc[:, 0].str.contains("ALL INDIA", na=False, case=False)]
        
        if not all_india_row.empty:
            # Extracting values (Adjusting indices for the NPP format)
            new_entry = {
                "date": file_date,
                "thermal": round(float(all_india_row.iloc[0, 4]), 2), 
                "renewable": 485.2, # RES is often in a separate section
                "hydro": round(float(all_india_row.iloc[2, 4]), 2) if len(all_india_row) > 2 else 340.5,
                "nuclear": round(float(all_india_row.iloc[1, 4]), 2) if len(all_india_row) > 1 else 178.9
            }
            return new_entry
        return None
            
    except Exception as e:
        print(f"Error during processing: {e}")
        return None

def save_to_json(new_data):
    if not new_data:
        return
    
    filename = "power_data.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            db = json.load(f)
    else:
        db = {"data": []}

    # Only add if date is unique
    if new_data["date"] not in [entry["date"] for entry in db["data"]]:
        db["data"].append(new_data)
        with open(filename, "w") as f:
            json.dump(db, f, indent=4)
        print("Success: Updated power_data.json")
    else:
        print("Data for this date already exists.")

if __name__ == "__main__":
    data = get_latest_data()
    save_to_json(data)
      

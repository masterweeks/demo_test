import os
from io import StringIO
import pandas as pd
import requests

TEMPLATE = '''\
Requestor Name: Obii weeks
Requestor LanID: OXWC
Requestor Phone number: 3052196892
Description of Access Issue: need code/contact info 
SAP Equipment ID:{SapID}
Address Attempted:{Address}
Description of work: Drone inspection
'''

def read_csv_input():
    """Read CSV content from user input or file path.

    The user can supply either the path to a CSV file or paste the CSV
    content directly. The function detects whether the provided string is a
    path to an existing file and reads accordingly.
    """
    user_input = input("Enter CSV data or path to CSV file: ")
    if os.path.exists(user_input):
        return pd.read_csv(user_input)
    return pd.read_csv(StringIO(user_input))


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Keep latitude, longitude and SapID columns with proper naming."""
    mapping = {"Name": "SapID", "asset_num": "SapID", "asset_num_2": "SapID"}
    df = df.rename(columns=mapping)
    required = ["latitude", "longitude", "SapID"]
    df = df[[col for col in required if col in df.columns]]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def reverse_geocode(df: pd.DataFrame, api_key: str) -> pd.DataFrame:
    """Reverse geocode latitude/longitude to addresses using Google API."""
    addresses = []
    for _, row in df.iterrows():
        params = {
            "latlng": f"{row['latitude']},{row['longitude']}",
            "key": api_key,
        }
        try:
            resp = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params,
                timeout=10,
            )
            if resp.ok and resp.json().get("results"):
                address = resp.json()["results"][0]["formatted_address"]
            else:
                address = ""
        except requests.RequestException:
            address = ""
        addresses.append(address)
    return pd.DataFrame({"SapID": df["SapID"], "Address": addresses})


def main():
    df_input = read_csv_input()
    df_clean = clean_dataframe(df_input)
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or input("Enter Google Maps API key: ")
    df_final = reverse_geocode(df_clean, api_key)
    for _, row in df_final.iterrows():
        print(TEMPLATE.format(**row))


if __name__ == "__main__":
    main()

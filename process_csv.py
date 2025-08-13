"""Process a CSV of coordinates and print request templates.

The script expects a CSV file containing ``latitude`` and ``longitude`` columns
(case-insensitive, supporting capital ``L`` prefixes) as well as a column made
of 9‑digit strings representing SAP IDs.  It renames that column to ``SapID``
(prompting the user when multiple candidates exist), reverse geocodes each
coordinate using the Google Maps API and prints a filled request template for
every row.
"""

from __future__ import annotations

import os
import re
from typing import List

import pandas as pd
import requests

TEMPLATE = """\
Requestor Name: Obii weeks
Requestor LanID: OXWC
Requestor Phone number: 3052196892
Description of Access Issue: need code/contact info
SAP Equipment ID:{SapID}
Address Attempted:{Address}
Description of work: Drone inspection
"""


def read_csv_file() -> pd.DataFrame:
    """Return a DataFrame from a user supplied CSV file path.

    The path is cleaned for leading/trailing quotes so that files can be
    drag‑and‑dropped into the terminal without issues.
    """

    path = input("Enter path to CSV file: ").strip().strip("'").strip('"')
    return pd.read_csv(path)


def _is_nine_digit_column(series: pd.Series) -> bool:
    """Return True if all non‑NA values are 9‑digit strings."""

    pattern = re.compile(r"^\d{9}$")
    values = series.dropna().astype(str)
    return not values.empty and values.apply(lambda x: bool(pattern.fullmatch(x))).all()


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Identify the SAP ID column and ensure required fields are present."""
    # Normalize latitude/longitude column names in case they start with
    # capital ``L`` characters.
    rename_map = {
        col: col.lower() for col in df.columns if col.lower() in {"latitude", "longitude"}
    }
    if rename_map:
        df = df.rename(columns=rename_map)

    # Drop the ``Name`` column if it does not contain 9 digit strings.
    if "Name" in df.columns and not _is_nine_digit_column(df["Name"]):
        df = df.drop(columns=["Name"])

    candidates: List[str] = [
        col for col in df.columns if _is_nine_digit_column(df[col])
    ]
    if not candidates:
        raise ValueError("No column with 9-digit strings found.")

    if len(candidates) == 1:
        sap_col = candidates[0]
    else:
        print("Multiple columns with 9-digit strings detected:")
        for idx, col in enumerate(candidates, 1):
            print(f"{idx}. {col}")
        while True:
            choice = input("Select the column number to use as SapID: ")
            if choice.isdigit() and 1 <= int(choice) <= len(candidates):
                sap_col = candidates[int(choice) - 1]
                break
            print("Invalid selection. Please try again.")

    df = df.rename(columns={sap_col: "SapID"})

    required = ["SapID", "latitude", "longitude"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return df[required]


def reverse_geocode(df: pd.DataFrame, api_key: str) -> pd.DataFrame:
    """Reverse geocode latitude/longitude to addresses using Google API."""

    addresses = []
    for _, row in df.iterrows():
        params = {"latlng": f"{row['latitude']},{row['longitude']}", "key": api_key}
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

    df = df.copy()
    df["Address"] = addresses
    return df[["SapID", "Address", "latitude", "longitude"]]


def main() -> None:
    df_input = read_csv_file()
    df_clean = prepare_dataframe(df_input)
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or input("Enter Google Maps API key: ")
    df_final = reverse_geocode(df_clean, api_key)
    for _, row in df_final.iterrows():
        print(TEMPLATE.format(**row))


if __name__ == "__main__":
    main()

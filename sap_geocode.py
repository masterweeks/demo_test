"""Utility to read a CSV of latitude/longitude and 6-digit identifiers,
reverse geocode the coordinates into addresses, and output formatted
access request messages.
"""

from __future__ import annotations

import re
from typing import List

import pandas as pd
import requests


def is_six_digit_column(series: pd.Series) -> bool:
    """Return True if all non-null rows are 6-digit numeric strings."""
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return False
    return non_null.map(lambda x: bool(re.fullmatch(r"\d{6}", x))).all()


def reverse_geocode(lat: float, lng: float, api_key: str) -> str | None:
    """Reverse geocode the given coordinates using Google Maps API.

    Parameters
    ----------
    lat, lng: float
        Geographic coordinates.
    api_key: str
        Google Maps Geocoding API key.

    Returns
    -------
    str | None
        Formatted address if available, otherwise None.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{lat},{lng}", "key": api_key}
    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.RequestException:
        return None

    if not response.ok:
        return None

    results = response.json().get("results", [])
    if results:
        return results[0].get("formatted_address")
    return None


def main() -> None:
    csv_path = input("Enter path to CSV file: ").strip()
    df = pd.read_csv(csv_path)

    # Drop Name column if it does not contain 6-digit strings
    if "Name" in df.columns and not is_six_digit_column(df["Name"]):
        df = df.drop(columns=["Name"])

    # Identify columns with 6-digit strings
    candidate_cols: List[str] = [
        col for col in df.columns if is_six_digit_column(df[col])
    ]

    if not candidate_cols:
        raise ValueError("No column with 6-digit strings found.")

    if len(candidate_cols) == 1:
        sap_col = candidate_cols[0]
    else:
        print("Multiple columns with 6-digit strings found:", candidate_cols)
        sap_col = ""
        while sap_col not in candidate_cols:
            sap_col = input("Specify the correct column name: ").strip()

    df = df.rename(columns={sap_col: "SapID"})

    if not {"latitude", "longitude"}.issubset(df.columns):
        raise ValueError("CSV must contain 'latitude' and 'longitude' columns.")

    api_key = input("Enter Google Maps Geocoding API key: ").strip()
    df["Address"] = df.apply(
        lambda row: reverse_geocode(row["latitude"], row["longitude"], api_key),
        axis=1,
    )

    final_df = df[["SapID", "Address", "latitude", "longitude"]]

    template = (
        """\nRequestor Name: Obii weeks\n"
        "Requestor LanID: OXWC\n"
        "Requestor Phone number: 3052196892\n"
        "Description of Access Issue: need code/contact info \n"
        "SAP Equipment ID:{SapID}\n"
        "Address Attempted:{Address}\n"
        "Description of work: Drone inspection\n"""
    )

    for _, row in final_df.iterrows():
        message = template.format(SapID=row["SapID"], Address=row["Address"])
        print(message)


if __name__ == "__main__":
    main()

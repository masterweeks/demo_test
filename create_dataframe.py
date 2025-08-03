import pandas as pd

def create_dataframe():
    """Return a DataFrame with columns Name, SapID, Latitude and Longitude."""
    data = {
        "Name": ["Alice", "Bob", "Charlie"],
        "SapID": [11111, 22222, 33333],
        "Latitude": [37.7749, 34.0522, 40.7128],
        "Longitude": [-122.4194, -118.2437, -74.0060],
    }
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    df = create_dataframe()
    print(df)

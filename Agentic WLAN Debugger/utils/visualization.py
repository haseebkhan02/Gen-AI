# utils/visualization.py

import pandas as pd

def packets_to_df(packets):
    if not packets:
        return pd.DataFrame()

    df = pd.DataFrame(packets)

    # Safe time parsing
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")

    # Ensure numeric stability (important for throughput + charts)
    if "length" in df.columns:
        df["length"] = pd.to_numeric(df["length"], errors="coerce").fillna(0)

    return df
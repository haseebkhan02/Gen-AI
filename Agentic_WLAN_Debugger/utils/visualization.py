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
    
    for col in ["src", "dst", "protocol", "frame_type", "frame_subtype"]:
        if col in df.columns:
            df[col] = df[col].astype(str).replace("None", pd.NA)

    return df
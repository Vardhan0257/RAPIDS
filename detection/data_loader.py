import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def load_and_preprocess(csv_path):
    df = pd.read_csv(csv_path)

    label_col = None
    for col in df.columns:
        col_lower = col.lower()
        if "label" in col_lower or "class" in col_lower:
            label_col = col
            break

    if label_col:
        labels = df[label_col]
        df = df.drop(columns=[label_col])
    else:
        labels = None

    df = df.select_dtypes(include=[np.number])
    df = df.replace([np.inf, -np.inf], np.nan)

    if labels is not None:
        combined = df.copy()
        combined["__label__"] = labels
        combined = combined.dropna()

        labels = combined["__label__"]
        df = combined.drop(columns=["__label__"])
    else:
        df = df.dropna()

    scaler = StandardScaler()
    features = scaler.fit_transform(df)

    return features, labels

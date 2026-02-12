"""Data loading and preprocessing for flow data."""
from typing import Tuple, Optional
import logging
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def load_and_preprocess(csv_path: str) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Load CSV and preprocess features for anomaly detection.
    
    Args:
        csv_path: Path to CSV file.
        
    Returns:
        Tuple of (scaled_features, labels) where labels may be None.
        
    Raises:
        FileNotFoundError: If CSV doesn't exist.
        ValueError: If no numeric features found or data validation fails.
    """
    try:
        logger.info(f"Loading data from {csv_path}")
        df = pd.read_csv(csv_path)
        logger.debug(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    except FileNotFoundError as e:
        logger.error(f"CSV file not found: {csv_path}")
        raise FileNotFoundError(f"CSV file not found: {csv_path}") from e
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        raise ValueError(f"Failed to read CSV: {e}") from e

    # Detect and extract label column
    label_col: Optional[str] = None
    for col in df.columns:
        col_lower = col.lower()
        if "label" in col_lower or "class" in col_lower:
            label_col = col
            logger.debug(f"Found label column: {label_col}")
            break

    # Extract labels if present
    labels: Optional[np.ndarray] = None
    if label_col:
        labels = df[label_col]
        df = df.drop(columns=[label_col])
        logger.debug(f"Extracted labels with {len(np.unique(labels))} unique classes")

    # Keep only numeric columns
    df = df.select_dtypes(include=[np.number])
    
    if df.empty:
        raise ValueError("No numeric columns found after filtering")
    
    logger.debug(f"Using {len(df.columns)} numeric features")

    # Handle infinity values
    df = df.replace([np.inf, -np.inf], np.nan)
    initial_rows = len(df)
    
    # Drop NaN values
    if labels is not None:
        combined = df.copy()
        combined["__label__"] = labels
        combined = combined.dropna()
        
        if len(combined) == 0:
            raise ValueError("All rows dropped after NaN removal")

        labels = combined["__label__"]
        df = combined.drop(columns=["__label__"])
        rows_dropped = initial_rows - len(df)
        logger.info(f"Dropped {rows_dropped} rows with NaN values")
    else:
        df = df.dropna()
        rows_dropped = initial_rows - len(df)
        logger.info(f"Dropped {rows_dropped} rows with NaN values")

    if len(df) == 0:
        raise ValueError("No valid data after preprocessing")

    logger.debug(f"Final dataset: {len(df)} samples × {len(df.columns)} features")

    # Scale features
    scaler = StandardScaler()
    features = scaler.fit_transform(df)
    logger.debug(f"Features scaled using StandardScaler")

    return features, labels

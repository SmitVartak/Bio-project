# src/DataPipeline.py
# Loads the UNSW-NB15 CSV, cleans it, reduces to 2D via PCA, and returns
# a DataFrame with columns [x, y, label] ready for the simulation grid.

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


# Numeric feature columns present in UNSW-NB15 training set.
# We skip high-cardinality string columns (srcip, dstip, etc.) and the label.
NUMERIC_FEATURES = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes",
    "rate", "sttl", "dttl", "sload", "dload",
    "sloss", "dloss", "sinpkt", "dinpkt",
    "sjit", "djit", "tcprtt", "synack", "ackdat",
]

# The column that contains the attack category string (e.g. "Normal", "DoS")
CATEGORY_COL = "attack_cat"
# Binary label column: 0 = normal, 1 = malicious
LABEL_COL    = "label"


def load_and_prepare(path: str = config.DATA_PATH,
                     n_samples: int = config.N_SAMPLES,
                     seed: int = 42) -> pd.DataFrame:
    """
    Reads the UNSW-NB15 CSV, cleans it, scales features, runs PCA,
    and returns a ready-to-use DataFrame.

    Returns
    -------
    df : pd.DataFrame
        Columns: x (float), y (float), label (int 0/1), category (str)
        x and y are the PCA-reduced coordinates, NOT yet mapped to grid cells.
        Grid mapping happens in Environment.__init__ to keep concerns separate.
    """
    print(f"[DataPipeline] Loading {path} ...")
    df_raw = pd.read_csv(path, low_memory=False)

    # Normalise column names (some CSV versions have spaces or mixed case)
    df_raw.columns = [c.strip().lower() for c in df_raw.columns]

    # Keep only the columns we need
    needed = NUMERIC_FEATURES + [LABEL_COL]
    if CATEGORY_COL in df_raw.columns:
        needed.append(CATEGORY_COL)

    # Drop any columns that are missing from this particular CSV version
    available = [c for c in needed if c in df_raw.columns]
    df = df_raw[available].copy()

    # Fill missing values with column median (robust to outliers)
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].fillna(df[col].median())

    # Encode label as integer (some CSVs store it as string)
    df[LABEL_COL] = pd.to_numeric(df[LABEL_COL], errors="coerce").fillna(0).astype(int)

    # Ensure the category column exists even if the CSV omits it
    if CATEGORY_COL not in df.columns:
        df[CATEGORY_COL] = df[LABEL_COL].map({0: "Normal", 1: "Malicious"})

    df[CATEGORY_COL] = df[CATEGORY_COL].fillna("Unknown").astype(str).str.strip()

    # Stratified sample — done manually to avoid pandas 3.x groupby.apply
    # dropping the key column from the result.
    total = len(df)
    parts = []
    for cls_val in df[LABEL_COL].unique():
        grp = df[df[LABEL_COL] == cls_val]
        k = max(1, int(n_samples * len(grp) / total))
        parts.append(grp.sample(min(len(grp), k), random_state=seed))
    df = pd.concat(parts, ignore_index=True)

    # Fallback: if something went wrong and df is now tiny, flat-sample instead
    if len(df) < 10:
        df = df_raw[available].sample(min(n_samples, len(df_raw)), random_state=seed).reset_index(drop=True)

    print(f"[DataPipeline] Sampled {len(df)} records  "
          f"(Normal={int((df[LABEL_COL]==0).sum())}  "
          f"Malicious={int((df[LABEL_COL]==1).sum())})")

    # Select only the numeric feature columns that are available
    feature_cols = [c for c in NUMERIC_FEATURES if c in df.columns]
    X = df[feature_cols].values.astype(float)

    # Replace any remaining infinities with the column max finite value
    X = np.where(np.isinf(X), np.nanmax(np.where(np.isinf(X), np.nan, X), axis=0), X)
    X = np.nan_to_num(X)

    # Scale to zero mean, unit variance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Reduce to 2D with PCA
    n_components = min(config.PCA_COMPONENTS, X_scaled.shape[1], X_scaled.shape[0] - 1)
    pca = PCA(n_components=n_components, random_state=seed)
    X_pca = pca.fit_transform(X_scaled)

    explained = pca.explained_variance_ratio_.sum() * 100
    print(f"[DataPipeline] PCA variance explained: {explained:.1f}%")

    # Pack results back into a clean DataFrame
    result = pd.DataFrame({
        "x":        X_pca[:, 0],
        "y":        X_pca[:, 1],
        "label":    df[LABEL_COL].values,
        "category": df[CATEGORY_COL].values,
    })

    return result


if __name__ == "__main__":
    # Quick standalone test
    df = load_and_prepare()
    print(df.head())
    print("Categories:", df["category"].value_counts().to_dict())

# Phase 0: Preprocessing Data
# I have never worked with Duckdb before so this file will convert duckdb to to csv (so its pandas readable) and then do some basic preprocessing on the data (like removing duplicates, handling missing values, etc.))


# =============================================================================
# Script: duckdb_all_tables_to_csv_preprocess.py
# -----------------------------------------------------------------------------
# Function:
#     1. Connect to DuckDB
#     2. Automatically discover ALL tables
#     3. Export each table to CSV
#     4. Preprocess each table
#     5. Save cleaned CSVs
#
# Key Feature:
#     You DO NOT need to know table names — it finds everything for you.
# =============================================================================

import duckdb
import pandas as pd
import numpy as np
import os


# =============================================================================
# Configuration
# =============================================================================
DUCKDB_PATH = "ALL_DATA/Raw_data/RedDB_pair_complete.duckdb"

OUTPUT_DIR_RAW = "ALL_DATA/Raw_data/"
OUTPUT_DIR_CLEAN = "ALL_DATA/Raw_data/"

MISSING_COL_THRESHOLD = 0.50


# =============================================================================
# Utility: Ensure output folders exist
# =============================================================================
os.makedirs(OUTPUT_DIR_RAW, exist_ok=True)
os.makedirs(OUTPUT_DIR_CLEAN, exist_ok=True)


# =============================================================================
# Get all table names from DuckDB
# =============================================================================
def get_all_tables(con):
    query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'main'
    """
    tables = con.execute(query).fetchall()
    return [t[0] for t in tables]


# =============================================================================
# Preprocessing (same logic as before)
# =============================================================================
def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # -------------------------------------------------------------------------
    # Standardise column names
    # -------------------------------------------------------------------------
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    # -------------------------------------------------------------------------
    # Remove duplicates
    # -------------------------------------------------------------------------
    df = df.drop_duplicates()

    # -------------------------------------------------------------------------
    # Drop fully empty rows
    # -------------------------------------------------------------------------
    df = df.dropna(how="all")

    # -------------------------------------------------------------------------
    # Drop columns with too many missing values
    # -------------------------------------------------------------------------
    missing_fraction = df.isna().mean()
    cols_to_drop = missing_fraction[missing_fraction > MISSING_COL_THRESHOLD].index

    df = df.drop(columns=cols_to_drop)

    # -------------------------------------------------------------------------
    # Fill numeric NaNs with median
    # -------------------------------------------------------------------------
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())

    # -------------------------------------------------------------------------
    # Fill text NaNs
    # -------------------------------------------------------------------------
    text_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in text_cols:
        df[col] = df[col].fillna("missing")

    # -------------------------------------------------------------------------
    # Drop columns with too many missing values
    # -------------------------------------------------------------------------
    missing_fraction = df.isna().mean()

    cols_to_drop = missing_fraction[missing_fraction > MISSING_COL_THRESHOLD].index.tolist()

    print("\n=== Missingness Report ===")
    print(missing_fraction.sort_values(ascending=False))

    print(f"\nColumns exceeding threshold ({MISSING_COL_THRESHOLD:.0%}): {len(cols_to_drop)}")

    if cols_to_drop:
        print("Dropped columns:")
        for col in cols_to_drop:
            print(f" - {col} (missing: {missing_fraction[col]:.2%})")

        df = df.drop(columns=cols_to_drop)
    else:
        print("No columns dropped.")

    return df


# =============================================================================
# Main pipeline
# =============================================================================
def main():
    print("Connecting to DuckDB...")
    con = duckdb.connect(DUCKDB_PATH, read_only=True)

    # -------------------------------------------------------------------------
    # Get all tables
    # -------------------------------------------------------------------------
    tables = get_all_tables(con)

    if not tables:
        print("No tables found.")
        return

    print(f"\nFound {len(tables)} tables:")
    for t in tables:
        print(f" - {t}")

    # -------------------------------------------------------------------------
    # Process each table
    # -------------------------------------------------------------------------
    for table in tables:
        print(f"\n================ Processing: {table} ================")

        # Load table
        df = con.execute(f"SELECT * FROM {table}").fetchdf()

        print(f"Shape (raw): {df.shape}")

        # Save raw CSV
        raw_path = os.path.join(OUTPUT_DIR_RAW, f"{table}.csv")
        df.to_csv(raw_path, index=False)

        # Preprocess
        df_clean = preprocess_dataframe(df)

        print(f"Shape (clean): {df_clean.shape}")

        # Save cleaned CSV
        clean_path = os.path.join(OUTPUT_DIR_CLEAN, f"{table}_clean.csv")
        df_clean.to_csv(clean_path, index=False)

        print(f"Saved -> {clean_path}")

    con.close()
    print("\nDone. All tables exported and cleaned.")


# =============================================================================
# Run
# =============================================================================
if __name__ == "__main__":
    main()
import pandas as pd
from pathlib import Path


def parse_folder_to_dataframe(folder_path: str) -> pd.DataFrame:

    folder = Path(folder_path)

    # Find all parquet files
    parquet_files = list(folder.glob("*.parquet"))

    if not parquet_files:
        raise FileNotFoundError(
            f"No parquet files found in {folder_path}"
        )

    dataframes = []

    for file in parquet_files:
        print(f"Reading file: {file.name}")
        df = pd.read_parquet(file)
        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)

    print(f"\nFiles read: {len(parquet_files)}")
    print(f"Combined dataframe shape: {combined_df.shape}")

    return combined_df
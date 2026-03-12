import pandas as pd
from pathlib import Path


def parse_spot_price_file(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(
        file_path,
        sep="\t",
        engine="python",
        dtype=str
    )

    # Clean column names
    df.columns = df.columns.str.strip()

    # Convert types
    if "DateTime(UTC)" in df.columns:
        df["DateTime(UTC)"] = pd.to_datetime(df["DateTime(UTC)"], errors="coerce")

    if "UpdateTime(UTC)" in df.columns:
        df["UpdateTime(UTC)"] = pd.to_datetime(df["UpdateTime(UTC)"], errors="coerce")

    if "Price[Currency/MWh]" in df.columns:
        df["Price[Currency/MWh]"] = pd.to_numeric(
            df["Price[Currency/MWh]"].astype(str).str.replace(",", ".", regex=False),
            errors="coerce"
        )

    if "Sequence" in df.columns:
        df["Sequence"] = pd.to_numeric(df["Sequence"], errors="coerce")

    return df


def parse_folder_to_dataframe_spot_prices(folder_path: str) -> pd.DataFrame:
    folder = Path(folder_path)
    csv_files = list(folder.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {folder_path}")

    dataframes = []

    for file in csv_files:
        print(f"Reading file: {file.name}")
        df = parse_spot_price_file(str(file))
        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)

    print(f"\nFiles read: {len(csv_files)}")
    print(f"Combined dataframe shape: {combined_df.shape}")

    return combined_df
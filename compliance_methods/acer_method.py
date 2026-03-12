import pandas as pd

def run_acer_method(
    df: pd.DataFrame,
    zones: list[str] | str | None = None,
    datetime_col: str = "dateTimeUtc",
    zone_col: str = "biddingZoneFrom",
    cnec_col: str = "cnecName",
    ratio_col: str = "ratio",
) -> pd.DataFrame:
    """
    ACER method:
    Selects the worst CNEC per bidding zone and datetime,
    where worst means the minimum ratio.

    Expected input:
    The dataframe must already contain a column called 'ratio',
    for example:
        df['ratio'] = (df['ram'] + df['aac']) / df['fmax']

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    zones : list[str] | str | None
        Bidding zones to keep.
        - None: keep all zones
        - list: keep selected zones
        - str: comma-separated zones, e.g. "DK1,DK2,SE1"
    datetime_col : str
        Name of datetime column.
    zone_col : str
        Name of bidding zone column.
    cnec_col : str
        Name of CNEC column.
    ratio_col : str
        Name of ratio column.

    Returns
    -------
    pd.DataFrame
        DataFrame with:
        - datetime
        - bidding zone
        - cnecName
        - worst_cnec
        - ratio
    """

    required_cols = [datetime_col, zone_col, cnec_col, ratio_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")

    acer_df = df.copy()

    # Clean zone column
    acer_df[zone_col] = acer_df[zone_col].astype(str).str.strip()

    # Allow comma-separated string input
    if isinstance(zones, str):
        zones = [z.strip() for z in zones.split(",") if z.strip()]

    # Filter only if zones are provided 
    if zones is not None:
        zones = [z.strip() for z in zones]
        acer_df = acer_df[acer_df[zone_col].isin(zones)].copy()

    # Ensure correct types
    acer_df[datetime_col] = pd.to_datetime(acer_df[datetime_col], utc=True, errors="coerce")
    acer_df[ratio_col] = pd.to_numeric(acer_df[ratio_col], errors="coerce")

    # Remove invalid rows
    acer_df = acer_df.dropna(subset=[datetime_col, zone_col, cnec_col, ratio_col]).copy()

    if acer_df.empty:
        return pd.DataFrame(
            columns=[datetime_col, zone_col, cnec_col, "worst_cnec", ratio_col]
        )

    # Find the worst CNEC = minimum ratio per zone and datetime
    idx = acer_df.groupby([zone_col, datetime_col])[ratio_col].idxmin() # For each BZ zone and datetime, find the index of the row with the minimum ratio (worst CNEC)
    acer_df = acer_df.loc[idx].copy()

    # Explicit worst CNEC column
    acer_df["worst_cnec"] = acer_df[cnec_col]                           # For intuition we refer to this as the worst CNEC, but it is just the CNEC corresponding to the minimum ratio.

    # Keep only relevant output columns
    acer_df = acer_df[
        [datetime_col, zone_col, cnec_col, "worst_cnec", ratio_col]
    ].sort_values([zone_col, datetime_col]).reset_index(drop=True)

    return acer_df
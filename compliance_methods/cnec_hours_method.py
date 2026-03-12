import pandas as pd
import numpy as np


def run_cnec_hours_method(
    df: pd.DataFrame,
    zones: list[str] | None = None,
    tso_value: str = "ENERGINET",
    threshold: float = 0.7,
    datetime_col: str = "dateTimeUtc",
    zone_col: str = "biddingZoneFrom",
    cnec_col: str = "cnecName",
    ratio_col: str = "ratio",
) -> pd.DataFrame:
    """
    CNEC-hours method:
    For each (bidding zone, MTU), calculate the share of compliant CNECs.

    Compliance is defined as:
        ratio >= threshold

    Expected input:
    The dataframe must already contain a column called 'ratio', for example:
        df['ratio'] = (df['ram'] + df['aac']) / df['fmax']

    Output format is aligned with acer_df:
        - dateTimeUtc
        - biddingZoneFrom
        - worst_cnec  -> NaN since we can have several incompliant CNECs per MTU, and we are only interested in the share of compliant CNECs
        - ratio       -> compliant CNEC share per MTU
    """

    if zones is None:
        zones = ["DK1", "DK2"]

    required_cols = [datetime_col, zone_col, cnec_col,  ratio_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")

    cnec_df = df.copy()

    # Filter zones, which can be provided by the user. 
    cnec_df = cnec_df[
        
        (cnec_df[zone_col].isin(zones))
    ].copy()

    # Types
    cnec_df[datetime_col] = pd.to_datetime(cnec_df[datetime_col], utc=True, errors="coerce")
    cnec_df[ratio_col] = pd.to_numeric(cnec_df[ratio_col], errors="coerce")

    # Drop invalid rows
    cnec_df = cnec_df.dropna(subset=[datetime_col, zone_col, cnec_col, ratio_col]).copy()

    if cnec_df.empty:
        return pd.DataFrame(
            columns=[datetime_col, zone_col, "worst_cnec", "ratio"]
        )

    # Compliance on row level
    cnec_df["compliant"] = cnec_df[ratio_col] >= threshold

    # Per MTU and zone: total unique CNECs and number of noncompliant rows
    by_hour = (
        cnec_df
        .groupby([zone_col, datetime_col], as_index=False)              # this goups by the zones and datetime, So each group represents:(zone, hour),
        .agg(
            n_cnecs=(cnec_col, "nunique"),                              # count unique CNECs per group, which gives us the total number of CNECs affecting that zone and hour
            n_noncompliant=("compliant", lambda s: (~s).sum())          # This counts how many rows are NOT compliant.
        )
    )

    # Convert to compliant share
    by_hour["n_compliant"] = by_hour["n_cnecs"] - by_hour["n_noncompliant"]
    by_hour["ratio"] = by_hour["n_compliant"] / by_hour["n_cnecs"]

    # Keep same format as acer_df
    by_hour["worst_cnec"] = np.nan                                      # note this collum do not have the same meaning as in acer method, since we can have several incompliant CNECs per MTU, and we are only interested in the share of compliant CNECs. We keep the column for consistency with acer_df, but it will be filled with NaN.

    cnec_hours_df = by_hour[
        [datetime_col, zone_col, "worst_cnec", "ratio"]
    ].sort_values([zone_col, datetime_col]).reset_index(drop=True)

    return cnec_hours_df
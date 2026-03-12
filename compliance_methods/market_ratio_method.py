import pandas as pd
import numpy as np


def run_cnec_hours_market_weighted_method(  
    df: pd.DataFrame,
    zones: list[str] | None = None,
    tso_value: str = "ENERGINET",
    threshold: float = 0.7,
    datetime_col: str = "dateTimeUtc",
    zone_col: str = "biddingZoneFrom",
    cnec_col: str = "cnecName",
    ratio_col: str = "ratio",
    ram_col: str = "ram",
    aac_col: str = "aac",
) -> pd.DataFrame:
    """
    Weighted CNEC-hours method.

    For each (bidding zone, MTU), compute:

        ratio = compliant_weight / incompliant_weight

    where:
        weight = ram + aac

        compliant_weight   = sum(weight for rows with ratio >= threshold)
        incompliant_weight = sum(weight for rows with ratio < threshold)

    Output:
        - dateTimeUtc
        - biddingZoneFrom
        - worst_cnec
        - ratio
    """

    if zones is None:
        zones = ["DK1", "DK2"]

    required_cols = [datetime_col, zone_col, cnec_col, ratio_col, ram_col, aac_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")

    cnec_df = df.copy()

    # Filter zones
    cnec_df = cnec_df[cnec_df[zone_col].isin(zones)].copy()

    # Convert types
    cnec_df[datetime_col] = pd.to_datetime(cnec_df[datetime_col], utc=True, errors="coerce")
    cnec_df[ratio_col] = pd.to_numeric(cnec_df[ratio_col], errors="coerce")
    cnec_df[ram_col] = pd.to_numeric(cnec_df[ram_col], errors="coerce").fillna(0)
    cnec_df[aac_col] = pd.to_numeric(cnec_df[aac_col], errors="coerce").fillna(0)

    # Drop invalid rows
    cnec_df = cnec_df.dropna(subset=[datetime_col, zone_col, cnec_col, ratio_col]).copy()

    if cnec_df.empty:
        return pd.DataFrame(columns=[datetime_col, zone_col, "worst_cnec", "ratio"])

    # Weight
    cnec_df["weight"] = cnec_df[ram_col] + cnec_df[aac_col]

    # Compliance flag
    cnec_df["compliant"] = cnec_df[ratio_col] >= threshold

    # Split weights
    cnec_df["compliant_weight"] = np.where(cnec_df["compliant"], cnec_df["weight"], 0.0)
    cnec_df["incompliant_weight"] = np.where(~cnec_df["compliant"], cnec_df["weight"], 0.0)

    # Aggregate per zone and MTU
    by_hour = (
        cnec_df
        .groupby([zone_col, datetime_col], as_index=False)
        .agg(
            compliant_weight=("compliant_weight", "sum"),
            incompliant_weight=("incompliant_weight", "sum"),
        )
    )

    # Compute ratio safely
    by_hour["ratio"] =         by_hour["compliant_weight"] /(by_hour["compliant_weight"] + by_hour["incompliant_weight"])

    by_hour["worst_cnec"] = np.nan                                                  # This method does not identify a specific worst CNEC, as it is based on aggregated weights. We keep the column for consistency with other methods, but it will be NaN.

    cnec_hours_df = by_hour[
        [datetime_col, zone_col, "worst_cnec", "ratio"]
    ].sort_values([zone_col, datetime_col]).reset_index(drop=True)

    return cnec_hours_df
import numpy as np
import pandas as pd


def run_shadow_price_method(
    df: pd.DataFrame,
    zones: list[str] | None = None,
    datetime_col: str = "dateTimeUtc",
    zone_col: str = "biddingZoneFrom",
    cnec_col: str = "cnecName",
    shadow_price_col: str = "shadowPrice",
    ratio_col: str = "ratio",
) -> pd.DataFrame:
    """
    Shadow price method.

    Logic
    -----
    Return all CNECs.

    For each CNEC row:
    - if shadowPrice > 0:
        keep the existing ratio from the input dataframe
    - if shadowPrice <= 0 or missing:
        set ratio = 1.0 (count as compliant)

    This method does not identify a single worst CNEC, so worst_cnec is always NaN.

    Output columns
    --------------
    - dateTimeUtc
    - biddingZoneFrom
    - cnecName
    - worst_cnec
    - ratio
    - shadowPrice
    """

    if zones is None:
        zones = ["DK1", "DK2"]

    required_cols = [datetime_col, zone_col, cnec_col, shadow_price_col, ratio_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")

    shadow_df = df.copy()

    shadow_df = shadow_df[shadow_df[zone_col].isin(zones)].copy()


    shadow_df[datetime_col] = pd.to_datetime(
        shadow_df[datetime_col], utc=True, errors="coerce"
    )

    shadow_df[shadow_price_col] = pd.to_numeric(
        shadow_df[shadow_price_col], errors="coerce"
    ).fillna(0.0)

    shadow_df[ratio_col] = pd.to_numeric(
        shadow_df[ratio_col], errors="coerce"
    )


    shadow_df = shadow_df.dropna(
        subset=[datetime_col, zone_col, cnec_col]
    ).copy()


    if shadow_df.empty:
        return pd.DataFrame(
            columns=[
                datetime_col,
                zone_col,
                cnec_col,
                "worst_cnec",
                ratio_col,
                shadow_price_col,
            ]
        )

    # If there is no shadow price, force compliance
    shadow_df[ratio_col] = np.where(
        shadow_df[shadow_price_col] > 0,
        shadow_df[ratio_col],   # keep original ratio
        1.0                     # no shadow price => compliant
    )

    # This method does not identify one worst CNEC
    shadow_df["worst_cnec"] = np.nan                # only for consistency with other methods, will be NaN

    shadow_price_df = shadow_df[
        [
            datetime_col,
            zone_col,
            cnec_col,
            "worst_cnec",
            ratio_col,
            shadow_price_col,
        ]
    ].sort_values([zone_col, datetime_col, cnec_col]).reset_index(drop=True)

    return shadow_price_df
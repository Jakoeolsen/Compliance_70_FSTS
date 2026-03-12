import pandas as pd


def run_france_method(
    constraint_df: pd.DataFrame,
    spot_price_df: pd.DataFrame,
    constraint_datetime_col: str = "dateTimeUtc",
    constraint_zone_col: str = "biddingZoneFrom",
    spot_datetime_col: str = "DateTime(UTC)",
    spot_zone_col: str = "MapCode",
    spot_price_col: str = "Price[Currency/MWh]",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    France method with zone-specific price convergence exclusion.

    Convergence logic
    -----------------
    For DK1 assessment:
        full price convergence across ["N02", "DK1", "DK2"]

    For DK2 assessment:
        full price convergence across ["DK1", "DK2", "SE4"]

    If convergence is found for a given MTU, rows in constraint_df for that
    bidding zone and timestamp are removed.

    Returns
    -------
    filtered_df : pd.DataFrame
        constraint_df with converged MTUs removed zone-specifically

    converged_dk1_mtus_df : pd.DataFrame
        MTUs where ["N02", "DK1", "DK2"] are fully converged

    converged_dk2_mtus_df : pd.DataFrame
        MTUs where ["DK1", "DK2", "SE4"] are fully converged
    """

    dk1_convergence_zones = [ "DK1", "DK2"]
    dk2_convergence_zones = ["DK1", "DK2", "SE4"]

    required_constraint_cols = [constraint_datetime_col, constraint_zone_col]
    missing_constraint_cols = [
        col for col in required_constraint_cols if col not in constraint_df.columns
    ]
    if missing_constraint_cols:
        raise KeyError(f"Missing required constraint columns: {missing_constraint_cols}")

    required_spot_cols = [spot_datetime_col, spot_zone_col, spot_price_col]
    missing_spot_cols = [col for col in required_spot_cols if col not in spot_price_df.columns]
    if missing_spot_cols:
        raise KeyError(f"Missing required spot price columns: {missing_spot_cols}")

    # -----------------------------
    # Prepare spot price dataframe
    # -----------------------------
    spot_df = spot_price_df.copy()
    spot_df[spot_datetime_col] = pd.to_datetime(
        spot_df[spot_datetime_col], utc=True, errors="coerce"
    )
    spot_df[spot_zone_col] = spot_df[spot_zone_col].astype(str).str.strip()
    spot_df[spot_price_col] = pd.to_numeric(spot_df[spot_price_col], errors="coerce")

    spot_df = spot_df.dropna(
        subset=[spot_datetime_col, spot_zone_col, spot_price_col]
    ).copy()

    # Keep one row per timestamp-zone
    spot_df = (
        spot_df
        .sort_values([spot_datetime_col, spot_zone_col])
        .drop_duplicates(subset=[spot_datetime_col, spot_zone_col], keep="first")
        .copy()
    )

    def get_converged_mtus(
        df: pd.DataFrame,
        convergence_zones: list[str],
        output_datetime_col: str,
    ) -> pd.DataFrame:
        """Return MTUs where all zones are present and all prices are equal."""
        sub = df[df[spot_zone_col].isin(convergence_zones)].copy()

        converged = (
            sub.groupby(spot_datetime_col)
            .filter(
                lambda x: (
                    set(x[spot_zone_col]) == set(convergence_zones)
                    and x[spot_price_col].nunique() == 1
                )
            )[[spot_datetime_col]]
            .drop_duplicates()
            .rename(columns={spot_datetime_col: output_datetime_col})
            .sort_values(output_datetime_col)
            .reset_index(drop=True)
        )

        return converged

    # ----------------------------------------
    # Find converged MTUs separately
    # ----------------------------------------
    converged_dk1_mtus_df = get_converged_mtus(
        spot_df,
        dk1_convergence_zones,
        constraint_datetime_col,
    )

    converged_dk2_mtus_df = get_converged_mtus(
        spot_df,
        dk2_convergence_zones,
        constraint_datetime_col,
    )

    dk1_convergence_timestamps = pd.to_datetime(
        converged_dk1_mtus_df[constraint_datetime_col],
        utc=True,
        errors="coerce",
    )

    dk2_convergence_timestamps = pd.to_datetime(
        converged_dk2_mtus_df[constraint_datetime_col],
        utc=True,
        errors="coerce",
    )

    # -----------------------------
    # Filter constraint dataframe
    # -----------------------------
    filtered_df = constraint_df.copy()
    filtered_df[constraint_datetime_col] = pd.to_datetime(
        filtered_df[constraint_datetime_col], utc=True, errors="coerce"
    )
    filtered_df[constraint_zone_col] = filtered_df[constraint_zone_col].astype(str).str.strip()

    remove_mask = (
        (
            (filtered_df[constraint_zone_col] == "DK1")
            & (filtered_df[constraint_datetime_col].isin(dk1_convergence_timestamps))
        )
        |
        (
            (filtered_df[constraint_zone_col] == "DK2")
            & (filtered_df[constraint_datetime_col].isin(dk2_convergence_timestamps))
        )
    )

    filtered_df = filtered_df[~remove_mask].copy()

    filtered_df = (
        filtered_df
        .sort_values([constraint_zone_col, constraint_datetime_col])
        .reset_index(drop=True)
    )

    return filtered_df, converged_dk1_mtus_df, converged_dk2_mtus_df
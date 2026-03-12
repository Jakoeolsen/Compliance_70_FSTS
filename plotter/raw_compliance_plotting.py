import pandas as pd
import matplotlib.pyplot as plt


def plot_pct_above_70(
    acer_df: pd.DataFrame,
    ratio_col: str = "ratio",
    zone_col: str = "biddingZoneFrom",
    datetime_col: str = "dateTimeUtc",
    threshold: float = 0.7,
    title_template: str = "ACER compliance (ratio ≥ 70%)"
):
    """
    Plot percentage of MTUs where ratio >= threshold
    for DK1 and DK2 in a simple bar chart.
    """

    df = acer_df.copy()

    # Ensure correct types
    df[ratio_col] = pd.to_numeric(df[ratio_col], errors="coerce")
    df[datetime_col] = pd.to_datetime(df[datetime_col], utc=True, errors="coerce")

    df = df.dropna(subset=[ratio_col, datetime_col])

    # Boolean condition
    df["above_threshold"] = df[ratio_col] >= threshold

    # Total MTUs per zone
    total_mtus = df.groupby(zone_col)[datetime_col].nunique()

    # MTUs above threshold
    mtus_above = (
        df[df["above_threshold"]]
        .groupby(zone_col)[datetime_col]
        .nunique()
    )

    # Calculate percentage
    pct = (mtus_above / total_mtus) * 100

    zones = pct.index.tolist()
    values = pct.values

    plt.figure(figsize=(6,4))

    bars = plt.bar(zones, values)

    plt.ylabel(f"% of MTUs ≥ {threshold*100:.0f}%")
    plt.title(title_template)

    # Label bars
    for i, v in enumerate(values):
        plt.text(i, v + 1, f"{v:.1f}%", ha="center", fontweight="bold")

    plt.ylim(0, 100)

    plt.tight_layout()
    plt.show()
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DEFAULT_BINS = [-np.inf, 0.2, 0.5, 0.7, np.inf]
DEFAULT_LABELS = [
    "MACZT < 20%",
    "20% ≤ MACZT < 50%",
    "50% ≤ MACZT < 70%",
    "MACZT ≥ 70%",
]

MACZT_COLORS = {
    "MACZT < 20%": "#D9D9D9",         # The color code for ENTSOE Market report
    "20% ≤ MACZT < 50%": "#E69F00",   # The color code for ENTSOE Market report
    "50% ≤ MACZT < 70%": "#F0E442",
    "MACZT ≥ 70%": "#009E73",
}


def plot_zone_acer(                     # This function is called by plot_all_acer_zones() and should not be used directly by users.
    acer_df: pd.DataFrame,              # This function plots the ACER MACZT distribution for a single zone.
    zone: str,
    datetime_col: str = "dateTimeUtc",
    zone_col: str = "biddingZoneFrom",
    ratio_col: str = "ratio",
    threshold: float = 0.7,             # This is the threshold for compliance, i.e. the percentage of MTUs that must have MACZT >= 70% to be considered compliant.
    bins: list | None = None,
    labels: list | None = None,
    figsize: tuple = (8, 4.8),          # Change this for a bigger figure size.
    title: str | None = None,
) -> None:
    """
    Plot ACER MACZT distribution for one zone.

    Parameters
    ----------
    acer_df : pd.DataFrame
        Output from run_acer_method(), expected to contain:
        - dateTimeUtc
        - biddingZoneFrom
        - ratio
    zone : str
        Zone to plot, e.g. 'DK1' or 'DK2'
    title : str | None
        Plot title. If None, a default title is used.
    """
    if bins is None:
        bins = DEFAULT_BINS
    if labels is None:
        labels = DEFAULT_LABELS

    required_cols = [datetime_col, zone_col, ratio_col]  # Check if the required columns are present in the DataFrame
    missing_cols = [col for col in required_cols if col not in acer_df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")

    d = acer_df.copy()
    d[datetime_col] = pd.to_datetime(d[datetime_col], utc=True, errors="coerce")  # coerce will convert invalid parsing to NaT, which we can then drop
    d[ratio_col] = pd.to_numeric(d[ratio_col], errors="coerce")  # coerce will convert invalid parsing to NaN, which we can then drop
    d = d.dropna(subset=[datetime_col, zone_col, ratio_col]).copy()

    d = d[d[zone_col] == zone].copy()
    if d.empty:
        print(f"EMPTY -> no rows found for zone '{zone}'")
        return

    d["compliant"] = d[ratio_col] >= threshold
    d["cat"] = pd.cut(d[ratio_col], bins=bins, labels=labels, right=False)

    total = d[datetime_col].nunique()
    if total == 0:
        print(f"EMPTY -> no MTUs found for zone '{zone}'")
        return

    pct_not = []
    pct_comp = []

    for lab in labels:
        sub = d[d["cat"] == lab]
        comp = sub["compliant"].sum()
        notc = len(sub) - comp

        pct_comp.append(100 * comp / total)
        pct_not.append(100 * notc / total)

    x = np.arange(len(labels))
    width = 0.8

    fig, ax = plt.subplots(figsize=figsize)

    text_kw = dict(
        fontsize=12,
        fontweight="bold",
        color="black",
        bbox=dict(
            facecolor="white",
            edgecolor="none",
            alpha=0.75,
            boxstyle="round,pad=0.25",
        ),
    )

    for i, lab in enumerate(labels):
        ax.bar(
            x[i],
            pct_not[i],
            width,
            color=MACZT_COLORS[lab],
            edgecolor="black",
        )

        ax.bar(
            x[i],
            pct_comp[i],
            width,
            bottom=pct_not[i],
            color=MACZT_COLORS[lab],
            edgecolor="black",
            hatch="///",
        )

        if pct_not[i] > 0:
            ax.text(
                x[i],
                pct_not[i] / 2,
                f"{pct_not[i]:.1f}%",
                ha="center",
                va="center",
                **text_kw,
            )

        if pct_comp[i] > 0:
            ax.text(
                x[i],
                pct_not[i] + pct_comp[i] / 2,
                f"{pct_comp[i]:.1f}%",
                ha="center",
                va="center",
                **text_kw,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of MTUs")

    if title is None:
        title = f"MACZT for {zone}"
    ax.set_title(title)

    plt.tight_layout()
    plt.show()


def plot_all_acer_zones(
    acer_df: pd.DataFrame,
    zones=None,
    datetime_col: str = "dateTimeUtc",
    zone_col: str = "biddingZoneFrom",
    ratio_col: str = "ratio",
    threshold: float = 0.7,
    title_template: str | None = None,
    figsize: tuple = (8, 4.8),
    bins: list | None = None,
    labels: list | None = None,
) -> None:
    """
    Plot ACER MACZT distribution for multiple zones.

    Parameters
    ----------
    acer_df : pd.DataFrame
        Input DataFrame.
    zones : list | str | None
        Zones to plot. If None, defaults to ['DK1', 'DK2'].
        If a string is passed, it will be split by commas.
    title_template : str | None
        Template for plot titles. Use {zone} inside the string if you want
        the zone name inserted automatically.
        Example:
            "ACER MACZT distribution for {zone}"
        If None, default titles are used.
    """
    if zones is None:
        zones = ["DK1", "DK2"]  # default, but can be changed by user input

    # Clean zone names
    df = acer_df.copy()
    df[zone_col] = df[zone_col].astype(str).str.strip()

    # Convert string input if needed
    if isinstance(zones, str):
        zones = [z.strip() for z in zones.split(",") if z.strip()]

    for zone in zones:
        zone_df = df[df[zone_col] == zone].copy()

        if zone_df.empty:
            print(f"No data for zone {zone}")
            continue

        if title_template is None:
            zone_title = f"MACZT for {zone}"
        else:
            zone_title = title_template.format(zone=zone)

        plot_zone_acer(
            acer_df=zone_df,
            zone=zone,
            datetime_col=datetime_col,
            zone_col=zone_col,
            ratio_col=ratio_col,
            threshold=threshold,
            bins=bins,
            labels=labels,
            figsize=figsize,
            title=zone_title,
        )
import pandas as pd

import pandas as pd

def prepare_viking_link_dataframe(df_viking_link: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the full Viking Link preprocessing workflow:
    - rename columns
    - extract biddingZoneFrom from cnecName
    - create aac
    - extract and merge forecasted flow from DK1_GB_EXP
    - calculate dk1_vk_ptdf
    - calculate MNCC
    """

    df_viking_link = df_viking_link.copy()

    # Rename columns to match the main flow-based format
    df_viking_link.rename(columns={'tsoOrigin': 'tso'}, inplace=True)
    df_viking_link.rename(columns={'criticalBranch_name': 'cnecName'}, inplace=True)
    df_viking_link.rename(columns={'Datetime_UTC': 'dateTimeUtc'}, inplace=True)
    df_viking_link.rename(columns={'fMax': 'fmax'}, inplace=True)

    # Extract DK1 or DK2 from the cnecName string
    df_viking_link["biddingZoneFrom"] = df_viking_link["cnecName"].str.extract(
        r"\b(DK1|DK2)\b", expand=False
    )

    # Create AAC column
    df_viking_link["aac"] = 0

    # Get the forecasted flow for DK1_GB_EXP
    forcasted_flow = df_viking_link[
        df_viking_link["cnecName"] == "DK1_GB_EXP"
    ][["dateTimeUtc", "fRef"]].copy()

    # Rename for clarity before merge
    forcasted_flow = forcasted_flow.rename(columns={"fRef": "forecasted_flow"})

    # Merge forecasted flow back on dateTimeUtc
    df_viking_link = df_viking_link.merge(
        forcasted_flow,
        on="dateTimeUtc",
        how="left"
    )

    # Calculate PTDF difference
    df_viking_link["dk1_vk_ptdf"] = df_viking_link["DK1"] - df_viking_link["DK1_VL"]

    # Calculate MNCC
    df_viking_link["MNCC"] = (
        df_viking_link["dk1_vk_ptdf"] * df_viking_link["forecasted_flow"]
    )

    return df_viking_link
    
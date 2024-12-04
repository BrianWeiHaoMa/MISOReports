import os
import datetime
from collections import defaultdict
import io
from xml.etree import ElementTree as ET
import json
import zipfile

import requests
import pandas as pd, pandas
import numpy as np, numpy


"""A file to hold the parsers for the different reports.
"""


MULTI_DF_NAMES_COLUMN = "table_names"
MULTI_DF_DFS_COLUMN = "dataframes"


def parse_currentinterval(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(text),   
    )

    df[["LMP", "MLC", "MCC"]] = df[["LMP", "MLC", "MCC"]].astype(numpy.dtypes.Float64DType())
    df[["INTERVAL"]] = df[["INTERVAL"]].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S")
    df[["CPNODE"]] = df[["CPNODE"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_rt_bc_HIST(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text

    csv_data = "\n".join(text.splitlines()[2:-2])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),   
        dtype={
            "Flowgate NERCID": pandas.core.arrays.string_.StringDtype(),
            "Constraint_ID": pandas.core.arrays.string_.StringDtype(),
            "Preliminary Shadow Price": pandas.core.arrays.string_.StringDtype(),
        }, 
        low_memory=False,
    )

    df["Preliminary Shadow Price"] = df["Preliminary Shadow Price"].replace({
        r"\(\$": "-",
        r"\$": "",
        r"\)": "",
    }, regex=True)
    
    df[["BP1", "PC1", "BP2", "PC2", "Preliminary Shadow Price"]] = df[["BP1", "PC1", "BP2", "PC2", "Preliminary Shadow Price"]].astype(numpy.dtypes.Float64DType())
    df[["Override"]] = df[["Override"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Market Date"]] = df[["Market Date"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["Hour of Occurrence"]] = df[["Hour of Occurrence"]].apply(pd.to_datetime, format="%H:%M")
    df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]] = df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_RT_UDS_Approved_Case_Percentage(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text

    csv_data = "\n".join(text.splitlines()[3:-2])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),   
        dtype={
            "UDS Case ID": pandas.core.arrays.string_.StringDtype(),
        }
    )

    df[["Percentage"]] = df[["Percentage"]].astype(numpy.dtypes.Float64DType())
    df[["Dispatch Interval"]] = df[["Dispatch Interval"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M")

    return df


def parse_Resource_Uplift_by_Commitment_Reason(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=10,
        dtype={
            "REASON ID": pandas.core.arrays.string_.StringDtype(),
            "REASON": pandas.core.arrays.string_.StringDtype(),
        }
    ).iloc[:-2]

    df[["ECONOMIC MAX"]] = df[["ECONOMIC MAX"]].astype(numpy.dtypes.Float64DType())
    df[["LOCAL RESOURCE ZONE"]] = df[["LOCAL RESOURCE ZONE"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["STARTTIME"]] = df[["STARTTIME"]].apply(pd.to_datetime, format="%Y/%m/%d %I:%M:%S %p")

    return df


def parse_rt_rpe(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    ).iloc[:-1]

    df[["Shadow Price"]] = df[["Shadow Price"]].astype(numpy.dtypes.Float64DType())
    df[["Time of Occurence"]] = df[["Time of Occurence"]].apply(pd.to_datetime, format="%m-%d-%Y %H:%M:%S")
    df[["Constraint Name", "Constraint Description"]] = df[["Constraint Name", "Constraint Description"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_Historical_RT_RSG_Commitment(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text

    csv_data = "\n".join(text.splitlines()[:-2])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),   
    )

    df[["TOTAL_ECON_MAX"]] = df[["TOTAL_ECON_MAX"]].astype(numpy.dtypes.Float64DType())
    df[["MKT_INT_END_EST"]] = df[["MKT_INT_END_EST"]].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S")
    df[["COMMIT_REASON", "NUM_RESOURCES"]] = df[["COMMIT_REASON", "NUM_RESOURCES"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_da_pr(
    res: requests.Response,
) -> pd.DataFrame:
    df1 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=6,
        nrows=2,
    )
    df1.rename(columns={df1.columns[0]: "Type"}, inplace=True)
    df1.drop(labels=df1.columns[5:], axis=1, inplace=True)
    df1[["Type"]] = df1[["Type"]].astype(pandas.core.arrays.string_.StringDtype())
    df1[["Demand Fixed", " Demand Price Sensitive", "Demand Virtual", "Demand Total"]] = df1[["Demand Fixed", " Demand Price Sensitive", "Demand Virtual", "Demand Total"]].astype(numpy.dtypes.Float64DType())

    df2 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=9,
        nrows=3,
    )
    df2.rename(columns={df2.columns[0]: "Type"}, inplace=True)
    df2.drop(labels=df2.columns[4:], axis=1, inplace=True)
    df2[["Type"]] = df2[["Type"]].astype(pandas.core.arrays.string_.StringDtype())
    df2[["Supply Physical", "Supply Virtual", "Supply Total"]] = df2[["Supply Physical", "Supply Virtual", "Supply Total"]].astype(numpy.dtypes.Float64DType())

    df3 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=14,
        nrows=24,
    )
    shared_column_names = list(df3.columns)[1:]

    df3.rename(columns={df3.columns[0]: "Hour"}, inplace=True)
    df3[["Hour"]] = df3[["Hour"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df3[shared_column_names] = df3[shared_column_names].astype(numpy.dtypes.Float64DType())            

    df4 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=39,
        nrows=3,
        names=["Around the Clock"] + shared_column_names,
    )

    df5 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=43,
        nrows=3,
        names=["On-Peak"] + shared_column_names,
    )

    df6 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=47,
        nrows=3,
        names=["Off-Peak"] + shared_column_names,
    )

    bottom_dfs = [df4, df5, df6]
    for i in range(len(bottom_dfs)):
        first_column = bottom_dfs[i].columns[0]
        bottom_dfs[i][[first_column]] = bottom_dfs[i][[first_column]].astype(pandas.core.arrays.string_.StringDtype())
        bottom_dfs[i][shared_column_names] = bottom_dfs[i][shared_column_names].astype(numpy.dtypes.Float64DType())

    # No names written for any of the tables in the report.
    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                f"Table {i}" for i in range(1, 7)
        ], 
        MULTI_DF_DFS_COLUMN: [
                df1, 
                df2, 
                df3,
        ] + bottom_dfs,
    })

    return df


def parse_da_pbc(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text

    lines = text.splitlines()[4:-2]
    lines[0] = lines[0].replace(" ", "")

    csv_data = "\n".join(lines)

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),   
        usecols=range(14)
    )

    df[["MARKET_HOUR_EST"]] = df[["MARKET_HOUR_EST"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
    df[["PRELIMINARY_SHADOW_PRICE"]] = df[["PRELIMINARY_SHADOW_PRICE"]].astype(numpy.dtypes.Float64DType())
    df[["BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE"]] = df[["BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["CONSTRAINT_NAME", "CURVETYPE", "REASON"]] = df[["CONSTRAINT_NAME", "CURVETYPE", "REASON"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_da_bc(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    )

    df[["Shadow Price", "BP1", "PC1", "BP2", "PC2"]] = df[["Shadow Price", "BP1", "PC1", "BP2", "PC2"]].astype(numpy.dtypes.Float64DType())
    df[["Hour of Occurrence", "Override"]] = df[["Hour of Occurrence", "Override"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Flowgate NERC ID", "Constraint_ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason"]] = df[["Flowgate NERC ID", "Constraint_ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_da_bcsf(
    res: requests.Response,
) -> pd.DataFrame:
    sheet1 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
        sheet_name="Sheet1",
    )

    sheet2 = pd.read_excel(
        io=io.BytesIO(res.content),
        sheet_name="Sheet2",
        header=None,
        names=list(sheet1.columns),
        skipfooter=1,
    )

    df = pd.concat(objs=[sheet1, sheet2]).reset_index(drop=True)

    df[["From KV", "To KV", "Direction"]] = df[["From KV", "To KV", "Direction"]].round().astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Constraint ID", "Constraint Name", "Contingency Name", "Constraint Type", "Flowgate Name", "Device Type", "Key1", "Key2", "Key3", "From Area", "To Area", "From Station", "To Station"]] = df[["Constraint ID", "Constraint Name", "Contingency Name", "Constraint Type", "Flowgate Name", "Device Type", "Key1", "Key2", "Key3", "From Area", "To Area", "From Station", "To Station"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_rt_pr(
    res: requests.Response,
) -> pd.DataFrame:
    df1 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=6,
        nrows=1,
    )
    df1.rename(columns={df1.columns[0]: "Type"}, inplace=True)
    df1.drop(labels=df1.columns[4:], axis=1, inplace=True)
   
    df2 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=8,
        nrows=2,
    )
    df2.rename(columns={df2.columns[0]: "Type"}, inplace=True)
    df2.drop(labels=df2.columns[4:], axis=1, inplace=True)
    
    df1_and_df2 = pd.concat(objs=[df1, df2]).reset_index(drop=True)

    df1_and_df2[["Type"]] = df1_and_df2[["Type"]].astype(pandas.core.arrays.string_.StringDtype())
    df1_and_df2[["Demand", "Supply", "Total"]] = df1_and_df2[["Demand", "Supply", "Total"]].astype(numpy.dtypes.Float64DType())

    df3 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=11,
        nrows=24,
    )
    shared_column_names = list(df3.columns)[1:]

    df3.rename(columns={df3.columns[0]: "Hour"}, inplace=True)
    df3[["Hour"]] = df3[["Hour"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df3[shared_column_names] = df3[shared_column_names].astype(numpy.dtypes.Float64DType())            

    df4 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=36,
        nrows=3,
        names=["Around the Clock"] + shared_column_names,
    )

    df5 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=40,
        nrows=3,
        names=["On-Peak"] + shared_column_names,
    )

    df6 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=44,
        nrows=3,
        names=["Off-Peak"] + shared_column_names,
    )

    bottom_dfs = [df4, df5, df6]
    for i in range(len(bottom_dfs)):
        first_column = bottom_dfs[i].columns[0]
        bottom_dfs[i][[first_column]] = bottom_dfs[i][[first_column]].astype(pandas.core.arrays.string_.StringDtype())
        bottom_dfs[i][shared_column_names] = bottom_dfs[i][shared_column_names].astype(numpy.dtypes.Float64DType())

    # No names written for any of the tables in the report.
    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                f"Table {i}" for i in range(1, 6)
        ], 
        MULTI_DF_DFS_COLUMN: [
                df1_and_df2, 
                df3,
        ] + bottom_dfs,
    })

    return df


def parse_rt_irsf(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[4:-2])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df.rename(
        columns={
            " INTRAREGIONAL_SCHEDULED_FLOW": "INTRAREGIONAL_SCHEDULED_FLOW",
            " CONSTRAINT_NAME": "CONSTRAINT_NAME",
        }, 
        inplace=True,
    )

    df[["INTRAREGIONAL_SCHEDULED_FLOW"]] = df[["INTRAREGIONAL_SCHEDULED_FLOW"]].astype(numpy.dtypes.Float64DType())
    df[["CONSTRAINT_NAME"]] = df[["CONSTRAINT_NAME"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["MKTHOUR_EST"]] = df[["MKTHOUR_EST"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")

    return df


def parse_rt_mf(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    ).iloc[:-1]

    df[["Unit Count", "Hour Ending"]] = df[["Unit Count", "Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Peak Flag", "Region Name", "Fuel Type"]] = df[["Peak Flag", "Region Name", "Fuel Type"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Time Interval EST"]] = df[["Time Interval EST"]].apply(pd.to_datetime, format="%m/%d/%Y %I:%M:%S %p")

    return df


def parse_rt_ex(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
    )

    df.rename(
        columns={
            "Unnamed: 0": "Hour",
        }, 
        inplace=True,
    )

    df[["Committed (GW at Economic Maximum) - Forward", "Committed (GW at Economic Maximum) - Real-Time", "Committed (GW at Economic Maximum) - Delta", "Load (GW) - Forward", "Load (GW) - Real-Time", "Load (GW) - Delta", "Net Scheduled Imports (GW) - Forward", "Net Scheduled Imports (GW) - Real-Time", "Net Scheduled Imports (GW) - Delta", "Outages (GW at Economic Maximum) - Forward", "Outages (GW at Economic Maximum) - Real-Time", "Outages (GW at Economic Maximum) - Delta", "Offer Changes (GW at Economic Maximum) - Forward", "Offer Changes (GW at Economic Maximum) - Real-Time", "Offer Changes (GW at Economic Maximum) - Delta"]] = df[["Committed (GW at Economic Maximum) - Forward", "Committed (GW at Economic Maximum) - Real-Time", "Committed (GW at Economic Maximum) - Delta", "Load (GW) - Forward", "Load (GW) - Real-Time", "Load (GW) - Delta", "Net Scheduled Imports (GW) - Forward", "Net Scheduled Imports (GW) - Real-Time", "Net Scheduled Imports (GW) - Delta", "Outages (GW at Economic Maximum) - Forward", "Outages (GW at Economic Maximum) - Real-Time", "Outages (GW at Economic Maximum) - Delta", "Offer Changes (GW at Economic Maximum) - Forward", "Offer Changes (GW at Economic Maximum) - Real-Time", "Offer Changes (GW at Economic Maximum) - Delta"]].astype(numpy.dtypes.Float64DType())           
    df["Hour"] = df["Hour"].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Real-Time Binding Constraints - (#)"]] = df[["Real-Time Binding Constraints - (#)"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_rt_pbc(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[4:-2])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
        usecols=range(14),
    )

    df.rename(
        columns={
            " CONSTRAINT_NAME": "CONSTRAINT_NAME",
            " CURVETYPE": "CURVETYPE",
            " PRELIMINARY_SHADOW_PRICE": "PRELIMINARY_SHADOW_PRICE",
            " BP1": "BP1",
            " PC1": "PC1",
            " BP2": "BP2",
            " PC2": "PC2",
            " BP3": "BP3",
            " PC3": "PC3",
            " BP4": "BP4",
            " PC4": "PC4",
            " OVERRIDE": "OVERRIDE",
            " REASON": "REASON",
        }, 
        inplace=True,
    )

    df[["PRELIMINARY_SHADOW_PRICE"]] = df[["PRELIMINARY_SHADOW_PRICE"]].astype(numpy.dtypes.Float64DType())
    df[["BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE"]] = df[["BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["REASON", "CONSTRAINT_NAME", "CURVETYPE"]] = df[["REASON", "CONSTRAINT_NAME", "CURVETYPE"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["MARKET_HOUR_EST"]] = df[["MARKET_HOUR_EST"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")

    return df


def parse_rt_bc(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    )
    
    df.rename(
        columns={
            "Hour of  Occurrence": "Hour of Occurrence",
        }, 
        inplace=True,
    )

    df[["Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2"]] = df[["Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2"]].astype(numpy.dtypes.Float64DType())
    df[["Override"]] = df[["Override"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]] = df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Constraint ID", "Flowgate NERC ID"]] = df[["Constraint ID", "Flowgate NERC ID"]].astype(pandas.core.arrays.integer.Int64Dtype()).astype(pandas.core.arrays.string_.StringDtype())            
    df[["Hour of Occurrence"]] = df[["Hour of Occurrence"]].apply(pd.to_datetime, format="%H:%M")

    return df


def parse_rt_or(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    )

    df.rename(
        columns={
            "Hour of  Occurrence": "Hour of Occurrence",
        }, 
        inplace=True,
    )
    
    df[["Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2"]] = df[["Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2"]].astype(numpy.dtypes.Float64DType())
    df[["Override"]] = df[["Override"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason"]] = df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Flowgate NERC ID"]] = df[["Flowgate NERC ID"]].astype(pandas.core.arrays.integer.Int64Dtype()).astype(pandas.core.arrays.string_.StringDtype())            
    df[["Hour of Occurrence"]] = df[["Hour of Occurrence"]].apply(pd.to_datetime, format="%H:%M")

    return df


def parse_rt_fuel_on_margin(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        content = z.read(z.namelist()[0])

    df = pd.read_excel(
        io=io.BytesIO(content),
        skiprows=3,
    ).iloc[:-1]

    df[["Unit Count", "Hour Ending"]] = df[["Unit Count", "Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Peak Flag", "Region Name", "Fuel Type"]] = df[["Peak Flag", "Region Name", "Fuel Type"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Time Interval EST"]] = df[["Time Interval EST"]].apply(pd.to_datetime, format="%m/%d/%Y %I:%M:%S %p")

    return df


def parse_Total_Uplift_by_Resource(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=6,
    ).iloc[:-2]

    df[["Total Uplift Amount"]] = df[["Total Uplift Amount"]].astype(numpy.dtypes.Float64DType())
    df[["Resource Name"]] = df[["Resource Name"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_ms_vlr_srw(
    res: requests.Response,
) -> pd.DataFrame:
    float_columns = ["DA VLR RSG MWP", "RT VLR RSG MWP", "DA+RT Total"]
    string_columns = ["Constraint"]
    column_names = string_columns + float_columns

    df1 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=7,
        nrows=3,
        usecols=column_names,
    )
    df1[float_columns] = df1[float_columns].astype(numpy.dtypes.Float64DType())
    df1[string_columns] = df1[string_columns].astype(pandas.core.arrays.string_.StringDtype())

    df2 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=15,
        nrows=7,
        usecols=column_names,
    )
    df2[float_columns] = df2[float_columns].astype(numpy.dtypes.Float64DType())
    df2[string_columns] = df2[string_columns].astype(pandas.core.arrays.string_.StringDtype())

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                "Central",
                "South",
        ], 
        MULTI_DF_DFS_COLUMN: [
                df1, 
                df2, 
        ],
    })

    return df


def parse_ms_rsg_srw(
    res: requests.Response,
) -> pd.DataFrame:
    dfs = []
    sheets = ["MKT TOT", "ATC CMC rate", "MISO DDC rate", "VLR DIST", "RSG MONTHLY"]

    df1 = pd.read_excel(
        io=io.BytesIO(res.content),
        sheet_name=sheets[0],
        skiprows=7,
        skipfooter=2,
    )

    df1[["MISO_RT_RSG_DIST2", "RT_RSG_DIST1", "RT_RSG_MWP", "DA_RSG_MWP", "DA_RSG_DIST"]] = df1[["MISO_RT_RSG_DIST2", "RT_RSG_DIST1", "RT_RSG_MWP", "DA_RSG_MWP", "DA_RSG_DIST"]].astype(numpy.dtypes.Float64DType())
    df1[["previous 36 months"]] = df1[["previous 36 months"]].astype(pandas.core.arrays.string_.StringDtype())
    df1[["START", "STOP"]] = df1[["START", "STOP"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df1 = df1.drop(columns=["Unnamed: 6"])

    dfs.append(df1)

    for idx in range(1, 4):
        df_middle = pd.read_excel(
            io=io.BytesIO(res.content),
            sheet_name=sheets[idx],
            skiprows=1,
        )

        df_middle[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df_middle[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
        df_middle[["CHNL NBR"]] = df_middle[["CHNL NBR"]].astype(pandas.core.arrays.integer.Int64Dtype())
        df_middle[["OPERATING DATE"]] = df_middle[["OPERATING DATE"]].apply(pd.to_datetime, format="%Y-%m-%d")
        df_middle[["BILL_DETERMINANT"]] = df_middle[["BILL_DETERMINANT"]].astype(pandas.core.arrays.string_.StringDtype())


        if idx == 1:
            df_middle[["CONSTRAINT NAME"]] = df_middle[["CONSTRAINT NAME"]].astype(pandas.core.arrays.string_.StringDtype())

        dfs.append(df_middle)

    df5 = pd.read_excel(
        io=io.BytesIO(res.content),
        sheet_name=sheets[4],
        skiprows=1,
    )

    df5.drop(columns=["Unnamed: 0"], inplace=True)
    
    df5[["DA NVLR DIST", "DA VLR DIST", "RT VLR DIST", "MISO CMC DIST", "MISO DDC DIST", "MISO RT RSG DIST2"]] = df5[["DA NVLR DIST", "DA VLR DIST", "RT VLR DIST", "MISO CMC DIST", "MISO DDC DIST", "MISO RT RSG DIST2"]].astype(numpy.dtypes.Float64DType())
    df5[["OPERATING MONTH"]] = df5[["OPERATING MONTH"]].apply(pd.to_datetime, format="%Y-%m-%d")

    dfs.append(df5)

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: sheets,
        MULTI_DF_DFS_COLUMN: dfs,
    })

    return df


def parse_ms_rnu_srw(
    res: requests.Response,
) -> pd.DataFrame:
    SHEET1 = "MKT TOT"
    SHEET2 = "hourly miso_rt_bill_mtr"
    SHEET3 = "RT CC JOA column"

    df1 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=8,
        sheet_name=SHEET1,
    ).iloc[:-2]

    df1[["JOA_MISO_UPLIFT", "MISO_RT_GFACO_DIST", "MISO_RT_GFAOB_DIST", "MISO_RT_RSG_DIST2", "RT_CC", "DA_RI", "RT_RI", "ASM_RI", "STRDFC_UPLIFT", "CRDFC_UPLIFT", "MISO_PV_MWP_UPLIFT", "MISO_DRR_COMP_UPL", "MISO_TOT_MIL_UPL", "RC_DIST", "TOTAL RNU"]] = df1[["JOA_MISO_UPLIFT", "MISO_RT_GFACO_DIST", "MISO_RT_GFAOB_DIST", "MISO_RT_RSG_DIST2", "RT_CC", "DA_RI", "RT_RI", "ASM_RI", "STRDFC_UPLIFT", "CRDFC_UPLIFT", "MISO_PV_MWP_UPLIFT", "MISO_DRR_COMP_UPL", "MISO_TOT_MIL_UPL", "RC_DIST", "TOTAL RNU"]].astype(numpy.dtypes.Float64DType())
    df1[["previous 36 months"]] = df1[["previous 36 months"]].astype(pandas.core.arrays.string_.StringDtype())
    df1[["START", "STOP"]] = df1[["START", "STOP"]].apply(pd.to_datetime, format="$m/$d/Y")

    df2 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=1,
        sheet_name=SHEET2,
    )

    df2[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df2[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
    df2[["CHANNEL"]] = df2[["CHANNEL"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df2[["STARTTIME"]] = df2[["STARTTIME"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df2[["BILL_DETERMINANT"]] = df2[["BILL_DETERMINANT"]].astype(pandas.core.arrays.string_.StringDtype())

    df3 = pd.read_excel(
        io=io.BytesIO(res.content),
        sheet_name=SHEET3,
    )

    df3[["RT CC", "RT JOA", "NET"]] = df3[["RT CC", "RT JOA", "NET"]].astype(numpy.dtypes.Float64DType())
    df3[["HRBEG"]] = df3[["HRBEG"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                SHEET1,
                SHEET2,
                SHEET3,
        ], 
        MULTI_DF_DFS_COLUMN: [
                df1, 
                df2, 
                df3,
        ],
    })
    
    return df


def parse_ms_ri_srw(
    res: requests.Response,
) -> pd.DataFrame:
    SHEET1 = "MKT TOT"
    SHEET2 = "hourly column Worksheet"

    df1 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=7,
        dtype={
            "Previous Months": pd.StringDtype(),
        },
        sheet_name=SHEET1,
    ).iloc[:-2]

    df1[["DA RI", "RT RI", "TOTAL RI"]] = df1[["DA RI", "RT RI", "TOTAL RI"]].astype(numpy.dtypes.Float64DType())
    df1[["Previous Months"]] = df1[["Previous Months"]].astype(pandas.core.arrays.string_.StringDtype())
    df1[["START", "STOP"]] = df1[["START", "STOP"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df1 = df1.drop(columns=["Unnamed: 5"])

    df2 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=1,
        sheet_name=SHEET2,
        usecols=[0, 1, 2, 3, 5, 6, 8, 9]
    )

    df2.columns = pd.Index(
        data=[
            "date", 
            "hrend", 
            "Total RI hourly", 
            "Total RI cumulative",
            "DA_RI hourly", 
            "DA_RI cumulative",
            "RT_RI hourly", 
            "RT_RI cumulative",
        ],
    )

    df2[["Total RI hourly", "Total RI cumulative", "DA_RI hourly", "DA_RI cumulative", "RT_RI hourly", "RT_RI cumulative"]] = df2[["Total RI hourly", "Total RI cumulative", "DA_RI hourly", "DA_RI cumulative", "RT_RI hourly", "RT_RI cumulative"]].astype(numpy.dtypes.Float64DType())
    df2[["hrend"]] = df2[["hrend"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df2[["date"]] = df2[["date"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                SHEET1,
                SHEET2,
        ], 
        MULTI_DF_DFS_COLUMN: [
                df1, 
                df2, 
        ],
    })

    return df


def parse_MARKET_SETTLEMENT_DATA_SRW(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        csv_file_name = ""
        for name in z.namelist():
            if name.endswith(".csv"):
                csv_file_name = name
                break
        
        if csv_file_name == "":
            raise ValueError("Unexpected: no csv file found in zip file.")

        text = z.read(csv_file_name).decode("utf-8")

    csv_data = "\n".join(text.splitlines()[:-1])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df["DATE"] = pd.to_datetime(df["DATE"], format="%m/%d/%Y")
    df["BILL_DET"] = df["BILL_DET"].astype(pandas.core.arrays.string_.StringDtype())
    df[["HR01", "HR02", "HR03", "HR04", "HR05", "HR06", "HR07", "HR08", "HR09", "HR10", "HR11", "HR12", "HR13", "HR14", "HR15", "HR16", "HR17", "HR18", "HR19", "HR20", "HR21", "HR22", "HR23", "HR24"]] = df[["HR01", "HR02", "HR03", "HR04", "HR05", "HR06", "HR07", "HR08", "HR09", "HR10", "HR11", "HR12", "HR13", "HR14", "HR15", "HR16", "HR17", "HR18", "HR19", "HR20", "HR21", "HR22", "HR23", "HR24"]].astype(numpy.dtypes.Float64DType())

    return df


def parse_ms_vlr_HIST_SRW(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    ).iloc[:-2]

    df[["OPERATING DATE"]] = df[["OPERATING DATE"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total"]] = df[["DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total"]].astype(numpy.dtypes.Float64DType())
    df[["SETTLEMENT RUN"]] = df[["SETTLEMENT RUN"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["REGION", "CONSTRAINT"]] = df[["REGION", "CONSTRAINT"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_ms_ecf_srw(
    res: requests.Response,
) -> pd.DataFrame:
    SHEET1 = "MKT TOT"
    SHEET2 = "JOA Hourly Totals"
    SHEET3 = "RT CC JOA column"
    SHEET4 = "ECF"

    df1 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=6,
        sheet_name=SHEET1,
    ).iloc[:-3]

    df1.rename(columns={"Unnamed: 0": "Type"}, inplace=True)
    df1.drop(columns=["Unnamed: 11"], inplace=True)

    df1[["Da Xs Cg Fnd", "Rt Cc", "Rt Xs Cg Fnd", "Ftr Auc Res", "Ao Ftr Mn Alc", "Ftr Yr Alc *", "Tbs Access", "Net Ecf", "Ftr Shrtfll", "Net Ftr Sf", "Ftr Trg Cr Alc", "Ftr Hr Alc", "Hr Mf", "Hourly Ftr Allocation", "Monthly Ftr Allocation"]] = df1[["Da Xs Cg Fnd", "Rt Cc", "Rt Xs Cg Fnd", "Ftr Auc Res", "Ao Ftr Mn Alc", "Ftr Yr Alc *", "Tbs Access", "Net Ecf", "Ftr Shrtfll", "Net Ftr Sf", "Ftr Trg Cr Alc", "Ftr Hr Alc", "Hr Mf", "Hourly Ftr Allocation", "Monthly Ftr Allocation"]].replace(',','', regex=True).astype(numpy.dtypes.Float64DType())
    df1[["Type"]] = df1[["Type"]].astype(pandas.core.arrays.string_.StringDtype())
    df1[["Start", "Stop"]] = df1[["Start", "Stop"]].apply(pd.to_datetime, format="%m/%d/%Y")

    df2 = pd.read_excel(
        io=io.BytesIO(res.content),
        sheet_name=SHEET2,
    )
    df2.drop(columns=["Unnamed: 0"], inplace=True)

    df2.columns = pd.Index(
        data=[
            "HRBEG",
            "CNTR_RTO",
            "DA_JOA",
            "RT_JOA",
        ],
    )
    
    df2[["DA_JOA", "RT_JOA"]] = df2[["DA_JOA", "RT_JOA"]].astype(numpy.dtypes.Float64DType())
    df2[["HRBEG"]] = df2[["HRBEG"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
    df2[["CNTR_RTO"]] = df2[["CNTR_RTO"]].astype(pandas.core.arrays.string_.StringDtype())

    df3 = pd.read_excel(
        io=io.BytesIO(res.content),
        sheet_name=SHEET3,
        skiprows=1,
    )
    df3.columns = pd.Index(
        data=[
            "HRBEG",
            "RT CC",
            "RT JOA",
            "NET",
        ],
    )
    df3[["RT CC", "RT JOA", "NET"]] = df3[["RT CC", "RT JOA", "NET"]].astype(numpy.dtypes.Float64DType())
    df3[["HRBEG"]] = df3[["HRBEG"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")

    df4 = pd.read_excel(
        io=io.BytesIO(res.content),
        sheet_name=SHEET4,
    )
    df4.rename(columns={"OD\n": "OD"}, inplace=True)

    df4[["DA_ECF", "RT_ECF", "DART_ECF", "DART_monthly"]] = df4[["DA_ECF", "RT_ECF", "DART_ECF", "DART_monthly"]].astype(numpy.dtypes.Float64DType())
    df4[["OD"]] = df4[["OD"]].apply(pd.to_datetime, format="%m/%d/%Y")

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                SHEET1,
                SHEET2,
                SHEET3,
                SHEET4,
        ], 
        MULTI_DF_DFS_COLUMN: [
                df1, 
                df2, 
                df3,
                df4,
        ],
    })

    return df


def parse_ccf_co(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[4:-1])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["HOUR1", "HOUR2", "HOUR3", "HOUR4", "HOUR5", "HOUR6", "HOUR7", "HOUR8", "HOUR9", "HOUR10", "HOUR11", "HOUR12", "HOUR13", "HOUR14", "HOUR15", "HOUR16", "HOUR17", "HOUR18", "HOUR19", "HOUR20", "HOUR21", "HOUR22", "HOUR23", "HOUR24"]] = df[["HOUR1", "HOUR2", "HOUR3", "HOUR4", "HOUR5", "HOUR6", "HOUR7", "HOUR8", "HOUR9", "HOUR10", "HOUR11", "HOUR12", "HOUR13", "HOUR14", "HOUR15", "HOUR16", "HOUR17", "HOUR18", "HOUR19", "HOUR20", "HOUR21", "HOUR22", "HOUR23", "HOUR24"]].astype(numpy.dtypes.Float64DType())
    df[["CONSTRAINT NAME", "NODE NAME"]] = df[["CONSTRAINT NAME", "NODE NAME"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["OPERATING DATE"]] = df[["OPERATING DATE"]].apply(pd.to_datetime, format="%m/%d/%Y")

    return df


def parse_ms_vlr_HIST(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[3:-3])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total"]] = df[["DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total"]].astype(numpy.dtypes.Float64DType())
    df[["SETTLEMENT RUN"]] = df[["SETTLEMENT RUN"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["REGION", "CONSTRAINT"]] = df[["REGION", "CONSTRAINT"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["OPERATING DATE"]] = df[["OPERATING DATE"]].apply(pd.to_datetime, format="%m/%d/%Y")

    return df


def parse_Daily_Uplift_by_Local_Resource_Zone(
    res: requests.Response,
) -> pd.DataFrame:
    df0 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=9,
        nrows=1,
    )

    month_string = df0.iloc[0, 0]
    year_string = df0.iloc[0, 1]
    
    if type(year_string) == str and type(month_string) == str:
        year_string = year_string[-4:]
    else:
        raise ValueError("Unexpected: year_string or month_string is not a string.")
    
    date_string = f"{month_string} {year_string}"
    month_days = pd.Period(date_string, freq='M').days_in_month
    n_rows = month_days + 1
    
    def parse_report_part(skiprows: int) -> pd.DataFrame:
        df = pd.read_excel(
            io=io.BytesIO(res.content),
            skiprows=skiprows,
            nrows=n_rows,
        )
        df.rename(columns={
            df.columns[1]: "Date",
            "Price Volatility Make Whole Payments\n": "Price Volatility Make Whole Payments",
        }, inplace=True)
        df.drop(labels=df.columns[0], axis=1, inplace=True)

        df[["Date"]] = df[["Date"]].astype(pandas.core.arrays.string_.StringDtype())
        df[["Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments"]] = df[["Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments"]].astype(numpy.dtypes.Float64DType())

        return df

    dfs = [] # There should be 10 dfs.

    for i in range(10):
        df = parse_report_part(9 + (4 + n_rows) * i)
        dfs.append(df)

    table_names = [
        "LRZ 1",
        "LRZ 10",
        "LRZ 2",
        "LRZ 3",
        "LRZ 4",
        "LRZ 5",
        "LRZ 6",
        "LRZ 7",
        "LRZ 8",
        "LRZ 9",
    ]

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: table_names, 
        MULTI_DF_DFS_COLUMN: dfs,
    })

    return df


def parse_fuelmix(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["ACT", "TOTALMW"]] = df[["ACT", "TOTALMW"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["CATEGORY"]] = df[["CATEGORY"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["INTERVALEST"]] = df[["INTERVALEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df


def parse_ace(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["value"]] = df[["value"]].astype(numpy.dtypes.Float64DType())
    df[["instantEST"]] = df[["instantEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df


def parse_AncillaryServicesMCP(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    _, csv1, csv2 = text.split("\n\n")

    csv1_lines = csv1.splitlines()
    
    df1 = pd.read_csv(
        filepath_or_buffer=io.StringIO("\n".join(csv1_lines[1:])),
    )

    df1.rename(columns={" GenRegMCP": "GenRegMCP"}, inplace=True)

    df1[["number"]] = df1[["number"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df1[["GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp"]] = df1[["GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp"]].astype(numpy.dtypes.Float64DType())

    csv2_lines = csv2.splitlines()

    df2 = pd.read_csv(
        filepath_or_buffer=io.StringIO("\n".join(csv2_lines[1:])),
    )

    df2[["number"]] = df2[["number"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df2[["GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp"]] = df2[["GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp"]].astype(numpy.dtypes.Float64DType())
    
    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                f"{csv1_lines[0]}", 
                f"{csv2_lines[0]}"
        ], 
        MULTI_DF_DFS_COLUMN: [
                df1, 
                df2, 
        ],
    })
    
    return df


def parse_cts(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["PJMFORECASTEDLMP"]] = df[["PJMFORECASTEDLMP"]].astype(numpy.dtypes.Float64DType())
    df[["CASEAPPROVALDATE", "SOLUTIONTIME"]] = df[["CASEAPPROVALDATE", "SOLUTIONTIME"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df


def parse_combinedwindsolar(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["ForecastDateTimeEST", "ActualDateTimeEST"]] = df[["ForecastDateTimeEST", "ActualDateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")
    df[["ForecastHourEndingEST", "ActualHourEndingEST"]] = df[["ForecastHourEndingEST", "ActualHourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["ForecastWindValue", "ForecastSolarValue", "ActualWindValue", "ActualSolarValue"]] = df[["ForecastWindValue", "ForecastSolarValue", "ActualWindValue", "ActualSolarValue"]].astype(numpy.dtypes.Float64DType())

    return df


def parse_WindForecast(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    dictionary = json.loads(text)

    df = pd.DataFrame(
        data=dictionary["Forecast"],
    )

    df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())
    df[["HourEndingEST"]] = df[["HourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["DateTimeEST"]] = df[["DateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df


def parse_Wind(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["ForecastValue", "ActualValue"]] = df[["ForecastValue", "ActualValue"]].astype(numpy.dtypes.Float64DType())
    df[["ForecastHourEndingEST", "ActualHourEndingEST"]] = df[["ForecastHourEndingEST", "ActualHourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["ForecastDateTimeEST", "ActualDateTimeEST"]] = df[["ForecastDateTimeEST", "ActualDateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df


def parse_SolarForecast(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    dictionary = json.loads(text)

    df = pd.DataFrame(
        data=dictionary["Forecast"],
    )

    df[["DateTimeEST"]] = df[["DateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")
    df[["HourEndingEST"]] = df[["HourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())

    return df


def parse_Solar(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["ForecastValue", "ActualValue"]] = df[["ForecastValue", "ActualValue"]].astype(numpy.dtypes.Float64DType())
    df[["ForecastHourEndingEST", "ActualHourEndingEST"]] = df[["ForecastHourEndingEST", "ActualHourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["ForecastDateTimeEST", "ActualDateTimeEST"]] = df[["ForecastDateTimeEST", "ActualDateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df


def parse_exantelmp(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["LMP", "Loss", "Congestion"]] = df[["LMP", "Loss", "Congestion"]].astype(numpy.dtypes.Float64DType())
    df[["Name"]] = df[["Name"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_da_exante_lmp(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[4:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
    df[["Node", "Type", "Value"]] = df[["Node", "Type", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_da_expost_lmp(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[4:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
    df[["Node", "Type", "Value"]] = df[["Node", "Type", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_rt_lmp_final(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[4:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
    df[["Node", "Type", "Value"]] = df[["Node", "Type", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_rt_lmp_prelim(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[4:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
    df[["Node", "Type", "Value"]] = df[["Node", "Type", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_DA_Load_EPNodes(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        text = z.read(z.namelist()[0]).decode("utf-8")

    csv_data = "\n".join(text.splitlines()[4:-1])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
    df[["EPNode", "Value"]] = df[["EPNode", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_DA_LMPs(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        text = z.read(z.namelist()[0]).decode("utf-8")

    csv_data = "\n".join(text.splitlines()[1:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["MARKET_DAY"]] = df[["MARKET_DAY"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
    df[["NODE", "TYPE", "VALUE"]] = df[["NODE", "TYPE", "VALUE"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_5min_exante_lmp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    ).iloc[:-1]

    df[["RT Ex-Ante LMP", "RT Ex-Ante MEC", "RT Ex-Ante MLC", "RT Ex-Ante MCC"]] = df[["RT Ex-Ante LMP", "RT Ex-Ante MEC", "RT Ex-Ante MLC", "RT Ex-Ante MCC"]].astype(numpy.dtypes.Float64DType())
    df[["CP Node"]] = df[["CP Node"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Time (EST)"]] = df[["Time (EST)"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df


def parse_nsi1(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["timestamp"]] = df[["timestamp"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")
    df[["AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE"]] = df[["AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_nsi5(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["timestamp"]] = df[["timestamp"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")
    df[["AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE"]] = df[["AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df
    

def parse_nsi1miso(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["timestamp"]] = df[["timestamp"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")
    df[["NSI"]] = df[["NSI"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_nsi5miso(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["timestamp"]] = df[["timestamp"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")
    df[["NSI"]] = df[["NSI"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_importtotal5(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    dictionary = json.loads(text)

    df = pd.DataFrame(
        data=dictionary
    )

    df[["Time"]] = df[["Time"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")
    df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())

    return df


def parse_reservebindingconstraints(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["Price"]] = df[["Price"]].astype(numpy.dtypes.Float64DType())
    df[["Period"]] = df[["Period"]].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S")
    df[["Name", "Description"]] = df[["Name", "Description"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_totalload(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text

    table_1 = "ClearedMW"
    df1 = pd.read_csv(
        filepath_or_buffer=io.StringIO(text),
        skiprows=3,
        nrows=24,
    )
    df1[["Load_Hour"]] = df1[["Load_Hour"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df1[["Load_Value"]] = df1[["Load_Value"]].astype(numpy.dtypes.Float64DType())

    table_2 = "MediumTermLoadForecast"
    df2 = pd.read_csv(
        filepath_or_buffer=io.StringIO(text),
        skiprows=29,
        nrows=24,
    )
    df2[["Hour_End"]] = df2[["Hour_End"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df2[["Load_Forecast"]] = df2[["Load_Forecast"]].astype(numpy.dtypes.Float64DType())

    table_3 = "FiveMinTotalLoad"
    df3 = pd.read_csv(
        filepath_or_buffer=io.StringIO(text),
        skiprows=55,
    )
    df3[["Load_Time"]] = df3[["Load_Time"]].apply(pd.to_datetime, format="%H:%M")
    df3[["Load_Value"]] = df3[["Load_Value"]].astype(numpy.dtypes.Float64DType())

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
            table_1,
            table_2,
            table_3,
        ],
        MULTI_DF_DFS_COLUMN: [
            df1,
            df2,
            df3,
        ],
    })

    return df


def parse_RSG(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["TOTAL_ECON_MAX"]] = df[["TOTAL_ECON_MAX"]].astype(numpy.dtypes.Float64DType())
    df[["MKT_INT_END_EST"]] = df[["MKT_INT_END_EST"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S %p")
    df[["COMMIT_REASON", "NUM_RESOURCES"]] = df[["COMMIT_REASON", "NUM_RESOURCES"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_WindActual(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    dictionary = json.loads(text)

    df = pd.DataFrame(
        data=dictionary["instance"],
    )

    df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())
    df[["HourEndingEST"]] = df[["HourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["DateTimeEST"]] = df[["DateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df  


def parse_SolarActual(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    dictionary = json.loads(text)

    df = pd.DataFrame(
        data=dictionary["instance"],
    )

    df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())
    df[["HourEndingEST"]] = df[["HourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["DateTimeEST"]] = df[["DateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df 


def parse_NAI(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["Name"]] = df[["Name"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())

    return df  


def parse_regionaldirectionaltransfer(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["NORTH_SOUTH_LIMIT", "SOUTH_NORTH_LIMIT", "RAW_MW", " UDSFLOW_MW"]] = df[["NORTH_SOUTH_LIMIT", "SOUTH_NORTH_LIMIT", "RAW_MW", " UDSFLOW_MW"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["INTERVALEST"]] = df[["INTERVALEST"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S %p")

    return df


def parse_generationoutagesplusminusfivedays(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["Unplanned", "Planned", "Forced", "Derated"]] = df[["Unplanned", "Planned", "Forced", "Derated"]].astype(pandas.core.arrays.integer.Int64Dtype())  
    df[["OutageDate"]] = df[["OutageDate"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S %p")
    df[["OutageMonthDay"]] = df[["OutageMonthDay"]].astype(pandas.core.arrays.string_.StringDtype())

    return df  


def parse_apiversion(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    dictionary = json.loads(text)


    df = pd.DataFrame(
        data=[dictionary]
    )

    df[["Semantic"]] = df[["Semantic"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_lmpconsolidatedtable(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[3:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["LMP", "MLC", "MCC", "REGMCP", "REGMILEAGEMCP", "SPINMCP", "SUPPMCP", "STRMCP", "RCUPMCP", "RCDOWNMCP", "LMP.1", "MLC.1", "MCC.1", "LMP.2", "MLC.2", "MCC.2", "LMP.3", "MLC.3", "MCC.3"]] = df[["LMP", "MLC", "MCC", "REGMCP", "REGMILEAGEMCP", "SPINMCP", "SUPPMCP", "STRMCP", "RCUPMCP", "RCDOWNMCP", "LMP.1", "MLC.1", "MCC.1", "LMP.2", "MLC.2", "MCC.2", "LMP.3", "MLC.3", "MCC.3"]].astype(numpy.dtypes.Float64DType())
    df[["Name"]] = df[["Name"]].astype(pandas.core.arrays.string_.StringDtype())

    return df  


def parse_realtimebindingconstraints(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["Price"]] = df[["Price"]].astype(numpy.dtypes.Float64DType())
    df[["OVERRIDE", "BP1", "PC1", "BP2", "PC2"]] = df[["OVERRIDE", "BP1", "PC1", "BP2", "PC2"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Period"]] = df[["Period"]].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S")
    df[["Name", "CURVETYPE"]] = df[["Name", "CURVETYPE"]].astype(pandas.core.arrays.string_.StringDtype())
    
    return df


def parse_realtimebindingsrpbconstraints(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["Price"]] = df[["Price"]].astype(numpy.dtypes.Float64DType())
    df[["OVERRIDE", "BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4"]] = df[["OVERRIDE", "BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Period"]] = df[["Period"]].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S")
    df[["Name", "REASON", "CURVETYPE"]] = df[["Name", "REASON", "CURVETYPE"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_RT_Load_EPNodes(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        text = z.read(z.namelist()[0]).decode("utf-8")

    csv_data = "\n".join(text.splitlines()[4:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )[:-1]

    df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
    df[["EPNode", "Value"]] = df[["EPNode", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_5MIN_LMP(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        text = z.read(z.namelist()[0]).decode("utf-8")

    csv_data = "\n".join(text.splitlines()[4:-2])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["LMP", "CON_LMP", "LOSS_LMP"]] = df[["LMP", "CON_LMP", "LOSS_LMP"]].astype(numpy.dtypes.Float64DType())
    df[["MKTHOUR_EST"]] = df[["MKTHOUR_EST"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M")
    df[["PNODENAME"]] = df[["PNODENAME"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_bids_cb(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        csv_data = z.read(z.namelist()[0]).decode("utf-8")

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["MW", "LMP", "PRICE1", "MW1", "PRICE2", "MW2", "PRICE3", "MW3", "PRICE4", "MW4", "PRICE5", "MW5", "PRICE6", "MW6", "PRICE7", "MW7", "PRICE8", "MW8", "PRICE9", "MW9"]] = df[["MW", "LMP", "PRICE1", "MW1", "PRICE2", "MW2", "PRICE3", "MW3", "PRICE4", "MW4", "PRICE5", "MW5", "PRICE6", "MW6", "PRICE7", "MW7", "PRICE8", "MW8", "PRICE9", "MW9"]].astype(numpy.dtypes.Float64DType())
    df[["Date/Time Beginning (EST)", "Date/Time End (EST)"]] = df[["Date/Time Beginning (EST)", "Date/Time End (EST)"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
    df[["Market Participant Code", "Region", "Type of Bid", "Bid ID"]] = df[["Market Participant Code", "Region", "Type of Bid", "Bid ID"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def helper_parse_asm(
        csv1_lines: str,
        csv2_lines: str,
) -> pd.DataFrame:
    table_1 = "Table 1"
    df1 = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv1_lines),
        skipinitialspace=True,
    )

    df1.drop(columns=["Unnamed: 0", "Unnamed: 1"], inplace=True)

    hours = [f"HE {i}" for i in range(1, 25)]
    df1[hours] = df1[hours].astype(numpy.dtypes.Float64DType())
    df1[["MCP Type"]] = df1[["MCP Type"]].astype(pandas.core.arrays.string_.StringDtype())

    table_2 = "Table 2"

    df2 = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv2_lines),
        skipinitialspace=True,
    )

    df2[hours] = df2[hours].astype(numpy.dtypes.Float64DType())
    df2[["Zone"]] = df2[["Zone"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df2[["Pnode", "MCP Type"]] = df2[["Pnode", "MCP Type"]].astype(pandas.core.arrays.string_.StringDtype())

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
            table_1,
            table_2,
        ],
        MULTI_DF_DFS_COLUMN: [
            df1,
            df2,
        ],
    })

    return df


def parse_asm_exante_damcp(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text

    second_table_start_idx = text.index("Pnode,Zone,MCP Type")

    return helper_parse_asm(
        csv1_lines="\n".join(text[:second_table_start_idx].splitlines()[4:]), 
        csv2_lines=text[second_table_start_idx:],
    )


def helper_parse_ftr_allocation(
    res: requests.Response,
) -> pd.DataFrame:
    data_mapping = {}

    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        file_paths = sorted(z.namelist())
        file_names = [os.path.basename(file_path) for file_path in file_paths]
        
        for file_path, file_name in zip(file_paths, file_names):
            data_mapping[file_name] = z.read(file_path).decode("utf-8")

    columns = list(pd.read_csv(filepath_or_buffer=io.StringIO(data_mapping[file_names[0]])).columns)

    string_columns = columns[:4] + columns[7:]
    float_columns = columns[4:7]

    dfs = []
    for file_name in file_names:
        data = data_mapping[file_name]

        df = pd.read_csv(
            filepath_or_buffer=io.StringIO(data),
        )

        df[float_columns] = df[float_columns].astype(numpy.dtypes.Float64DType())
        df[string_columns] = df[string_columns].astype(pandas.core.arrays.string_.StringDtype())

        dfs.append(df)

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
            "Fall",
            "Spring",
            "Summer",
            "Winter",
        ],
        MULTI_DF_DFS_COLUMN: dfs,
    })

    return df


def parse_ftr_allocation_restoration(
    res: requests.Response,
) -> pd.DataFrame:
    return helper_parse_ftr_allocation(res)


def parse_ftr_allocation_stage_1A(
    res: requests.Response,
) -> pd.DataFrame:
    return helper_parse_ftr_allocation(res)


def parse_ftr_allocation_stage_1B(
    res: requests.Response,
) -> pd.DataFrame:
    return helper_parse_ftr_allocation(res)


def parse_ftr_allocation_summary(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        residule_file, allocation_file = z.namelist()

        residule_content, allocation_content = z.read(residule_file), z.read(allocation_file)

    df_residule = pd.read_excel(
        io=io.BytesIO(residule_content),
    ).iloc[:-4]

    df_residule[["STAGE2MW", "STAGE2PAYMENT"]] = df_residule[["STAGE2MW", "STAGE2PAYMENT"]].astype(numpy.dtypes.Float64DType())
    df_residule[["ID_TOU"]] = df_residule[["ID_TOU"]].astype(pandas.core.arrays.string_.StringDtype())
    df_residule[["START_DATE"]] = df_residule[["START_DATE"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")

    df_allocation = pd.read_excel(
        io=io.BytesIO(allocation_content),
    )

    df_allocation[["MW"]] = df_allocation[["MW"]].astype(numpy.dtypes.Float64DType())
    df_allocation[["DATE_START", "DATE_END"]] = df_allocation[["DATE_START", "DATE_END"]].apply(pd.to_datetime, format="%m/%d/%Y %I:%M:%S %p")
    df_allocation[["MARKET_NAME", "ID_TOU", "SOURCE_NAME", "SINK_NAME", "STAGE", "TYPE"]] = df_allocation[["MARKET_NAME", "ID_TOU", "SOURCE_NAME", "SINK_NAME", "STAGE", "TYPE"]].astype(pandas.core.arrays.string_.StringDtype())

    df = pd.DataFrame(data={
        MULTI_DF_NAMES_COLUMN: [residule_file.split('/')[-1][:-5], allocation_file.split('/')[-1][:-5]], 
        MULTI_DF_DFS_COLUMN: [df_residule, df_allocation],
    })

    return df


def helper_parse_ftr(
    res: requests.Response,
    files_by_type: defaultdict[str, list[dict[str, str]]],
) -> pd.DataFrame:
    def get_date_key(file_path: str) -> tuple[int, int]:
        parts = file_path.split("/")[-1].split("_")[1:]

        date_part = parts[0]
        month_str = date_part[:3]
        year_str = date_part[3:] 
        months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
        month = months.get(month_str, 0) 
        year = int("20" + year_str) 
        
        return (year, month)

    df_names = []
    dfs = []

    files_by_name = {
        file["name"]: file for file in files_by_type["BindingConstraint"]
    }

    sorted_files = [files_by_name[name] for name in sorted(files_by_name.keys(), key=get_date_key)]

    file_counter = 0
    file_names = []

    for csv_file in sorted_files:
        df = pd.read_csv(
            filepath_or_buffer=io.StringIO(csv_file["data"]),
        )

        df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
        df[["Flow", "Limit", "MarginalCost", "Violation"]] = df[["Flow", "Limit", "MarginalCost", "Violation"]].astype(numpy.dtypes.Float64DType())
        df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]] = df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]].astype(pandas.core.arrays.string_.StringDtype())
        
        file_counter += 1
        df_names.append(f"File {file_counter}")
        
        file_names.append(csv_file["name"].split("/")[-1].split(".")[0])

        dfs.append(df)

    files_by_name = {
        file["name"]: file for file in files_by_type["MarketResults"]
    }

    sorted_files = [files_by_name[name] for name in sorted(files_by_name.keys(), key=get_date_key)]

    for csv_file in sorted_files:
        df = pd.read_csv(
            filepath_or_buffer=io.StringIO(csv_file["data"]),
        )

        df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
        df[["MW", "ClearingPrice"]] = df[["MW", "ClearingPrice"]].astype(numpy.dtypes.Float64DType())
        df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "HedgeType", "Type", "Class"]] = df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "HedgeType", "Type", "Class"]].astype(pandas.core.arrays.string_.StringDtype())
        df[["StartDate", "EndDate"]] = df[["StartDate", "EndDate"]].apply(pd.to_datetime, format="%m/%d/%Y")
 
        file_counter += 1
        df_names.append(f"File {file_counter}")
        
        file_names.append(csv_file["name"].split("/")[-1].split(".")[0])

        dfs.append(df)
    
    files_by_name = {
        file["name"]: file for file in files_by_type["SourceSinkShadowPrices"]
    }

    sorted_files = [files_by_name[name] for name in sorted(files_by_name.keys(), key=get_date_key)]

    for csv_file in sorted_files:
        df = pd.read_csv(
            filepath_or_buffer=io.StringIO(csv_file["data"]),
        )

        df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
        df[["ShadowPrice"]] = df[["ShadowPrice"]].astype(numpy.dtypes.Float64DType())
        df[["SourceSink", "Class"]] = df[["SourceSink", "Class"]].astype(pandas.core.arrays.string_.StringDtype())

        file_counter += 1
        df_names.append(f"File {file_counter}")
        
        file_names.append(csv_file["name"].split("/")[-1].split(".")[0])
        
        dfs.append(df)

    metadata_df = pd.DataFrame(data={
        f"File {num + 1}": [name] for num, name in enumerate(file_names)
    })

    metadata_columns = [f"File {num}" for num in range(1, len(file_names) + 1)]
    metadata_df[metadata_columns] = metadata_df[metadata_columns].astype(pandas.core.arrays.string_.StringDtype())
        
    df = pd.DataFrame(data={
        MULTI_DF_NAMES_COLUMN: ["Metadata"] + df_names, 
        MULTI_DF_DFS_COLUMN: [metadata_df] + dfs,
    })
    
    return df


def parse_ftr_annual_results_round_1(
    res: requests.Response,
) -> pd.DataFrame:
    files_by_type = defaultdict(list)

    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        for filename in z.namelist():
            prefix = filename.split('_')[0]
            
            files_by_type[prefix].append({
                "name": filename, 
                "data": z.read(filename).decode("utf-8"),
            })

    return helper_parse_ftr(res=res, files_by_type=files_by_type)


def parse_ftr_annual_results_round_2(
    res: requests.Response,
) -> pd.DataFrame:
    files_by_type = defaultdict(list)

    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        for filename in z.namelist():
            filepath = filename.split('/')
            prefix = filepath[1].split('_')[0]
            
            files_by_type[prefix].append({
                "name": filename, 
                "data": z.read(filename).decode("utf-8"),
            })

    return helper_parse_ftr(res=res, files_by_type=files_by_type)


def parse_ftr_annual_results_round_3(
    res: requests.Response,
) -> pd.DataFrame:
    files_by_type = defaultdict(list)

    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        for filename in z.namelist():
            filepath = filename.split('/')
            prefix = filepath[1].split('_')[0]
            
            files_by_type[prefix].append({
                "name": filename, 
                "data": z.read(filename).decode("utf-8"),
            })

    return helper_parse_ftr(res=res, files_by_type=files_by_type)


def parse_ftr_annual_bids_offers(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        csv_data = z.read(z.namelist()[0]).decode("utf-8")

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
        dtype={"Asset Owner ID": pandas.core.arrays.string_.StringDtype()},
    )[:-1]

    df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df[["MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10"]] = df[["MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10"]].astype(numpy.dtypes.Float64DType())
    df[["Market Name", "Source", "Sink", "Hedge Type", "Class", "Type"]] = df[["Market Name", "Source", "Sink", "Hedge Type", "Class", "Type"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Start Date", "End Date"]] = df[["Start Date", "End Date"]].apply(pd.to_datetime, format="%m/%d/%Y")
    
    return df


def parse_ftr_mpma_results(
    res: requests.Response,
) -> pd.DataFrame:
    files_by_type = defaultdict(list)

    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        for filename in z.namelist():
            filepath = filename.split('/')
            prefix = filepath[1].split('_')[0]
            
            files_by_type[prefix].append({
                "name": filename, 
                "data": z.read(filename).decode("utf-8"),
            })

    return helper_parse_ftr(res=res, files_by_type=files_by_type)


def parse_ftr_mpma_bids_offers(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        csv_data = z.read(z.namelist()[0]).decode("utf-8")

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
        dtype={"Asset Owner ID": pandas.core.arrays.string_.StringDtype()},
    )[:-1]

    df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df[["MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10"]] = df[["MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10"]].astype(numpy.dtypes.Float64DType())
    df[["Market Name", "Source", "Sink", "Hedge Type", "Class", "Type"]] = df[["Market Name", "Source", "Sink", "Hedge Type", "Class", "Type"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Start Date", "End Date"]] = df[["Start Date", "End Date"]].apply(pd.to_datetime, format="%m/%d/%Y")

    return df


def parse_asm_expost_damcp(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv1, csv2 = text.split("\n\n\n")

    csv1_lines = csv1.splitlines()

    return helper_parse_asm(
        csv1_lines="\n".join(csv1_lines[4:]), 
        csv2_lines=csv2,
    )


def parse_asm_rtmcp_final(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    _, _, csv1, csv2 = text.split("\r\n\r\n")

    return helper_parse_asm(csv1_lines=csv1, csv2_lines=csv2)


def parse_asm_rtmcp_prelim(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    _, _, csv1, csv2 = text.split("\r\n\r\n")

    return helper_parse_asm(csv1_lines=csv1, csv2_lines=csv2)


def parse_5min_exante_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    ).iloc[:-1]

    df[["RT Ex-Ante MCP Regulation", "RT Ex-Ante MCP Spin", "RT Ex-Ante MCP Supp"]] = df[["RT Ex-Ante MCP Regulation", "RT Ex-Ante MCP Spin", "RT Ex-Ante MCP Supp"]].astype(numpy.dtypes.Float64DType())
    df[["Zone"]] = df[["Zone"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Time (EST)"]] = df[["Time (EST)"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df


def parse_5min_expost_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    ).iloc[:-1]

    df[["RT MCP Regulation", "RT MCP Spin", "RT MCP Supp"]] = df[["RT MCP Regulation", "RT MCP Spin", "RT MCP Supp"]].astype(numpy.dtypes.Float64DType())
    df[["Zone"]] = df[["Zone"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Time (EST)"]] = df[["Time (EST)"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df


def parse_da_exante_ramp_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
    ).iloc[:-1]
        
    df.columns = pd.Index([
        "Hour Ending",
    ] + [
        f"Reserve Zone {zone_num} - {direction}" 
        for zone_num in range(1, 9) 
        for direction in ["DA MCP Ramp Up Ex-Ante 1 Hour", "DA MCP Ramp Down Ex-Ante 1 Hour"]
    ])
    
    df[["Reserve Zone 1 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Ante 1 Hour"]] = df[["Reserve Zone 1 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Ante 1 Hour"]].astype(numpy.dtypes.Float64DType())
    df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_da_exante_str_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=7,
    ).iloc[:-1]
        
    df = df.rename(columns={idx: f"Reserve Zone {idx}" for idx in range(1, 9)})

    df[["Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8"]] = df[["Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8"]].astype(numpy.dtypes.Float64DType())
    df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_da_expost_ramp_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
    ).iloc[:-1]
        
    df.columns = pd.Index([
        "Hour Ending",
    ] + [
        f"Reserve Zone {zone_num} - {direction}" 
        for zone_num in range(1, 9) 
        for direction in ["DA MCP Ramp Up Ex-Post 1 Hour", "DA MCP Ramp Down Ex-Post 1 Hour"]
    ])

    df[["Reserve Zone 1 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Post 1 Hour"]] = df[["Reserve Zone 1 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Post 1 Hour"]].astype(numpy.dtypes.Float64DType())
    df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_da_expost_str_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
    ).iloc[:-1]
        
    df = df.rename(columns={idx: f"Reserve Zone {idx}" for idx in range(1, 9)})

    df[["Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8"]] = df[["Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8"]].astype(numpy.dtypes.Float64DType())
    df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_rt_expost_ramp_5min_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=6,
    ).iloc[:-1]
        
    df.columns = pd.Index([
        "Time (EST)", 
        "Preliminary / Final"
    ] + [
        f"Reserve Zone {zone_num} - {direction}" 
        for zone_num in range(1, 9) 
        for direction in ["RT MCP Ramp Up Ex-Post 5 Min", "RT MCP Ramp Down Ex-Post 5 Min"]
    ])

    df[["Reserve Zone 1 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post 5 Min"]] = df[["Reserve Zone 1 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post 5 Min"]].astype(numpy.dtypes.Float64DType())
    df[["Time (EST)"]] = df[["Time (EST)"]].apply(pd.to_datetime, format="%m/%d/%Y  %I:%M:%S %p")
    df[["Preliminary / Final"]] = df[["Preliminary / Final"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_rt_expost_ramp_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
    ).iloc[:-1]
        
    df.columns = pd.Index([
        "Market Date", 
        "Hour Ending", 
        "Preliminary / Final"
    ] + [
        f"Reserve Zone {zone_num} - {direction}" 
        for zone_num in range(1, 9) 
        for direction in ["RT MCP Ramp Up Ex-Post Hourly", "RT MCP Ramp Down Ex-Post Hourly"]
    ])

    df[["Reserve Zone 1 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post Hourly"]] = df[["Reserve Zone 1 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post Hourly"]].astype(numpy.dtypes.Float64DType())
    df[["Market Date"]] = df[["Market Date"]].apply(pd.to_datetime, format="%Y-%m-%d")
    df[["Preliminary / Final"]] = df[["Preliminary / Final"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_rt_expost_str_5min_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
    ).iloc[:-1]
        
    df = df.rename(columns={idx: f"RESERVE ZONE {idx}" for idx in range(1, 9)})
    df = df.drop(columns=["Unnamed: 0"])

    df[["RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8"]] = df[["RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8"]].astype(numpy.dtypes.Float64DType())
    df[["Time(EST)"]] = df[["Time(EST)"]].apply(pd.to_datetime, format="%m/%d/%Y  %I:%M:%S %p")
    df[["Preliminary/ Final"]] = df[["Preliminary/ Final"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_rt_expost_str_mcp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
    ).iloc[:-1]
        
    df = df.rename(columns={idx: f"RESERVE ZONE {idx}" for idx in range(1, 9)})

    df[["RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8"]] = df[["RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8"]].astype(numpy.dtypes.Float64DType())
    df[["MARKET DATE"]] = df[["MARKET DATE"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["Preliminary/ Final"]] = df[["Preliminary/ Final"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_Allocation_on_MISO_Flowgates(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[:-2])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
        thousands=",",
    )

    df[["Allocation (MW)"]] = df[["Allocation (MW)"]].astype(numpy.dtypes.Float64DType())
    df[["Allocation to Rating Percentage"]] = df[["Allocation to Rating Percentage"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["NERC ID", "Flowgate Owner", "Flowgate Description", "Entity", "Direction", "Reciprocal Status on Flowgate"]] = df[["NERC ID", "Flowgate Owner", "Flowgate Description", "Entity", "Direction", "Reciprocal Status on Flowgate"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_M2M_FFE(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[:-1])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
        thousands=",",
    )

    df[["Adjusted FFE", "Non Monitoring RTO FFE"]] = df[["Adjusted FFE", "Non Monitoring RTO FFE"]].astype(numpy.dtypes.Float64DType())
    df[["NERC Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description"]] = df[["NERC Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Hour Ending"]] = df[["Hour Ending"]].apply(pd.to_datetime, format="%m/%d/%Y  %I:%M:%S %p")

    return df


def parse_M2M_Flowgates_as_of(
    res: requests.Response,
) -> pd.DataFrame:
    csv_data = res.text

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description"]] = df[["Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_da_M2M_Settlement_srw(
    res: requests.Response,
) -> pd.DataFrame:
    raise NotImplementedError("As of 2024-11-19, not a single non-empty report was published yet.")


def parse_M2M_Settlement_srw(
    res: requests.Response,
) -> pd.DataFrame:
    csv_data = res.text

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df["HOUR_ENDING"] = [(datetime.datetime.strptime(dtime.replace(" 24:00:00", " 00:00:00"), "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S") if dtime.endswith("24:00:00") else dtime for dtime in df["HOUR_ENDING"]]
    
    df[["MISO_SHADOW_PRICE", "CP_SHADOW_PRICE", "MISO_CREDIT", "CP_CREDIT"]] = df[["MISO_SHADOW_PRICE", "CP_SHADOW_PRICE", "MISO_CREDIT", "CP_CREDIT"]].astype(numpy.dtypes.Float64DType())
    df[["FLOWGATE_ID", "MONITORING_RTO", "CP_RTO", "FLOWGATE_NAME"]] = df[["FLOWGATE_ID", "MONITORING_RTO", "CP_RTO", "FLOWGATE_NAME"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["MISO_MKT_FLOW", "MISO_FFE", "CP_MKT_FLOW", "CP_FFE"]] = df[["MISO_MKT_FLOW", "MISO_FFE", "CP_MKT_FLOW", "CP_FFE"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["HOUR_ENDING"]] = df[["HOUR_ENDING"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")

    return df


def parse_MM_Annual_Report(
    res: requests.Response,
) -> pd.DataFrame:
        with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
            annual_files = z.namelist()[:-1]
            transparency_file = z.namelist()[-1]

            annual_content = [z.read(content) for content in annual_files]

            cur_year = int(transparency_file.rsplit("_")[-1][:4])
            transparency_content = z.read(transparency_file)

        df_names = []
        dfs = []

        for xlsx, name in zip(annual_content, annual_files):
            region = name.split('_')[-1][:-5]

            for idx, sheet  in enumerate(f"GraphDataAnnual{region}_{year}" for year in range(cur_year, cur_year + 4)):
                df = pd.read_excel(
                    io=io.BytesIO(xlsx),
                    skiprows=3,
                    skipfooter=1,
                    sheet_name=sheet,
                )

                df[[f"{region} Available Margin (MW)"]] = df[[f"{region} Available Margin (MW)"]].astype(numpy.dtypes.Float64DType())
                df[["Date"]] = df[["Date"]].apply(pd.to_datetime, format="%m/%d/%Y")

                dfs.append(df)
                df_names.append(f"{region} Year {idx + 1}")

        for sheet in ("Future", "History"):

            df_transparency = pd.read_excel(
                io=io.BytesIO(transparency_content),
                skiprows=3,
                skipfooter=1,
                sheet_name=sheet,
            )

            df_transparency[["Central Region (MW)", "North Region (MW)", "South Region (MW)"]] = df_transparency[["Central Region (MW)", "North Region (MW)", "South Region (MW)"]].astype(numpy.dtypes.Float64DType())
            df_transparency[["Date"]] = df_transparency[["Date"]].apply(pd.to_datetime, format="%m/%d/%Y %I:%M:%S %p")

            dfs.append(df_transparency)
            df_names.append(f"Transparency {sheet}")
        
        df = pd.DataFrame(data={
            MULTI_DF_NAMES_COLUMN: df_names, 
            MULTI_DF_DFS_COLUMN: dfs,
        })

        return df


def parse_asm_da_co(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        csv_data = z.read(z.namelist()[0]).decode("utf-8")

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP", "RegMW", "SpinMCP", "SpinMW", "SuppMCP", "SuppMW", "OfflineSTR", "STRMCP", "STRMW", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel"]] = df[["RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP", "RegMW", "SpinMCP", "SpinMW", "SuppMCP", "SuppMW", "OfflineSTR", "STRMCP", "STRMW", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel"]].astype(numpy.dtypes.Float64DType())
    df[["Date/Time Beginning (EST)", "Date/Time End (EST)"]] = df[["Date/Time Beginning (EST)", "Date/Time End (EST)"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
    df[["Region", "Unit Code"]] = df[["Region", "Unit Code"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_asm_rt_co(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        csv_data = z.read(z.namelist()[0]).decode("utf-8")

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP1", "RegMW1", "RegMCP2", "RegMW2", "RegMCP3", "RegMW3", "RegMCP4", "RegMW4", "RegMCP5", "RegMW5", "RegMCP6", "RegMW6", "RegMCP7", "RegMW7", "RegMCP8", "RegMW8", "RegMCP9", "RegMW9", "RegMCP10", "RegMW10", "RegMCP11", "RegMW11", "RegMCP12", "RegMW12", "SpinMCP1", "SpinMW1", "SpinMCP2", "SpinMW2", "SpinMCP3", "SpinMW3", "SpinMCP4", "SpinMW4", "SpinMCP5", "SpinMW5", "SpinMCP6", "SpinMW6", "SpinMCP7", "SpinMW7", "SpinMCP8", "SpinMW8", "SpinMCP9", "SpinMW9", "SpinMCP10", "SpinMW10", "SpinMCP11", "SpinMW11", "SpinMCP12", "SpinMW12", "SuppMCP1", "SuppMW1", "SuppMCP2", "SuppMW2", "SuppMCP3", "SuppMW3", "SuppMCP4", "SuppMW4", "SuppMCP5", "SuppMW5", "SuppMCP6", "SuppMW6", "SuppMCP7", "SuppMW7", "SuppMCP8", "SuppMW8", "SuppMCP9", "SuppMW9", "SuppMCP10", "SuppMW10", "SuppMCP11", "SuppMW11", "SuppMCP12", "SuppMW12", "StrOfflineOfferRate", "STRMCP1", "STRMW1", "STRMCP2", "STRMW2", "STRMCP3", "STRMW3", "STRMCP4", "STRMW4", "STRMCP5", "STRMW5", "STRMCP6", "STRMW6", "STRMCP7", "STRMW7", "STRMCP8", "STRMW8", "STRMCP9", "STRMW9", "STRMCP10", "STRMW10", "STRMCP11", "STRMW11", "STRMCP12", "STRMW12", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel"]] = df[["RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP1", "RegMW1", "RegMCP2", "RegMW2", "RegMCP3", "RegMW3", "RegMCP4", "RegMW4", "RegMCP5", "RegMW5", "RegMCP6", "RegMW6", "RegMCP7", "RegMW7", "RegMCP8", "RegMW8", "RegMCP9", "RegMW9", "RegMCP10", "RegMW10", "RegMCP11", "RegMW11", "RegMCP12", "RegMW12", "SpinMCP1", "SpinMW1", "SpinMCP2", "SpinMW2", "SpinMCP3", "SpinMW3", "SpinMCP4", "SpinMW4", "SpinMCP5", "SpinMW5", "SpinMCP6", "SpinMW6", "SpinMCP7", "SpinMW7", "SpinMCP8", "SpinMW8", "SpinMCP9", "SpinMW9", "SpinMCP10", "SpinMW10", "SpinMCP11", "SpinMW11", "SpinMCP12", "SpinMW12", "SuppMCP1", "SuppMW1", "SuppMCP2", "SuppMW2", "SuppMCP3", "SuppMW3", "SuppMCP4", "SuppMW4", "SuppMCP5", "SuppMW5", "SuppMCP6", "SuppMW6", "SuppMCP7", "SuppMW7", "SuppMCP8", "SuppMW8", "SuppMCP9", "SuppMW9", "SuppMCP10", "SuppMW10", "SuppMCP11", "SuppMW11", "SuppMCP12", "SuppMW12", "StrOfflineOfferRate", "STRMCP1", "STRMW1", "STRMCP2", "STRMW2", "STRMCP3", "STRMW3", "STRMCP4", "STRMW4", "STRMCP5", "STRMW5", "STRMCP6", "STRMW6", "STRMCP7", "STRMW7", "STRMCP8", "STRMW8", "STRMCP9", "STRMW9", "STRMCP10", "STRMW10", "STRMCP11", "STRMW11", "STRMCP12", "STRMW12", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel"]].astype(numpy.dtypes.Float64DType())
    df[["Mkthour Begin (EST)"]] = df[["Mkthour Begin (EST)"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
    df[["Region", "Unit Code"]] = df[["Region", "Unit Code"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_Dead_Node_Report(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=9,
        usecols='B:C',
    ).iloc[:-3]

    df = df.rename(columns={"Unnamed: 1": "Mkt Hour", "Unnamed: 2": "PNODE Name"})
    df = df.dropna()
    
    df = df[df["Mkt Hour"] != "\n\nMkt Hour"]
    df = df.reset_index(drop=True)

    df[["Mkt Hour"]] = df[["Mkt Hour"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
    df[["PNODE Name"]] = df[["PNODE Name"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_rt_co(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        csv_data = z.read(z.namelist()[0]).decode("utf-8")

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data), 
    )

    df[["Cleared MW1", "Cleared MW2", "Cleared MW3", "Cleared MW4", "Cleared MW5", "Cleared MW6", "Cleared MW7", "Cleared MW8", "Cleared MW9", "Cleared MW10", "Cleared MW11", "Cleared MW12", "Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel"]] = df[["Cleared MW1", "Cleared MW2", "Cleared MW3", "Cleared MW4", "Cleared MW5", "Cleared MW6", "Cleared MW7", "Cleared MW8", "Cleared MW9", "Cleared MW10", "Cleared MW11", "Cleared MW12", "Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel"]].astype(numpy.dtypes.Float64DType())
    df[["Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope"]] = df[["Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Mkthour Begin (EST)"]] = df[["Mkthour Begin (EST)"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
    df[["Region", "Unit Code"]] = df[["Region", "Unit Code"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_da_co(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        csv_data = z.read(z.namelist()[0]).decode("utf-8")

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data), 
    )

    df[["Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "MW", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel"]] = df[["Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "MW", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel"]].astype(numpy.dtypes.Float64DType())
    df[["Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope"]] = df[["Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Date/Time Beginning (EST)", "Date/Time End (EST)"]] = df[["Date/Time Beginning (EST)", "Date/Time End (EST)"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
    df[["Region", "Unit Code"]] = df[["Region", "Unit Code"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_cpnode_reszone(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    ).iloc[:-1]

    df[["Reserve Zone"]] = df[["Reserve Zone"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["CP Node Name"]] = df[["CP Node Name"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_sr_ctsl(
    res: requests.Response,
) -> pd.DataFrame:
    import pdfplumber # Importing here because this is the only parser that needs this.

    with pdfplumber.open(io.BytesIO(res.content)) as pdf:
        pg = pdf.pages[0]

        bounding_box = (0, pg.height / 8, pg.width, (pg.height * 3) / 4)
        pg = pg.crop(bounding_box, relative=True)

        tables = pg.extract_tables(table_settings={
            "vertical_strategy": "explicit",
            "horizontal_strategy": "text",
            "snap_tolerance": 4,
            "explicit_vertical_lines": [18.9, 299.71666666666664, 355.80000000000007, 411.80000000000007, 467.80000000000007, 523.8000000000001, 579.8000000000001, 635.8000000000001, 691.8000000000001, 747.8000000000001, 803.8000000000001, 859.8000000000001, 915.8000000000001, 973.7833333333333],
            "intersection_x_tolerance": 10,
        })
    
    if not tables:
        raise ValueError("Unexpected: no tables file found in PDF.")

    try:
        divider = tables[0].index(["" for i in range(13)])
    except ValueError:
        raise ValueError("Unexpected: no table delimiter found in PDF.")
    
    tables = [tables[0][:divider], tables[0][divider + 1:]]

    df_names = []
    dfs = []

    for table in tables:
        df = pd.DataFrame(
            data=table[1:], 
            columns=table[0],
        )
        
        year = df.columns[-1].split()[-1]

        df[["Cost Paid by Load (Hourly Avg per Month)"]] = df[["Cost Paid by Load (Hourly Avg per Month)"]].astype(pandas.core.arrays.string_.StringDtype())
        df[[f"Jan {year}", f"Feb {year}", f"Mar {year}", f"Apr {year}", f"May {year}", f"Jun {year}", f"Jul {year}", f"Aug {year}", f"Sep {year}", f"Oct {year}", f"Nov {year}", f"Dec {year}"]] = df[[f"Jan {year}", f"Feb {year}", f"Mar {year}", f"Apr {year}", f"May {year}", f"Jun {year}", f"Jul {year}", f"Aug {year}", f"Sep {year}", f"Oct {year}", f"Nov {year}", f"Dec {year}"]].replace(r'[\$,()]', '', regex=True).replace(r'^\s*$', np.nan, regex=True).astype(numpy.dtypes.Float64DType())

        dfs.append(df)
        df_names.append(f"Cost Paid by Load - {year}")

    df = pd.DataFrame(data={
        MULTI_DF_NAMES_COLUMN: df_names, 
        MULTI_DF_DFS_COLUMN: dfs,
    })
    
    return df


def parse_df_al(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
    ).iloc[:-1]

    df = df[df["Market Day"] != "Market Day"]
    df = df[df["HourEnding"].notna()]
    df = df.reset_index(drop=True)
    df[["HourEnding"]] = df[["HourEnding"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["LRZ1 MTLF (MWh)", "LRZ1 ActualLoad (MWh)", "LRZ2_7 MTLF (MWh)", "LRZ2_7 ActualLoad (MWh)", "LRZ3_5 MTLF (MWh)", "LRZ3_5 ActualLoad (MWh)", "LRZ4 MTLF (MWh)", "LRZ4 ActualLoad (MWh)", "LRZ6 MTLF (MWh)", "LRZ6 ActualLoad (MWh)", "LRZ8_9_10 MTLF (MWh)", "LRZ8_9_10 ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)"]] = df[["LRZ1 MTLF (MWh)", "LRZ1 ActualLoad (MWh)", "LRZ2_7 MTLF (MWh)", "LRZ2_7 ActualLoad (MWh)", "LRZ3_5 MTLF (MWh)", "LRZ3_5 ActualLoad (MWh)", "LRZ4 MTLF (MWh)", "LRZ4 ActualLoad (MWh)", "LRZ6 MTLF (MWh)", "LRZ6 ActualLoad (MWh)", "LRZ8_9_10 MTLF (MWh)", "LRZ8_9_10 ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)"]].astype(numpy.dtypes.Float64DType())
    df[["Market Day"]] = df[["Market Day"]].apply(pd.to_datetime, format="%m/%d/%Y")

    return df


def parse_rf_al(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
        usecols='B:K',
    ).iloc[:-3]

    df = df.dropna(how="all")
    df = df[df["Market Day"] != "Market Day"]
    df = df.reset_index(drop=True)
    df[["HourEnding"]] = df[["HourEnding"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["North MTLF (MWh)", "North ActualLoad (MWh)", "Central MTLF (MWh)", "Central ActualLoad (MWh)", "South MTLF (MWh)", "South ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)"]] = df[["North MTLF (MWh)", "North ActualLoad (MWh)", "Central MTLF (MWh)", "Central ActualLoad (MWh)", "South MTLF (MWh)", "South ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)"]].astype(numpy.dtypes.Float64DType())
    df[["Market Day"]] = df[["Market Day"]].apply(pd.to_datetime, format="%m/%d/%Y")

    return df


def parse_da_bc_HIST(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[2:-3])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
        low_memory=False,
    )

    df["Shadow Price"] = df["Shadow Price"].replace({
        r"\(\$": "-",
        r"\$": "",
        r"\)": "",
    }, regex=True)

    df[["Shadow Price", "BP1", "PC1", "BP2", "PC2"]] = df[["Shadow Price", "BP1", "PC1", "BP2", "PC2"]].astype(numpy.dtypes.Float64DType())
    df[["Hour of Occurrence", "Override"]] = df[["Hour of Occurrence", "Override"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Market Date"]] = df[["Market Date"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["Constraint Name", "Constraint_ID", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]] = df[["Constraint Name", "Constraint_ID", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_da_ex_rg(
    res: requests.Response,
) -> pd.DataFrame:
    sheet_names = ["Summary", "Regional Level"]
    dfs = []

    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=6,
        sheet_name=sheet_names[0],
    ).iloc[:-1]

    df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total"]] = df[["Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total"]].astype(numpy.dtypes.Float64DType())

    dfs.append(df)

    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=6,
        sheet_name=sheet_names[1],
    ).iloc[:-1]
    
    df.dropna(subset=['Region'], inplace=True)

    last_value = None
    filled_column = []

    for val in df["Hour Ending"]:
        if pd.notna(val):
            last_value = val

        filled_column.append(last_value)

    df["Hour Ending"] = filled_column

    df[["Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total"]] = df[["Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total"]].astype(numpy.dtypes.Float64DType())
    df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Region"]] = df[["Region"]].astype(pandas.core.arrays.string_.StringDtype())

    dfs.append(df)

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: sheet_names, 
        MULTI_DF_DFS_COLUMN: dfs,
    })

    return df


def parse_da_ex(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
    )

    df.rename(columns={"Unnamed: 0": "Hour"}, inplace=True)
    df[["Hour"]] = df[["Hour"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total"]] = df[["Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total"]].astype(numpy.dtypes.Float64DType())
    
    return df


def parse_da_rpe(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    )[:-1]

    df[["Hour of Occurence"]] = df[["Hour of Occurence"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Constraint Name", "Constraint Description"]] = df[["Constraint Name", "Constraint Description"]].astype(pandas.core.arrays.string_.StringDtype())
    df[["Shadow Price"]] = df[["Shadow Price"]].astype(numpy.dtypes.Float64DType())
    
    return df


def parse_RT_LMPs(
    res: requests.Response,
) -> pd.DataFrame:
    with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
        text = z.read(z.namelist()[0]).decode("utf-8")

    csv_data = "\n".join(text.splitlines()[1:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
        thousands=",",
    )

    df[["MARKET_DAY"]] = df[["MARKET_DAY"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
    df[["NODE", "TYPE", "VALUE"]] = df[["NODE", "TYPE", "VALUE"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_sr_gfm(
    res: requests.Response,
) -> pd.DataFrame:
    MarketHourColumn = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="A",
    )[:-1]

    MarketHourColumn["Market Hour Ending"] = MarketHourColumn["Market Hour Ending"].astype(pandas.core.arrays.string_.StringDtype())

    df1 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="B:J",
        sheet_name="RT Generation Fuel Mix",
    )[:-1]
    shared_column_names = list(df1.columns)[:-2]

    df1[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]] = df1[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]].astype(numpy.dtypes.Float64DType())
    
    df2 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="L:T",
        sheet_name="RT Generation Fuel Mix",
        names=shared_column_names + ["Storage", "Total MW"],
    )[:-1]

    df2[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]] = df2[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]].astype(numpy.dtypes.Float64DType())

    df3 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="V:AC",
        sheet_name="RT Generation Fuel Mix",
        names=shared_column_names + ["Total MW"],
    )[:-1]

    df3[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW"]] = df3[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW"]].astype(numpy.dtypes.Float64DType())

    df4 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="AG:AO",
        sheet_name="RT Generation Fuel Mix",
        names=shared_column_names + ["Storage", "MISO"],
    )[:-1]

    df4[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO"]] = df4[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO"]].astype(numpy.dtypes.Float64DType())

    df5 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="B:J",
        sheet_name="DA Cleared Generation Fuel Mix",
        names=shared_column_names + ["Storage", "Total MW"],
    )[:-1]

    df5[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]] = df5[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]].astype(numpy.dtypes.Float64DType())

    df6 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="L:T",
        sheet_name="DA Cleared Generation Fuel Mix",
        names=shared_column_names + ["Storage", "Total MW"],
    )[:-1]

    df6[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]] = df6[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]].astype(numpy.dtypes.Float64DType())

    df7 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="V:AC",
        sheet_name="DA Cleared Generation Fuel Mix",
        names=shared_column_names + ["Total MW"],
    )[:-1]

    df7[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW"]] = df7[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW"]].astype(numpy.dtypes.Float64DType())

    df8 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="AG:AO",
        sheet_name="DA Cleared Generation Fuel Mix",
        names=shared_column_names + ["Storage", "MISO"],
    )[:-1]

    df8[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO"]] = df8[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO"]].astype(numpy.dtypes.Float64DType())


    df_list = [df1, df2, df3, df4, df5, df6, df7, df8]

    for df in df_list:
        df.insert(
            loc=0,
            column="Market Hour Ending",
            value=MarketHourColumn["Market Hour Ending"],
        )

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                "RT Generation Fuel Mix Central",
                "RT Generation Fuel Mix North",
                "RT Generation Fuel Mix South",
                "RT Generation Fuel Mix Totals",
                "DA Cleared Generation Fuel Mix Central",
                "DA Cleared Generation Fuel Mix North",
                "DA Cleared Generation Fuel Mix South",
                "DA Cleared Generation Fuel Mix Totals",
        ], 
        MULTI_DF_DFS_COLUMN: [
                df1, 
                df2,
                df3,
                df4,
                df5,
                df6,
                df7,
                df8,
        ],
    })

    return df


def parse_dfal_HIST(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
    )[:-2]

    df = df[df["MarketDay"] != "MarketDay"]
    df = df.reset_index(drop=True)
    df[["HourEnding"]] = df[["HourEnding"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["MarketDay"]] = df[["MarketDay"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["MTLF (MWh)", "ActualLoad (MWh)"]] = df[["MTLF (MWh)", "ActualLoad (MWh)"]].astype(numpy.dtypes.Float64DType())
    df[["LoadResource Zone"]] = df[["LoadResource Zone"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_historical_gen_fuel_mix(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="B:G",
    )

    df[["HourEnding"]] = df[["HourEnding"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Market Date"]] = df[["Market Date"]].apply(pd.to_datetime, format="%Y-%m-%d")
    df[["DA Cleared UDS Generation", "[RT Generation State Estimator"]] = df[["DA Cleared UDS Generation", "[RT Generation State Estimator"]].astype(numpy.dtypes.Float64DType())
    df[["Region", "Fuel Type"]] = df[["Region", "Fuel Type"]].astype(pandas.core.arrays.string_.StringDtype())
    
    return df


def parse_hwd_HIST(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[7:-1])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Market Day	"]] = df[["Market Day	"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["MWh"]] = df[["MWh"]].astype(numpy.dtypes.Float64DType())

    return df


def parse_sr_hist_is(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[1:-2])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
        sep="|",
    )

    df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["MKTDAY"]] = df[["MKTDAY"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["INTERFACE"]] = df[["INTERFACE"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_rfal_HIST(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        usecols="B:G",
    )[:-4]

    df[["HourEnding"]] = df[["HourEnding"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Market Day"]] = df[["Market Day"]].apply(pd.to_datetime, format="%m/%d/%Y")
    df[["MTLF (MWh)", "Actual Load (MWh)"]] = df[["MTLF (MWh)", "Actual Load (MWh)"]].astype(numpy.dtypes.Float64DType())
    df[["Region", "Footnote"]] = df[["Region", "Footnote"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_sr_lt(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    )

    df[["Minimum (GW)", "Average (GW)", "Maximum (GW)"]] = df[["Minimum (GW)", "Average (GW)", "Maximum (GW)"]].astype(numpy.dtypes.Float64DType())
    df[["Week Starting"]] = df[["Week Starting"]].apply(pd.to_datetime)
    
    return df


def parse_sr_la_rg(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    delimiter_index = text.rfind(",,,,,,,,,,,,,,,")

    csv_data1 = "\n".join(text[:delimiter_index].splitlines()[3:])
    csv_data2 = "\n".join(text[delimiter_index:].splitlines()[1:-1])

    df1 = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data1),
    )

    df1 = df1.dropna()
    df1 = df1.reset_index(drop=True)
    df1[["10/24/2024 Thursday Peak Hour: HE  19 MTLF (GW)", "10/24/2024 Thursday Peak Hour: HE  19 Capacity on Outage (GW)", "10/25/2024 Friday   Peak Hour: HE  16 MTLF (GW)", "10/25/2024 Friday   Peak Hour: HE  16 Capacity on Outage (GW)", "10/26/2024 Saturday Peak Hour: HE  19 MTLF (GW)", "10/26/2024 Saturday Peak Hour: HE  19 Capacity on Outage (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 MTLF (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 Capacity on Outage (GW)", "10/28/2024 Monday   Peak Hour: HE  19 MTLF (GW)", "10/28/2024 Monday   Peak Hour: HE  19Capacity on Outage (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 MTLF (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 Capacity on Outage (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 MTLF (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 Capacity on Outage (GW)"]] = df1[["10/24/2024 Thursday Peak Hour: HE  19 MTLF (GW)", "10/24/2024 Thursday Peak Hour: HE  19 Capacity on Outage (GW)", "10/25/2024 Friday   Peak Hour: HE  16 MTLF (GW)", "10/25/2024 Friday   Peak Hour: HE  16 Capacity on Outage (GW)", "10/26/2024 Saturday Peak Hour: HE  19 MTLF (GW)", "10/26/2024 Saturday Peak Hour: HE  19 Capacity on Outage (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 MTLF (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 Capacity on Outage (GW)", "10/28/2024 Monday   Peak Hour: HE  19 MTLF (GW)", "10/28/2024 Monday   Peak Hour: HE  19Capacity on Outage (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 MTLF (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 Capacity on Outage (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 MTLF (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 Capacity on Outage (GW)"]].astype(numpy.dtypes.Float64DType())
    df1[["Region"]] = df1[["Region"]].astype(pandas.core.arrays.string_.StringDtype())
    df1["Hourend_EST"] = df1["Hourend_EST"].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())

    df2_columns = ["Type"] + list(df1.columns)[1:]
    df2 = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data2),
        names=df2_columns,
        header=None,
    )
    df2[["10/24/2024 Thursday Peak Hour: HE  19 MTLF (GW)", "10/24/2024 Thursday Peak Hour: HE  19 Capacity on Outage (GW)", "10/25/2024 Friday   Peak Hour: HE  16 MTLF (GW)", "10/25/2024 Friday   Peak Hour: HE  16 Capacity on Outage (GW)", "10/26/2024 Saturday Peak Hour: HE  19 MTLF (GW)", "10/26/2024 Saturday Peak Hour: HE  19 Capacity on Outage (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 MTLF (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 Capacity on Outage (GW)", "10/28/2024 Monday   Peak Hour: HE  19 MTLF (GW)", "10/28/2024 Monday   Peak Hour: HE  19Capacity on Outage (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 MTLF (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 Capacity on Outage (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 MTLF (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 Capacity on Outage (GW)"]] = df2[["10/24/2024 Thursday Peak Hour: HE  19 MTLF (GW)", "10/24/2024 Thursday Peak Hour: HE  19 Capacity on Outage (GW)", "10/25/2024 Friday   Peak Hour: HE  16 MTLF (GW)", "10/25/2024 Friday   Peak Hour: HE  16 Capacity on Outage (GW)", "10/26/2024 Saturday Peak Hour: HE  19 MTLF (GW)", "10/26/2024 Saturday Peak Hour: HE  19 Capacity on Outage (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 MTLF (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 Capacity on Outage (GW)", "10/28/2024 Monday   Peak Hour: HE  19 MTLF (GW)", "10/28/2024 Monday   Peak Hour: HE  19Capacity on Outage (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 MTLF (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 Capacity on Outage (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 MTLF (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 Capacity on Outage (GW)"]].astype(numpy.dtypes.Float64DType())
    df2[["Type", "Region"]] = df2[["Type", "Region"]].astype(pandas.core.arrays.string_.StringDtype())

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
            "Table 1",
            "Table 2",
        ],
        MULTI_DF_DFS_COLUMN: [
            df1,
            df2,
        ],
    })

    return df


def parse_mom(
    res: requests.Response,
) -> pd.DataFrame:
    time_6 = [f"Day {i}" for i in range(1, 7)]
    time_7 = [f"Day {i}" for i in range(1, 8)]
    time_30 = [f"Day {i}" for i in range(1, 31)]
    df_time_6 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        nrows=1,
        sheet_name="MISO",
        usecols="B:G",
        names=time_6,
    )

    df_time_6[time_6] = df_time_6[time_6].astype(pandas.core.arrays.string_.StringDtype())

    df_time_7 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
        nrows=1,
        sheet_name="OUTAGE",
        usecols="C:I",
        names=time_7,
    )

    df_time_7[time_7] = df_time_7[time_7].astype(pandas.core.arrays.string_.StringDtype())

    df_time_30 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=25,
        nrows=1,
        sheet_name="OUTAGE",
        usecols="C:AF",
        names=time_30,
    )

    df_time_30[time_30] = df_time_30[time_30].astype(pandas.core.arrays.string_.StringDtype())

    df1 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=5,
        sheet_name="MISO",
        names= ["Resources"] + time_6,
    )[:-4]
    
    df1 = df1.dropna(how="all").reset_index(drop=True)
    df1[time_6] = df1[time_6].astype(numpy.dtypes.Float64DType())
    df1[["Resources"]] = df1[["Resources"]].astype(pandas.core.arrays.string_.StringDtype())

    df2 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        sheet_name="NORTH",
        names= ["Resources"] + time_6,
    )[:-4]
    
    df2 = df2.dropna(how="all").reset_index(drop=True)
    df2[time_6] = df2[time_6].astype(numpy.dtypes.Float64DType())
    df2[["Resources"]] = df2[["Resources"]].astype(pandas.core.arrays.string_.StringDtype())

    df3 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        sheet_name="CENTRAL",
        names= ["Resources"] + time_6,
    )[:-4]
    
    df3 = df3.dropna(how="all").reset_index(drop=True)
    df3[time_6] = df3[time_6].astype(numpy.dtypes.Float64DType())
    df3[["Resources"]] = df3[["Resources"]].astype(pandas.core.arrays.string_.StringDtype())

    df4 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        sheet_name="NORTH+CENTRAL",
        names= ["Resources"] + time_6,
    )[:-4]
    
    df4 = df4.dropna(how="all").reset_index(drop=True)
    df4[time_6] = df4[time_6].replace(',','', regex=True).astype(numpy.dtypes.Float64DType())
    df4[["Resources"]] = df4[["Resources"]].astype(pandas.core.arrays.string_.StringDtype())

    df5 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        sheet_name="SOUTH",
        names= ["Resources"] + time_6,
    )[:-4]
    
    df5 = df5.dropna(how="all").reset_index(drop=True)
    df5[time_6] = df5[time_6].replace(',','', regex=True).astype(numpy.dtypes.Float64DType())
    df5[["Resources"]] = df5[["Resources"]].astype(pandas.core.arrays.string_.StringDtype())

    df6 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        sheet_name="SOLAR HOURLY",
    )[:-2]

    df6[["North", "Central", "South", "MISO"]] = df6[["North", "Central", "South", "MISO"]].astype(numpy.dtypes.Float64DType())
    df6[["DAY HE"]] = df6[["DAY HE"]].astype(pandas.core.arrays.string_.StringDtype())

    df7 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        sheet_name="WIND HOURLY",
    )[:-2]

    df7[["North", "Central", "South", "MISO"]] = df7[["North", "Central", "South", "MISO"]].astype(numpy.dtypes.Float64DType())
    df7[["DAY HE"]] = df7[["DAY HE"]].astype(pandas.core.arrays.string_.StringDtype())

    df8 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        sheet_name="WIND UNCERTAINTY",
        names=["Wind Uncertainty"] + time_6
    )[:-3]

    df8[time_6] = df8[time_6].astype(numpy.dtypes.Float64DType())
    df8.loc[4,"Wind Uncertainty"] = "Standard Deviation Percentage"
    df8.loc[5,"Wind Uncertainty"] = "Standard Deviation in MW"
    df8[["Wind Uncertainty"]] = df8[["Wind Uncertainty"]].astype(pandas.core.arrays.string_.StringDtype())

    df9 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=4,
        sheet_name="LOAD UNCERTAINTY",
        names=["Load Uncertainty"] + time_6
    )[:-3]

    df9[time_6] = df9[time_6].astype(numpy.dtypes.Float64DType())
    df9.loc[3,"Load Uncertainty"] = "Standard Deviation Percentage"
    df9.loc[4,"Load Uncertainty"] = "Standard Deviation in MW"
    df9[["Load Uncertainty"]] = df9[["Load Uncertainty"]].astype(pandas.core.arrays.string_.StringDtype())

    df10 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=6,
        nrows=17,
        sheet_name="OUTAGE",
        names= ["Location", "Type"] + time_7,
    )
    
    df10[time_7] = df10[time_7].astype(numpy.dtypes.Float64DType())
    df10[["Location", "Type"]] = df10[["Location", "Type"]].astype(pandas.core.arrays.string_.StringDtype())

    df11 = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=26,
        sheet_name="OUTAGE",
        names= ["Location", "Type"] + time_30,
    )[:-3]
    
    df11[time_30] = df11[time_30].astype(numpy.dtypes.Float64DType())
    df11[["Location", "Type"]] = df11[["Location", "Type"]].astype(pandas.core.arrays.string_.StringDtype())

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                "6 DAYS AHEAD DATES",
                "MISO",
                "NORTH",
                "CENTRAL",
                "NORTH+CENTRAL",
                "SOUTH",
                "SOLAR HOURLY",
                "WIND HOURLY",
                "WIND UNCERTAINTY",
                "LOAD UNCERTAINTY",
                "7 DAYS AHEAD DATES",
                "OUTAGE 7-DAY LOOK-AHEAD",
                "30 DAYS BACK DATES",
                "OUTAGE 30-DAY LOOK-BACK",
        ], 
        MULTI_DF_DFS_COLUMN: [
                df_time_6,
                df1, 
                df2,
                df3,
                df4,
                df5,
                df6,
                df7,
                df8,
                df9,
                df_time_7,
                df10,
                df_time_30,
                df11,
        ],
    })

    return df


def parse_sr_nd_is(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=10,
        usecols="B:R"
    )[:-11]
    
    df.rename(
        columns={
            "Unnamed: 1": "Hour",
        }, 
        inplace=True,
    )

    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df["Hour"] = df["Hour"].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
    df[["GLHB", "IESO", "MHEB", "PJM", "SOCO", "SWPP", "TVA", "AECI", "LGEE", "Other", "Total"]] = df[["GLHB", "IESO", "MHEB", "PJM", "SOCO", "SWPP", "TVA", "AECI", "LGEE", "Other", "Total"]].astype(pandas.core.arrays.integer.Int64Dtype())

    return df


def parse_PeakHourOverview(
    res: requests.Response,
) -> pd.DataFrame:
    def handle_table(
        data_lines: list[str],
    ) -> pd.DataFrame:
        clean_data_lines = [line.lstrip("(+)").lstrip() for line in data_lines]
        
        data = {}
        for line in clean_data_lines:
            key, value = line.split(",")
            data[key] = [value]
        
        df = pd.DataFrame(data, dtype=pandas.core.arrays.integer.Int64Dtype())

        return df

    text = res.text

    data_lines_1 = text.splitlines()[4:8]
    data_lines_2 = text.splitlines()[9:13]

    df1 = handle_table(data_lines_1)
    df2 = handle_table(data_lines_2)

    df = pd.DataFrame({
        MULTI_DF_NAMES_COLUMN: [
                "SYSTEM RESOURCE CAPACITY",
                "SYSTEM OBLIGATION",
        ], 
        MULTI_DF_DFS_COLUMN: [
                df1, 
                df2, 
        ],
    })

    return df


def parse_sr_tcdc_group2(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[4:-2])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["EffectiveTime", "TerminationTime"]] = df[["EffectiveTime", "TerminationTime"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
    df[["BP1", "PC1", "BP2", "PC2"]] = df[["BP1", "PC1", "BP2", "PC2"]].astype(numpy.dtypes.Float64DType())
    df[["ContingencyName", "ContingencyDescription", "BranchName", "CurveName", "Reason"]] = df[["ContingencyName", "ContingencyDescription", "BranchName", "CurveName", "Reason"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def helper_parse_market_report_xml(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
                
    element_tree = ET.fromstring(text)
    product = element_tree.find("Product")
    account_header = product.find("AccountHeader") # type: ignore
    posting_headers = account_header.findall("PostingHeader") # type: ignore

    data_elements: list[ET.Element] = []
    for posting_header in posting_headers:
        if posting_header.find("HourlyIndicatedValue") is not None:
            data_elements.append(posting_header)
    
    data_element_columns = [tag for (tag, text) in data_elements[0].find("HourlyIndicatedValue").items()] # type: ignore
    partial_dfs = []
    for element in data_elements:
        outer_mappings = {tag: text for (tag, text) in element.items()}
        
        inner_data = {tag: [] for tag in data_element_columns} # type: ignore

        inner_elements = element.findall("HourlyIndicatedValue")
        for inner_element in inner_elements:
            for tag, text in inner_element.items():
                inner_data[tag].append(text)

        partial_df = pd.DataFrame(inner_data)
        for key, value in outer_mappings.items():
            if key in partial_df.columns:
                raise ValueError(f"Key {key} already exists in the DataFrame.")
            
            partial_df[key] = value
        
        partial_dfs.append(partial_df)

    df = pd.concat(partial_dfs, ignore_index=True)

    df[["PostedValue", "Hour", "UTCOffset"]] = df[["PostedValue", "Hour", "UTCOffset"]].astype(pandas.core.arrays.integer.Int64Dtype())
    df[["Data_Date"]] = df[["Data_Date"]].apply(pd.to_datetime, format="%j%Y")
    df[["Data_Code", "Data_Type", "PostingType"]] = df[["Data_Code", "Data_Type", "PostingType"]].astype(pandas.core.arrays.string_.StringDtype())

    return df


def parse_MISOdaily(
    res: requests.Response,
) -> pd.DataFrame:
    return helper_parse_market_report_xml(res)


def parse_MISOsamedaydemand(
    res: requests.Response,
) -> pd.DataFrame:
    return helper_parse_market_report_xml(res)

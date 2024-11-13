import pytest
import datetime

import pandas as pd, pandas
import numpy as np, numpy
import requests

from MISOReports.MISOReports import (
    MISORTWDDataBrokerURLBuilder,
    MISORTWDBIReporterURLBuilder,
    MISOMarketReportsURLBuilder,
    MISOReports,
    MULTI_DF_NAMES_COLUMN,
    MULTI_DF_DFS_COLUMN,
)


def try_to_get_df_res(
    report_name: str, 
    datetime_increment_limit: int,
) -> pd.DataFrame:
    """Tries to get the df for the report_name and returns it. If a request fails, it will 
    increment the datetime and try again up to datetime_increment_limit times.

    :param str report_name: The name of the report to get the df for.
    :param int datetime_increment_limit: The number of times to try to get the df before raising an error.
    :return pd.DataFrame: The df for the report_name.
    """
    report_mappings = MISOReports.report_mappings
    report = report_mappings[report_name]

    cnt = 0
    curr_target_date = report.example_datetime
    while cnt <= datetime_increment_limit:
        try:
            df = MISOReports.get_df(
                report_name=report_name,
                ddatetime=curr_target_date,
            )
            break
        except requests.HTTPError as e:
            curr_target_date = report.url_builder.add_to_datetime(
                ddatetime=curr_target_date, 
                direction=1,
            )
            cnt += 1
    
    if cnt > datetime_increment_limit:
        raise ValueError(f"Failed to get {report_name} after {datetime_increment_limit} attempts (last datetime tried: {curr_target_date}).")
    
    return df


def get_dtype_frozenset(
    df: pd.DataFrame,
    columns: list[str],
) -> frozenset:
    """Returns a frozenset of the types of the columns in the DataFrame.

    :param pd.DataFrame df: The DataFrame to get the types of the columns from.
    :param list[str] columns: The columns to get the types of.
    :return frozenset: A frozenset of the types of the columns in the DataFrame.
    """
    dtypes = df[columns].dtypes

    res = []
    for k in dtypes.index:
        res.append(type(dtypes[k]))
    
    return frozenset(res)


@pytest.fixture
def get_df_test_names():
    single_df_tests = [v[0] for v in single_df_test_list]
    multiple_dfs_tests = [v[0] for v in multiple_dfs_test_list]
    return single_df_tests + multiple_dfs_tests


@pytest.fixture
def datetime_increment_limit(request):
    return request.config.getoption("--datetime-increments-limit")


@pytest.mark.parametrize(
    "target, supported_extensions, file_extension, expected", [
        ("getapiversion", ["json"], "json", "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getapiversion&returnType=json"),
        ("getfuelmix", ["csv", "xml", "json"], "csv", "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getfuelmix&returnType=csv"),
        ("getace", ["csv", "xml", "json"], "xml", "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getace&returnType=xml"),
        ("getAncillaryServicesMCP", ["csv", "xml", "json"], "json", "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getAncillaryServicesMCP&returnType=json"),
    ]
)
def test_MISORTWDDataBrokerURLBuilder_build_url_extension_supported(
    target, 
    supported_extensions, 
    file_extension, 
    expected,
):
    url_builder = MISORTWDDataBrokerURLBuilder(
        target=target, 
        supported_extensions=supported_extensions,
    )

    assert url_builder.build_url(file_extension=file_extension) == expected


@pytest.mark.parametrize(
    "target, supported_extensions, file_extension", [
        ("getapiversion", ["json"], "xml"),
        ("getfuelmix", ["csv", "xml", "json"], "http"),
        ("getace", ["csv", "xml", "json"], "xlsx"),
        ("getAncillaryServicesMCP", ["csv", "xml", "json"], "xlsx"),
    ]
)
def test_MISORTWDDataBrokerURLBuilder_build_url_extension_not_supported(
    target, 
    supported_extensions, 
    file_extension, 
):
    url_builder = MISORTWDDataBrokerURLBuilder(
        target=target, 
        supported_extensions=supported_extensions,
    )

    with pytest.raises(ValueError) as e:
        url_builder.build_url(file_extension=file_extension)


@pytest.mark.parametrize(
    "target, supported_extensions, file_extension, expected", [
        ("currentinterval", ["csv"], "csv", "https://api.misoenergy.org/MISORTWDBIReporter/Reporter.asmx?messageType=currentinterval&returnType=csv"),
    ]
)
def test_MISORTWDBIReporterURLBuilder_build_url_extension_supported(
    target, 
    supported_extensions, 
    file_extension, 
    expected,
):
    url_builder = MISORTWDBIReporterURLBuilder(
        target=target, 
        supported_extensions=supported_extensions,
    )

    assert url_builder.build_url(file_extension=file_extension) == expected


@pytest.mark.parametrize(
    "target, supported_extensions, file_extension", [
        ("currentinterval", ["csv"], "json"),
    ]
)
def test_MISORTWDBIReporterURLBuilder_build_url_extension_not_supported(
    target, 
    supported_extensions, 
    file_extension, 
):
    url_builder = MISORTWDBIReporterURLBuilder(
        target=target, 
        supported_extensions=supported_extensions,
    )

    with pytest.raises(ValueError) as e:
        url_builder.build_url(file_extension=file_extension)


@pytest.mark.parametrize(
    "target, supported_extensions, url_generator, ddatetime, file_extension, expected", [
        ("DA_Load_EPNodes", ["zip"], MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last, datetime.datetime(year=2024, month=10, day=21), "zip", "https://docs.misoenergy.org/marketreports/DA_Load_EPNodes_20241021.zip"),
        ("da_exante_lmp", ["csv"], MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first, datetime.datetime(year=2024, month=10, day=26), "csv", "https://docs.misoenergy.org/marketreports/20241026_da_exante_lmp.csv"),
        ("da_expost_lmp", ["csv"], MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first, datetime.datetime(year=2024, month=10, day=26), "csv", "https://docs.misoenergy.org/marketreports/20241026_da_expost_lmp.csv"),
        ("DA_LMPs", ["zip"], MISOMarketReportsURLBuilder.url_generator_YYYY_current_month_name_to_two_months_later_name_first, datetime.datetime(year=2024, month=7, day=1), "zip", "https://docs.misoenergy.org/marketreports/2024-Jul-Sep_DA_LMPs.zip"),
        ("DA_LMPs", ["zip"], MISOMarketReportsURLBuilder.url_generator_YYYY_current_month_name_to_two_months_later_name_first, datetime.datetime(year=2024, month=11, day=1), "zip", "https://docs.misoenergy.org/marketreports/2024-Nov-Jan_DA_LMPs.zip"),
        ("rt_expost_str_5min_mcp", ["xlsx"], MISOMarketReportsURLBuilder.url_generator_YYYYmm_first, datetime.datetime(year=2024, month=10, day=1), "xlsx", "https://docs.misoenergy.org/marketreports/202410_rt_expost_str_5min_mcp.xlsx"),
        ("MARKET_SETTLEMENT_DATA_SRW", ["zip"], MISOMarketReportsURLBuilder.url_generator_no_date, None, "zip", "https://docs.misoenergy.org/marketreports/MARKET_SETTLEMENT_DATA_SRW.zip"),
        ("MARKET_SETTLEMENT_DATA_SRW", ["zip"], MISOMarketReportsURLBuilder.url_generator_no_date, datetime.datetime.now(), "zip", "https://docs.misoenergy.org/marketreports/MARKET_SETTLEMENT_DATA_SRW.zip"),
        ("M2M_Settlement_srw", ["csv"], MISOMarketReportsURLBuilder.url_generator_YYYY_last, datetime.datetime(year=2024, month=10, day=1), "csv", "https://docs.misoenergy.org/marketreports/M2M_Settlement_srw_2024.csv"),
        ("Allocation_on_MISO_Flowgates", ["csv"], MISOMarketReportsURLBuilder.url_generator_YYYY_mm_dd_last, datetime.datetime(year=2024, month=10, day=29), "csv", "https://docs.misoenergy.org/marketreports/Allocation_on_MISO_Flowgates_2024_10_29.csv"),
    ]
)
def test_MISOMarketReportsURLBuilder_build_url(   
    target, 
    supported_extensions, 
    url_generator,
    ddatetime,
    file_extension,
    expected, 
):
    url_builder = MISOMarketReportsURLBuilder(
        target=target, 
        supported_extensions=supported_extensions,
        url_generator=url_generator
    )

    assert url_builder.build_url(ddatetime=ddatetime, file_extension=file_extension) == expected
        

def test_get_df_every_report_example_url_returns_non_empty_df(datetime_increment_limit):
    mappings = MISOReports.report_mappings

    # These reports have no non-empty tables as of 2024-11-02.
    empty_reports = set(
        [
            "da_M2M_Settlement_srw",
        ],
    )

    for report_name, report in mappings.items():
        try:
            df = try_to_get_df_res(
                report_name=report_name,
                datetime_increment_limit=datetime_increment_limit,
            )

            assert not df.columns.empty
            if report_name not in empty_reports:
                assert not df.empty
        except NotImplementedError as e:
            pass


single_df_test_list = [
    (
        "rt_bc_HIST", 
        {
            ("Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
            ("Override",): pandas.core.arrays.integer.Int64Dtype,
            ("Flowgate NERCID", "Constraint_ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type",): pandas.core.arrays.string_.StringDtype,
            ("Market Date", "Hour of Occurrence",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "RT_UDS_Approved_Case_Percentage", 
        {
            ("Percentage",): numpy.dtypes.Float64DType,
            ("UDS Case ID",): pandas.core.arrays.string_.StringDtype,
            ("Dispatch Interval",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "Resource_Uplift_by_Commitment_Reason", 
        {
            ("ECONOMIC MAX",): numpy.dtypes.Float64DType,
            ("LOCAL RESOURCE ZONE",): pandas.core.arrays.integer.Int64Dtype,
            ("REASON", "REASON ID",): pandas.core.arrays.string_.StringDtype,
            ("STARTTIME",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rt_rpe", 
        {
            ("Shadow Price",): numpy.dtypes.Float64DType,
            ("Constraint Name", "Constraint Description",): pandas.core.arrays.string_.StringDtype,
            ("Time of Occurence",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "Historical_RT_RSG_Commitment", 
        {
            ("TOTAL_ECON_MAX",): numpy.dtypes.Float64DType,
            ("COMMIT_REASON", "NUM_RESOURCES",): pandas.core.arrays.string_.StringDtype,
            ("MKT_INT_END_EST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "da_pbc", 
        {
            ("PRELIMINARY_SHADOW_PRICE",): numpy.dtypes.Float64DType,
            ("BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE",): pandas.core.arrays.integer.Int64Dtype,
            ("CONSTRAINT_NAME", "CURVETYPE", "REASON",): pandas.core.arrays.string_.StringDtype,
            ("MARKET_HOUR_EST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "da_bc", 
        {
            ("Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
            ("Hour of Occurrence", "Override",): pandas.core.arrays.integer.Int64Dtype,
            ("Flowgate NERC ID", "Constraint_ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "da_bcsf", 
        {
            ("From KV", "To KV", "Direction",): pandas.core.arrays.integer.Int64Dtype,
            ("Constraint ID", "Constraint Name", "Contingency Name", "Constraint Type", "Flowgate Name", "Device Type", "Key1", "Key2", "Key3", "From Area", "To Area", "From Station", "To Station",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "MARKET_SETTLEMENT_DATA_SRW", 
        {
            ("DATE",): numpy.dtypes.DateTime64DType,
            ("BILL_DET",): pandas.core.arrays.string_.StringDtype,
            ("HR01", "HR02", "HR03", "HR04", "HR05", "HR06", "HR07", "HR08", "HR09", "HR10", "HR11", "HR12", "HR13", "HR14", "HR15", "HR16", "HR17", "HR18", "HR19", "HR20", "HR21", "HR22", "HR23", "HR24",): numpy.dtypes.Float64DType,
        }
    ),
    (
        "combinedwindsolar", 
        {
            ("ForecastDateTimeEST", "ActualDateTimeEST",): numpy.dtypes.DateTime64DType,
            ("ForecastHourEndingEST", "ActualHourEndingEST",): pandas.core.arrays.integer.Int64Dtype,
            ("ForecastWindValue", "ForecastSolarValue", "ActualWindValue", "ActualSolarValue",): numpy.dtypes.Float64DType,
        }
    ),
    (
        "ms_vlr_HIST_SRW", 
        {
            ("OPERATING DATE",): numpy.dtypes.DateTime64DType,
            ("SETTLEMENT RUN", "DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total",): numpy.dtypes.Float64DType,
            ("REGION", "CONSTRAINT",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "SolarForecast", 
        {
            ("DateTimeEST",): numpy.dtypes.DateTime64DType,
            ("HourEndingEST",): pandas.core.arrays.integer.Int64Dtype,
            ("Value",): numpy.dtypes.Float64DType,
        }
    ),
    (
        "DA_LMPs", 
        {
            ("MARKET_DAY",): numpy.dtypes.DateTime64DType,
            ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): numpy.dtypes.Float64DType,
            ("NODE", "TYPE", "VALUE",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "rt_irsf", 
        {
            ("MKTHOUR_EST",): numpy.dtypes.DateTime64DType,
            ("INTRAREGIONAL_SCHEDULED_FLOW",): numpy.dtypes.Float64DType,
            ("CONSTRAINT_NAME",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "rt_mf", 
        {
            ("Unit Count", "Hour Ending",): pandas.core.arrays.integer.Int64Dtype,
            ("Time Interval EST",): numpy.dtypes.DateTime64DType,
            ("Peak Flag", "Region Name", "Fuel Type",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "rt_ex", 
        {
            ("Committed (GW at Economic Maximum) - Forward", "Committed (GW at Economic Maximum) - Real-Time", "Committed (GW at Economic Maximum) - Delta", "Load (GW) - Forward", "Load (GW) - Real-Time", "Load (GW) - Delta", "Net Scheduled Imports (GW) - Forward", "Net Scheduled Imports (GW) - Real-Time", "Net Scheduled Imports (GW) - Delta", "Outages (GW at Economic Maximum) - Forward", "Outages (GW at Economic Maximum) - Real-Time", "Outages (GW at Economic Maximum) - Delta", "Offer Changes (GW at Economic Maximum) - Forward", "Offer Changes (GW at Economic Maximum) - Real-Time", "Offer Changes (GW at Economic Maximum) - Delta",): numpy.dtypes.Float64DType,
            ("Hour", "Real-Time Binding Constraints - (#)",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "df_al", 
        {
            ("LRZ1 MTLF (MWh)", "LRZ1 ActualLoad (MWh)", "LRZ2_7 MTLF (MWh)", "LRZ2_7 ActualLoad (MWh)", "LRZ3_5 MTLF (MWh)", "LRZ3_5 ActualLoad (MWh)", "LRZ4 MTLF (MWh)", "LRZ4 ActualLoad (MWh)", "LRZ6 MTLF (MWh)", "LRZ6 ActualLoad (MWh)", "LRZ8_9_10 MTLF (MWh)", "LRZ8_9_10 ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)",): numpy.dtypes.Float64DType,
            ("HourEnding",): pandas.core.arrays.integer.Int64Dtype,
            ("Market Day",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rf_al", 
        {
            ("North MTLF (MWh)", "North ActualLoad (MWh)", "Central MTLF (MWh)", "Central ActualLoad (MWh)", "South MTLF (MWh)", "South ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)",): numpy.dtypes.Float64DType,
            ("HourEnding",): pandas.core.arrays.integer.Int64Dtype,
            ("Market Day",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "da_rpe", 
        {
            ("Shadow Price",): numpy.dtypes.Float64DType,
            ("Hour of Occurence",): pandas.core.arrays.integer.Int64Dtype,
            ("Constraint Name", "Constraint Description",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "da_ex", 
        {
            ("Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total",): numpy.dtypes.Float64DType,
            ("Hour",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "da_ex_rg", 
        {
            ("Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total",): numpy.dtypes.Float64DType,
            ("Hour Ending",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "da_bc_HIST", 
        {
            ("Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
            ("Hour of Occurrence", "Override",): pandas.core.arrays.integer.Int64Dtype,
            ("Constraint Name", "Constraint_ID", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type",): pandas.core.arrays.string_.StringDtype,
            ("Market Date",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "cpnode_reszone", 
        {
            ("Reserve Zone",): pandas.core.arrays.integer.Int64Dtype,
            ("CP Node Name",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "da_co", 
        {
            ("Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "MW", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): numpy.dtypes.Float64DType,
            ("Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope",): pandas.core.arrays.integer.Int64Dtype,
            ("Region", "Unit Code",): pandas.core.arrays.string_.StringDtype,
            ("Date/Time Beginning (EST)", "Date/Time End (EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rt_co", 
        {
            ("Cleared MW1", "Cleared MW2", "Cleared MW3", "Cleared MW4", "Cleared MW5", "Cleared MW6", "Cleared MW7", "Cleared MW8", "Cleared MW9", "Cleared MW10", "Cleared MW11", "Cleared MW12", "Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): numpy.dtypes.Float64DType,
            ("Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope",): pandas.core.arrays.integer.Int64Dtype,
            ("Region", "Unit Code",): pandas.core.arrays.string_.StringDtype,
            ("Mkthour Begin (EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "Dead_Node_Report", 
        {
            ("PNODE Name",): pandas.core.arrays.string_.StringDtype,
            ("Mkt Hour",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "asm_rt_co", 
        {
            ("RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP1", "RegMW1", "RegMCP2", "RegMW2", "RegMCP3", "RegMW3", "RegMCP4", "RegMW4", "RegMCP5", "RegMW5", "RegMCP6", "RegMW6", "RegMCP7", "RegMW7", "RegMCP8", "RegMW8", "RegMCP9", "RegMW9", "RegMCP10", "RegMW10", "RegMCP11", "RegMW11", "RegMCP12", "RegMW12", "SpinMCP1", "SpinMW1", "SpinMCP2", "SpinMW2", "SpinMCP3", "SpinMW3", "SpinMCP4", "SpinMW4", "SpinMCP5", "SpinMW5", "SpinMCP6", "SpinMW6", "SpinMCP7", "SpinMW7", "SpinMCP8", "SpinMW8", "SpinMCP9", "SpinMW9", "SpinMCP10", "SpinMW10", "SpinMCP11", "SpinMW11", "SpinMCP12", "SpinMW12", "SuppMCP1", "SuppMW1", "SuppMCP2", "SuppMW2", "SuppMCP3", "SuppMW3", "SuppMCP4", "SuppMW4", "SuppMCP5", "SuppMW5", "SuppMCP6", "SuppMW6", "SuppMCP7", "SuppMW7", "SuppMCP8", "SuppMW8", "SuppMCP9", "SuppMW9", "SuppMCP10", "SuppMW10", "SuppMCP11", "SuppMW11", "SuppMCP12", "SuppMW12", "StrOfflineOfferRate", "STRMCP1", "STRMW1", "STRMCP2", "STRMW2", "STRMCP3", "STRMW3", "STRMCP4", "STRMW4", "STRMCP5", "STRMW5", "STRMCP6", "STRMW6", "STRMCP7", "STRMW7", "STRMCP8", "STRMW8", "STRMCP9", "STRMW9", "STRMCP10", "STRMW10", "STRMCP11", "STRMW11", "STRMCP12", "STRMW12", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): numpy.dtypes.Float64DType,
            ("Region", "Unit Code",): pandas.core.arrays.string_.StringDtype,
            ("Mkthour Begin (EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "asm_da_co", 
        {
            ("RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP", "RegMW", "SpinMCP", "SpinMW", "SuppMCP", "SuppMW", "OfflineSTR", "STRMCP", "STRMW", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): numpy.dtypes.Float64DType,
            ("Region", "Unit Code",): pandas.core.arrays.string_.StringDtype,
            ("Date/Time Beginning (EST)", "Date/Time End (EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "M2M_Settlement_srw", 
        {
            ("MISO_SHADOW_PRICE", "MISO_MKT_FLOW", "MISO_FFE", "CP_SHADOW_PRICE", "CP_MKT_FLOW", "CP_FFE", "MISO_CREDIT", "CP_CREDIT",): numpy.dtypes.Float64DType,
            ("FLOWGATE_ID", "MONITORING_RTO", "CP_RTO", "FLOWGATE_NAME",): pandas.core.arrays.string_.StringDtype,
            ("HOUR_ENDING",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "M2M_Flowgates_as_of", 
        {
            ("Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "M2M_FFE", 
        {
            ("Non Monitoring RTO FFE", "Adjusted FFE",): numpy.dtypes.Float64DType,
            ("NERC Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description",): pandas.core.arrays.string_.StringDtype,
            ("Hour Ending",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "Allocation_on_MISO_Flowgates", 
        {
            ("Allocation (MW)",): numpy.dtypes.Float64DType,
            ("Allocation to Rating Percentage",): pandas.core.arrays.integer.Int64Dtype,
            ("NERC ID", "Flowgate Owner", "Flowgate Description", "Entity", "Direction", "Reciprocal Status on Flowgate",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "rt_pbc", 
        {
            ("PRELIMINARY_SHADOW_PRICE",): numpy.dtypes.Float64DType,
            ("BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE",): pandas.core.arrays.integer.Int64Dtype,
            ("CONSTRAINT_NAME", "CURVETYPE", "REASON",): pandas.core.arrays.string_.StringDtype,
            ("MARKET_HOUR_EST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rt_bc", 
        {
            ("Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
            ("Override",): pandas.core.arrays.integer.Int64Dtype,
            ("Flowgate NERC ID", "Constraint ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type",): pandas.core.arrays.string_.StringDtype,
            ("Hour of Occurrence",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rt_or", 
        {
            ("Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
            ("Override",): pandas.core.arrays.integer.Int64Dtype,
            ("Flowgate NERC ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason",): pandas.core.arrays.string_.StringDtype,
            ("Hour of Occurrence",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rt_fuel_on_margin", 
        {
            ("Hour Ending", "Unit Count",): pandas.core.arrays.integer.Int64Dtype,
            ("Peak Flag", "Region Name", "Fuel Type",): pandas.core.arrays.string_.StringDtype,
            ("Time Interval EST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "5min_expost_mcp", 
        {
            ("RT MCP Regulation", "RT MCP Spin", "RT MCP Supp",): numpy.dtypes.Float64DType,
            ("Zone",): pandas.core.arrays.string_.StringDtype,
            ("Time (EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "5min_exante_mcp", 
        {
            ("RT Ex-Ante MCP Regulation", "RT Ex-Ante MCP Spin", "RT Ex-Ante MCP Supp",): numpy.dtypes.Float64DType,
            ("Zone",): pandas.core.arrays.string_.StringDtype,
            ("Time (EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "ftr_mpma_bids_offers", 
        {
            ("MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10",): numpy.dtypes.Float64DType,
            ("Market Name", "Source", "Sink", "Hedge Type", "Class", "Type", "Round", "Asset Owner ID",): pandas.core.arrays.string_.StringDtype,
            ("Start Date", "End Date",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "ftr_annual_bids_offers", 
        {
            ("MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10",): numpy.dtypes.Float64DType,
            ("Market Name", "Source", "Sink", "Hedge Type", "Class", "Type", "Round", "Asset Owner ID",): pandas.core.arrays.string_.StringDtype,
            ("Start Date", "End Date",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "bids_cb", 
        {
            ("MW", "LMP", "PRICE1", "MW1", "PRICE2", "MW2", "PRICE3", "MW3", "PRICE4", "MW4", "PRICE5", "MW5", "PRICE6", "MW6", "PRICE7", "MW7", "PRICE8", "MW8", "PRICE9", "MW9",): numpy.dtypes.Float64DType,
            ("Market Participant Code",): pandas.core.arrays.integer.Int64Dtype,
            ("Region", "Type of Bid", "Bid ID",): pandas.core.arrays.string_.StringDtype,
            ("Date/Time Beginning (EST)", "Date/Time End (EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "5MIN_LMP", 
        {
            ("LMP", "CON_LMP", "LOSS_LMP",): numpy.dtypes.Float64DType,
            ("PNODENAME",): pandas.core.arrays.string_.StringDtype,
            ("MKTHOUR_EST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "RT_Load_EPNodes", 
        {
            ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): numpy.dtypes.Float64DType,
            ("EPNode", "Value",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "realtimebindingsrpbconstraints", 
        {
            ("Price",): numpy.dtypes.Float64DType,
            ("BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4",): pandas.core.arrays.integer.Int64Dtype,
            ("Name", "OVERRIDE", "REASON", "CURVETYPE",): pandas.core.arrays.string_.StringDtype,
            ("Period",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "realtimebindingconstraints", 
        {
            ("Price",): numpy.dtypes.Float64DType,
            ("BP1", "PC1", "BP2", "PC2",): pandas.core.arrays.integer.Int64Dtype,
            ("Name", "OVERRIDE", "CURVETYPE",): pandas.core.arrays.string_.StringDtype,
            ("Period",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "lmpconsolidatedtable", 
        {
            ("LMP", "MLC", "MCC", "REGMCP", "REGMILEAGEMCP", "SPINMCP", "SUPPMCP", "STRMCP", "RCUPMCP", "RCDOWNMCP", "LMP.1", "MLC.1", "MCC.1", "LMP.2", "MLC.2", "MCC.2", "LMP.3", "MLC.3", "MCC.3",): numpy.dtypes.Float64DType,
            ("Name",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "apiversion", 
        {
            ("Semantic",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "generationoutagesplusminusfivedays", 
        {
            ("Unplanned", "Planned", "Forced", "Derated",): pandas.core.arrays.integer.Int64Dtype,
            ("OutageMonthDay",): pandas.core.arrays.string_.StringDtype,
            ("OutageDate",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rt_expost_str_mcp", 
        {
            ("Hour Ending", "RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8",): numpy.dtypes.Float64DType,
            ("Preliminary/ Final",): pandas.core.arrays.string_.StringDtype,
            ("MARKET DATE",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rt_expost_str_5min_mcp", 
        {
            ("RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8",): numpy.dtypes.Float64DType,
            ("Preliminary/ Final",): pandas.core.arrays.string_.StringDtype,
            ("Time(EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rt_expost_ramp_mcp", 
        {
            ("Reserve Zone 1 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post Hourly",): numpy.dtypes.Float64DType,
            ("Hour Ending",): pandas.core.arrays.integer.Int64Dtype,
            ("Preliminary / Final",): pandas.core.arrays.string_.StringDtype,
            ("Market Date",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "rt_expost_ramp_5min_mcp", 
        {
            ("Reserve Zone 1 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post 5 Min",): numpy.dtypes.Float64DType,
            ("Preliminary / Final",): pandas.core.arrays.string_.StringDtype,
            ("Time (EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "da_expost_str_mcp", 
        {
            ("Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8",): numpy.dtypes.Float64DType,
            ("Hour Ending",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "da_expost_ramp_mcp", 
        {
            ("Reserve Zone 1 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Post 1 Hour",): numpy.dtypes.Float64DType,
            ("Hour Ending",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "da_exante_str_mcp", 
        {
            ("Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8",): numpy.dtypes.Float64DType,
            ("Hour Ending",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "da_exante_ramp_mcp", 
        {
            ("Reserve Zone 1 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Ante 1 Hour",): numpy.dtypes.Float64DType,
            ("Hour Ending",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "regionaldirectionaltransfer", 
        {
            ("NORTH_SOUTH_LIMIT", "SOUTH_NORTH_LIMIT", "RAW_MW", " UDSFLOW_MW",): pandas.core.arrays.integer.Int64Dtype,
            ("INTERVALEST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "NAI", 
        {
            ("Value",): numpy.dtypes.Float64DType,
            ("Name",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "Total_Uplift_by_Resource", 
        {
            ("Total Uplift Amount",): numpy.dtypes.Float64DType,
            ("Resource Name",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "ms_rsg_srw", 
        {
            ("MISO_RT_RSG_DIST2", "RT_RSG_DIST1", "RT_RSG_MWP", "DA_RSG_MWP", "DA_RSG_DIST",): numpy.dtypes.Float64DType,
            ("previous 36 months",): pandas.core.arrays.string_.StringDtype,
            ("START", "STOP",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "ms_rnu_srw", 
        {
            ("JOA_MISO_UPLIFT", "MISO_RT_GFACO_DIST", "MISO_RT_GFAOB_DIST", "MISO_RT_RSG_DIST2", "RT_CC", "DA_RI", "RT_RI", "ASM_RI", "STRDFC_UPLIFT", "CRDFC_UPLIFT", "MISO_PV_MWP_UPLIFT", "MISO_DRR_COMP_UPL", "MISO_TOT_MIL_UPL", "RC_DIST", "TOTAL RNU",): numpy.dtypes.Float64DType,
            ("previous 36 months",): pandas.core.arrays.string_.StringDtype,
            ("START", "STOP",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "ms_ri_srw", 
        {
            ("DA RI", "RT RI", "TOTAL RI",): numpy.dtypes.Float64DType,
            ("Previous Months",): pandas.core.arrays.string_.StringDtype,
            ("START", "STOP",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "ms_ecf_srw", 
        {
            ("Da Xs Cg Fnd", "Rt Cc", "Rt Xs Cg Fnd", "Ftr Auc Res", "Ao Ftr Mn Alc", "Ftr Yr Alc *", "Tbs Access", "Net Ecf", "Ftr Shrtfll", "Net Ftr Sf", "Ftr Trg Cr Alc", "Ftr Hr Alc", "Hr Mf", "Hourly Ftr Allocation", "Monthly Ftr Allocation",): numpy.dtypes.Float64DType,
            ("Unnamed: 0",): pandas.core.arrays.string_.StringDtype,
            ("Start", "Stop",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "ccf_co", 
        {
            ("HOUR1", "HOUR2", "HOUR3", "HOUR4", "HOUR5", "HOUR6", "HOUR7", "HOUR8", "HOUR9", "HOUR10", "HOUR11", "HOUR12", "HOUR13", "HOUR14", "HOUR15", "HOUR16", "HOUR17", "HOUR18", "HOUR19", "HOUR20", "HOUR21", "HOUR22", "HOUR23", "HOUR24",): numpy.dtypes.Float64DType,
            ("CONSTRAINT NAME", "NODE NAME",): pandas.core.arrays.string_.StringDtype,
            ("OPERATING DATE",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "ms_vlr_HIST", 
        {
            ("DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total",): numpy.dtypes.Float64DType,
            ("SETTLEMENT RUN",): pandas.core.arrays.integer.Int64Dtype,
            ("REGION", "CONSTRAINT",): pandas.core.arrays.string_.StringDtype,
            ("OPERATING DATE",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "fuelmix", 
        {
            ("ACT", "TOTALMW",): pandas.core.arrays.integer.Int64Dtype,
            ("CATEGORY",): pandas.core.arrays.string_.StringDtype,
            ("INTERVALEST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "ace", 
        {
            ("value",): numpy.dtypes.Float64DType,
            ("instantEST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "cts", 
        {
            ("PJMFORECASTEDLMP",): numpy.dtypes.Float64DType,
            ("CASEAPPROVALDATE", "SOLUTIONTIME",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "WindForecast", 
        {
            ("Value",): numpy.dtypes.Float64DType,
            ("HourEndingEST",): pandas.core.arrays.integer.Int64Dtype,
            ("DateTimeEST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "Wind", 
        {
            ("ForecastValue", "ActualValue",): numpy.dtypes.Float64DType,
            ("ForecastHourEndingEST", "ActualHourEndingEST",): pandas.core.arrays.integer.Int64Dtype,
            ("ForecastDateTimeEST", "ActualDateTimeEST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "Solar", 
        {
            ("ForecastValue", "ActualValue",): numpy.dtypes.Float64DType,
            ("ForecastHourEndingEST", "ActualHourEndingEST",): pandas.core.arrays.integer.Int64Dtype,
            ("ForecastDateTimeEST", "ActualDateTimeEST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "exantelmp", 
        {
            ("LMP", "Loss", "Congestion",): numpy.dtypes.Float64DType,
            ("Name",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "da_exante_lmp", 
        {
            ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
            ("Node", "Type", "Value",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "da_expost_lmp", 
        {
            ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
            ("Node", "Type", "Value",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "rt_lmp_final", 
        {
            ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
            ("Node", "Type", "Value",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "rt_lmp_prelim", 
        {
            ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
            ("Node", "Type", "Value",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "DA_Load_EPNodes", 
        {
            ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): numpy.dtypes.Float64DType,
            ("EPNode", "Value",): pandas.core.arrays.string_.StringDtype,
        }
    ),
    (
        "5min_exante_lmp", 
        {
            ("RT Ex-Ante LMP", "RT Ex-Ante MEC", "RT Ex-Ante MLC", "RT Ex-Ante MCC",): numpy.dtypes.Float64DType,
            ("CP Node",): pandas.core.arrays.string_.StringDtype,
            ("Time (EST)",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "SolarActual", 
        {
            ("Value",): numpy.dtypes.Float64DType,
            ("HourEndingEST",): pandas.core.arrays.integer.Int64Dtype,
            ("DateTimeEST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "WindActual", 
        {
            ("Value",): numpy.dtypes.Float64DType,
            ("HourEndingEST",): pandas.core.arrays.integer.Int64Dtype,
            ("DateTimeEST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "RSG", 
        {
            ("TOTAL_ECON_MAX",): numpy.dtypes.Float64DType,
            ("COMMIT_REASON", "NUM_RESOURCES",): pandas.core.arrays.string_.StringDtype,
            ("MKT_INT_END_EST",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "reservebindingconstraints", 
        {
            ("Price",): numpy.dtypes.Float64DType,
            ("Name", "Description",): pandas.core.arrays.string_.StringDtype,
            ("Period",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "importtotal5", 
        {
            ("Value",): numpy.dtypes.Float64DType,
            ("Time",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "nsi5miso", 
        {
            ("timestamp",): numpy.dtypes.DateTime64DType,
            ("NSI",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "nsi1miso", 
        {
            ("NSI",): pandas.core.arrays.integer.Int64Dtype,
            ("timestamp",): numpy.dtypes.DateTime64DType,
        }
    ),
    (
        "nsi5", 
        {
            ("timestamp",): numpy.dtypes.DateTime64DType,
            ("AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "nsi1", 
        {
            ("timestamp",): numpy.dtypes.DateTime64DType,
            ("AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE",): pandas.core.arrays.integer.Int64Dtype,
        }
    ),
    (
        "RT_LMPs",
        {
            ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): numpy.dtypes.Float64DType,
            ("NODE", "TYPE", "VALUE",): pandas.core.arrays.string_.StringDtype,
            ("MARKET_DAY",): numpy.dtypes.DateTime64DType,
        },
    ),
]


@pytest.mark.parametrize(
    "report_name, columns_mapping", single_df_test_list
)
def test_get_df_single_df_correct_columns(report_name, columns_mapping, datetime_increment_limit):
    df = try_to_get_df_res(
        report_name=report_name,
        datetime_increment_limit=datetime_increment_limit,
    )

    columns_mapping_columns = []
    for columns_group in columns_mapping.keys():
        columns_mapping_columns.extend(columns_group)
        
    columns_mapping_columns_set = frozenset(columns_mapping_columns)
    df_columns_set = frozenset(df.columns)

    if columns_mapping_columns_set != df_columns_set:
        raise ValueError(f"Expected columns {columns_mapping_columns_set} do not match df columns {df_columns_set}.")

    for columns_tuple, column_type in columns_mapping.items():
        columns = list(columns_tuple)
        
        assert frozenset([column_type]) == get_dtype_frozenset(df, columns), \
            f"For report {report_name}, columns {columns} are not of type {column_type}."


multiple_dfs_test_list = [
    (
        "AncillaryServicesMCP",
        {
            "Interval": {
                ("RefId",): pandas.core.arrays.string_.StringDtype,
            },
            "RealTimeMCP": {
                ("number",): pandas.core.arrays.integer.Int64Dtype,
                ("GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp",): numpy.dtypes.Float64DType,
            },
            "DayAheadMCP": {
                ("number",): pandas.core.arrays.integer.Int64Dtype,
                ("GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp",): numpy.dtypes.Float64DType,
            }
        },
    ),
    (
        "ftr_mpma_results",
        {
            "BindingConstraint_Dec24_AUCTION_Nov24Auc_Round_1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Feb25_AUCTION_Nov24Auc_Round_1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Jan25_AUCTION_Nov24Auc_Round_1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Nov24_AUCTION_Nov24Auc_Round_1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "MarketResults_Dec24_AUCTION_Nov24Auc_Round_1": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Feb25_AUCTION_Nov24Auc_Round_1": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Jan25_AUCTION_Nov24Auc_Round_1": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Nov24_AUCTION_Nov24Auc_Round_1": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "SourceSinkShadowPrices_Dec24_AUCTION_Nov24Auc_Round_1": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Feb25_AUCTION_Nov24Auc_Round_1": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Jan25_AUCTION_Nov24Auc_Round_1": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Nov24_AUCTION_Nov24Auc_Round_1": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            }
        },
    ),
    (
        "da_pr",
        {
            "Table 1": {
                ("Type",): pandas.core.arrays.string_.StringDtype,
                ("Demand Fixed", " Demand Price Sensitive", "Demand Virtual", "Demand Total",): numpy.dtypes.Float64DType,
            },
            "Table 2": {
                ("Type",): pandas.core.arrays.string_.StringDtype,
                ("Supply Physical", "Supply Virtual", "Supply Total",): numpy.dtypes.Float64DType,
            },
            "Table 3": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): numpy.dtypes.Float64DType,
                ("Hour",): pandas.core.arrays.integer.Int64Dtype,
            },
            "Table 4": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): numpy.dtypes.Float64DType,
                ("Around the Clock",): pandas.core.arrays.string_.StringDtype,
            },
            "Table 5": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): numpy.dtypes.Float64DType,
                ("On-Peak",): pandas.core.arrays.string_.StringDtype,  
            },
            "Table 6": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): numpy.dtypes.Float64DType,
                ("Off-Peak",): pandas.core.arrays.string_.StringDtype, 
            }
        },
    ),
    (
        "asm_rtmcp_prelim",
        {
            "Table 1": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
                ("Label", "MCP Type",): pandas.core.arrays.string_.StringDtype,
            },
            "Table 2": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
                ("Zone",): pandas.core.arrays.integer.Int64Dtype,
                ("Pnode", "MCP Type",): pandas.core.arrays.string_.StringDtype,
            },
        }
    ),
    (
        "asm_rtmcp_final",
        {
            "Table 1": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
                ("Label", "MCP Type",): pandas.core.arrays.string_.StringDtype,
            },
            "Table 2": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
                ("Zone",): pandas.core.arrays.integer.Int64Dtype,
                ("Pnode", "MCP Type",): pandas.core.arrays.string_.StringDtype,
            },
        }
    ),
    (
        "asm_expost_damcp",
        {
            "Table 1": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
                ("Label", "MCP Type",): pandas.core.arrays.string_.StringDtype,
            },
            "Table 2": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): numpy.dtypes.Float64DType,
                ("Zone",): pandas.core.arrays.integer.Int64Dtype,
                ("Pnode", "MCP Type",): pandas.core.arrays.string_.StringDtype,
            },
        }
    ),
    (
        "ftr_annual_results_round_1",
        {
            "BindingConstraint_Fal24_AUCTION_Annual24Auc_Round_1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Spr25_AUCTION_Annual24Auc_Round_1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Sum24_AUCTION_Annual24Auc_Round_1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Win24_AUCTION_Annual24Auc_Round_1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "MarketResults_Fal24_AUCTION_Annual24Auc_Round_1": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Spr25_AUCTION_Annual24Auc_Round_1": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Sum24_AUCTION_Annual24Auc_Round_1": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Win24_AUCTION_Annual24Auc_Round_1": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "SourceSinkShadowPrices_Fal24_AUCTION_Annual24Auc_Round_1": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Spr25_AUCTION_Annual24Auc_Round_1": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Sum24_AUCTION_Annual24Auc_Round_1": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Win24_AUCTION_Annual24Auc_Round_1": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
        },
    ),
    (
        "ftr_annual_results_round_2",
        {
            "BindingConstraint_Fal24_AUCTION_Annual24Auc_Round_2": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Spr25_AUCTION_Annual24Auc_Round_2": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Sum24_AUCTION_Annual24Auc_Round_2": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Win24_AUCTION_Annual24Auc_Round_2": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "MarketResults_Fal24_AUCTION_Annual24Auc_Round_2": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Spr25_AUCTION_Annual24Auc_Round_2": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Sum24_AUCTION_Annual24Auc_Round_2": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Win24_AUCTION_Annual24Auc_Round_2": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "SourceSinkShadowPrices_Spr25_AUCTION_Annual24Auc_Round_2": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Fal24_AUCTION_Annual24Auc_Round_2": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Sum24_AUCTION_Annual24Auc_Round_2": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Win24_AUCTION_Annual24Auc_Round_2": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
        },
    ),
    (
        "ftr_annual_results_round_3",
        {
            "BindingConstraint_Fal24_AUCTION_Annual24Auc_Round_3": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Sum24_AUCTION_Annual24Auc_Round_3": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Spr25_AUCTION_Annual24Auc_Round_3": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "BindingConstraint_Win24_AUCTION_Annual24Auc_Round_3": {
                ("Limit", "Flow", "Violation", "MarginalCost",): numpy.dtypes.Float64DType,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pandas.core.arrays.string_.StringDtype,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,

            },
            "MarketResults_Fal24_AUCTION_Annual24Auc_Round_3": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Spr25_AUCTION_Annual24Auc_Round_3": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Sum24_AUCTION_Annual24Auc_Round_3": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "MarketResults_Win24_AUCTION_Annual24Auc_Round_3": {
                ("MW", "ClearingPrice",): numpy.dtypes.Float64DType,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class", "Round",): pandas.core.arrays.string_.StringDtype,
                ("StartDate", "EndDate",): numpy.dtypes.DateTime64DType,
            },
            "SourceSinkShadowPrices_Spr25_AUCTION_Annual24Auc_Round_3": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Sum24_AUCTION_Annual24Auc_Round_3": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Win24_AUCTION_Annual24Auc_Round_3": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
            "SourceSinkShadowPrices_Fal24_AUCTION_Annual24Auc_Round_3": {
                ("ShadowPrice",): numpy.dtypes.Float64DType,
                ("Round",): pandas.core.arrays.integer.Int64Dtype,
                ("SourceSink", "Class",): pandas.core.arrays.string_.StringDtype,
            },
        },
    ),
    (
        "rt_pr",
        {
            "Table 1": {
                ("Demand", "Supply", "Total",): numpy.dtypes.Float64DType,
                ("Type",): pandas.core.arrays.string_.StringDtype,
            },
            "Table 2": {
                ("Demand", "Supply", "Total",): numpy.dtypes.Float64DType,
                ("Type",): pandas.core.arrays.string_.StringDtype,
            },
            "Table 3": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): numpy.dtypes.Float64DType,
                ("Hour",): pandas.core.arrays.integer.Int64Dtype,
            },
            "Table 4": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): numpy.dtypes.Float64DType,
                ("Around the Clock",): pandas.core.arrays.string_.StringDtype,
            },
            "Table 5": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): numpy.dtypes.Float64DType,
                ("On-Peak",): pandas.core.arrays.string_.StringDtype,  
            },
            "Table 6": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): numpy.dtypes.Float64DType,
                ("Off-Peak",): pandas.core.arrays.string_.StringDtype, 
            }
        },
    ),
    (
        "ms_vlr_srw",
        {
            "Table 1": {
                ("DA VLR RSG MWP", "RT VLR RSG MWP", "DA+RT Total",): numpy.dtypes.Float64DType,
                ("Constraint",): pandas.core.arrays.string_.StringDtype,
            },
            "Table 2": {
                ("DA VLR RSG MWP", "RT VLR RSG MWP", "DA+RT Total",): numpy.dtypes.Float64DType,
                ("Constraint",): pandas.core.arrays.string_.StringDtype,
            }
        },
    ),
]


@pytest.mark.parametrize(
    "report_name, dfs_mapping", multiple_dfs_test_list
)
def test_get_df_multiple_dfs_correct_columns_and_matching_df_names(report_name, dfs_mapping, datetime_increment_limit):
    df = try_to_get_df_res(
        report_name=report_name,
        datetime_increment_limit=datetime_increment_limit,
    )

    # Check that df names are as expected.
    expected_df_names = frozenset(dfs_mapping.keys())
    actual_df_names = frozenset(list(df[MULTI_DF_NAMES_COLUMN]))
    assert expected_df_names == actual_df_names, \
        f"Expected DF names {expected_df_names} do not match actual DF names {actual_df_names}."
    
    # Check that df columns are of the expected type.
    for df_name, columns_mapping in dfs_mapping.items():
        df_name_idx = list(df[MULTI_DF_NAMES_COLUMN]).index(df_name)
        res_df = df[MULTI_DF_DFS_COLUMN].iloc[df_name_idx]

        columns_mapping_columns = []
        for columns_group in columns_mapping.keys():
            columns_mapping_columns.extend(columns_group)

        columns_mapping_columns_set = frozenset(columns_mapping_columns)
        res_df_columns_set = frozenset(res_df.columns)

        # Check that the columns in the df match the expected columns.
        if columns_mapping_columns_set != res_df_columns_set:
            raise ValueError(f"Expected columns {columns_mapping_columns_set} do not match df columns {res_df_columns_set}.")

        for columns_tuple, column_type in columns_mapping.items():
            columns = list(columns_tuple)

            assert frozenset([column_type]) == get_dtype_frozenset(res_df, columns), \
                f"For multi-df report {report_name}, df {df_name}, columns {columns} are not of type {column_type}."


def test_get_df_test_test_names_have_no_duplicates(get_df_test_names):
    holder = set()
    for name in get_df_test_names:
        if name in holder:
            raise ValueError(f"Test name {name} is a duplicate.")
        holder.add(name)


@pytest.mark.completion
def test_get_df_test_correct_columns_check_for_every_report(get_df_test_names):
    reports = frozenset(MISOReports.report_mappings.keys())
    correct_column_types_check_reports = frozenset(get_df_test_names)
    
    assert correct_column_types_check_reports == reports, \
        "Not all reports are checked for correct columns."
    
@pytest.mark.parametrize(
    "direction, target, supported_extensions, url_generator, ddatetime, file_extension, expected", [
        (4, "DA_Load_EPNodes", ["zip"], MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last, datetime.datetime(year=2024, month=10, day=21), "zip", "https://docs.misoenergy.org/marketreports/DA_Load_EPNodes_20241025.zip"),
        (1, "da_exante_lmp", ["csv"], MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first, datetime.datetime(year=2024, month=10, day=26), "csv", "https://docs.misoenergy.org/marketreports/20241027_da_exante_lmp.csv"),
        (1, "da_expost_lmp", ["csv"], MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first, datetime.datetime(year=2024, month=10, day=26), "csv", "https://docs.misoenergy.org/marketreports/20241027_da_expost_lmp.csv"),
        (-1, "DA_LMPs", ["zip"], MISOMarketReportsURLBuilder.url_generator_YYYY_current_month_name_to_two_months_later_name_first, datetime.datetime(year=2024, month=7, day=1), "zip", "https://docs.misoenergy.org/marketreports/2024-Apr-Jun_DA_LMPs.zip"),
        (0, "DA_LMPs", ["zip"], MISOMarketReportsURLBuilder.url_generator_YYYY_current_month_name_to_two_months_later_name_first, datetime.datetime(year=2024, month=11, day=1), "zip", "https://docs.misoenergy.org/marketreports/2024-Nov-Jan_DA_LMPs.zip"),
        (-3, "rt_expost_str_5min_mcp", ["xlsx"], MISOMarketReportsURLBuilder.url_generator_YYYYmm_first, datetime.datetime(year=2024, month=10, day=1), "xlsx", "https://docs.misoenergy.org/marketreports/202407_rt_expost_str_5min_mcp.xlsx"),
        (1, "MARKET_SETTLEMENT_DATA_SRW", ["zip"], MISOMarketReportsURLBuilder.url_generator_no_date, datetime.datetime(year=2024, month=10, day=1), "zip", "https://docs.misoenergy.org/marketreports/MARKET_SETTLEMENT_DATA_SRW.zip"),
        (1, "MARKET_SETTLEMENT_DATA_SRW", ["zip"], MISOMarketReportsURLBuilder.url_generator_no_date, datetime.datetime.now(), "zip", "https://docs.misoenergy.org/marketreports/MARKET_SETTLEMENT_DATA_SRW.zip"),
        (1, "M2M_Settlement_srw", ["csv"], MISOMarketReportsURLBuilder.url_generator_YYYY_last, datetime.datetime(year=2024, month=10, day=1), "csv", "https://docs.misoenergy.org/marketreports/M2M_Settlement_srw_2025.csv"),
        (1, "Allocation_on_MISO_Flowgates", ["csv"], MISOMarketReportsURLBuilder.url_generator_YYYY_mm_dd_last, datetime.datetime(year=2024, month=10, day=29), "csv", "https://docs.misoenergy.org/marketreports/Allocation_on_MISO_Flowgates_2024_10_30.csv"),
    ]
)
def test_MISOMarketReportsURLBuilder_add_to_datetime(
    direction,
    target, 
    supported_extensions, 
    url_generator,
    ddatetime,
    file_extension,
    expected, 
):
    url_builder = MISOMarketReportsURLBuilder(
        target=target,
        supported_extensions=supported_extensions,
        url_generator=url_generator,
    )

    new_datetime = url_builder.add_to_datetime(
        ddatetime=ddatetime, 
        direction=direction,
    )

    url = url_builder.build_url(
        ddatetime=new_datetime,
        file_extension=file_extension,
    )

    assert url == expected, f"Expected {expected}, got {url}."
    

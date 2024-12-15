from typing import Callable
import datetime
import re

import pytest
import pandas as pd
import requests

from MISOReports.MISOReports import (
    MISORTWDDataBrokerURLBuilder,
    MISORTWDBIReporterURLBuilder,
    MISOMarketReportsURLBuilder,
    MISOReports,
)
from MISOReports.parsers import (
    MULTI_DF_DFS_COLUMN,
    MULTI_DF_NAMES_COLUMN,
)


def try_to_get_dfs(
        report_name: str, 
        datetime_increment_limit: int,
        number_of_dfs_to_stop_at: int,
) -> list[pd.DataFrame]:
    """Tries to get the df for the report_name and returns it. If a request fails, it will 
    increment the datetime and try again up to datetime_increment_limit times.

    :param str report_name: The name of the report to get the df for.
    :param int datetime_increment_limit: The number of times to try to get the df before raising an error.
    :param int number_of_dfs_to_stop_at: The number of successfully downloaded dfs to stop at.
    :return pd.DataFrame: The df for the report_name.
    """
    report_mappings = MISOReports.report_mappings
    report = report_mappings[report_name]

    increment_cnt = 0
    curr_target_date = report.example_datetime
    dfs = []
    while increment_cnt <= datetime_increment_limit:
        try:
            df = MISOReports.get_df(
                report_name=report_name,
                ddatetime=curr_target_date,
            )

            dfs.append(df)

            if len(dfs) >= number_of_dfs_to_stop_at:
                break
        except requests.HTTPError as e:
            curr_target_date = report.url_builder.add_to_datetime(
                ddatetime=curr_target_date, 
                direction=1,
            )
            increment_cnt += 1
    
    if increment_cnt > datetime_increment_limit:
        raise ValueError(f"Failed to get {report_name} after {datetime_increment_limit} attempts (last datetime tried: {curr_target_date}).")
    
    return dfs


def uses_correct_dtypes(
        df: pd.DataFrame,
        columns: list[str],
        dtype_checker: Callable[[object], bool],
) -> bool:
    """Checks if the columns in the df have the correct dtypes.

    :param pd.DataFrame df: The df to check the dtypes of.
    :param list[str] columns: The columns to check the dtypes of.
    :param Callable[[object], bool] dtype_checker: The function to check the dtypes with.
    :return bool: True if the columns have the correct dtypes, False otherwise.
    """
    for column in columns:
        if not dtype_checker(df[column]):
            return False
        
    return True


@pytest.fixture
def get_df_test_names():
    single_df_tests = [v[0] for v in single_df_test_list]
    multiple_dfs_tests = [v[0] for v in multiple_dfs_test_list]
    nsi_tests = nsi_test_list
    ftr_mpma_results_tests = ftr_mpma_results_test_list

    res = [
        *single_df_tests,
        *multiple_dfs_tests,
        *nsi_tests,
        *ftr_mpma_results_tests,
    ]

    return res


@pytest.fixture
def datetime_increment_limit(request):
    return request.config.getoption("--datetime-increments-limit")


@pytest.fixture
def number_of_dfs_to_stop_at(request):
    return request.config.getoption("--number-of-dfs-to-stop-at")


def test_MISOMarketReportsURLBuilder_add_to_datetime_has_an_increment_mapping_for_all_url_generators():
    url_generators = []
    for func_str in dir(MISOMarketReportsURLBuilder):
        func = getattr(MISOMarketReportsURLBuilder, func_str)
        if callable(func) and func_str.startswith("url_generator_"):
            url_generators.append(func)
    
    dummy_datetime = datetime.datetime.now()
    for url_generator in url_generators:
        obj = MISOMarketReportsURLBuilder(
            target="test",
            supported_extensions=["csv"],
            url_generator=url_generator,
        )

        try:
            obj.add_to_datetime(
                ddatetime=dummy_datetime, 
                direction=1,
            )
        except ValueError as e:
            raise AssertionError(f"{url_generator}: {e}")


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


single_df_test_list = [
    (
        "MISOsamedaydemand", 
        {
            ("PostedValue", "Hour", "UTCOffset",): pd.api.types.is_integer_dtype,
            ("Data_Code", "Data_Type", "PostingType",): pd.api.types.is_string_dtype,
            ("Data_Date",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "MISOdaily", 
        {
            ("PostedValue", "Hour", "UTCOffset",): pd.api.types.is_integer_dtype,
            ("Data_Code", "Data_Type", "PostingType",): pd.api.types.is_string_dtype,
            ("Data_Date",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "currentinterval", 
        {
            ("LMP", "MLC", "MCC",): pd.api.types.is_float_dtype,
            ("CPNODE",): pd.api.types.is_string_dtype,
            ("INTERVAL",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_bc_HIST", 
        {
            ("Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2",): pd.api.types.is_float_dtype,
            ("Override",): pd.api.types.is_integer_dtype,
            ("Flowgate NERCID", "Constraint_ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type",): pd.api.types.is_string_dtype,
            ("Market Date", "Hour of Occurrence",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "RT_UDS_Approved_Case_Percentage", 
        {
            ("Percentage",): pd.api.types.is_float_dtype,
            ("UDS Case ID",): pd.api.types.is_string_dtype,
            ("Dispatch Interval",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "Resource_Uplift_by_Commitment_Reason", 
        {
            ("ECONOMIC MAX",): pd.api.types.is_float_dtype,
            ("LOCAL RESOURCE ZONE",): pd.api.types.is_integer_dtype,
            ("REASON", "REASON ID",): pd.api.types.is_string_dtype,
            ("STARTTIME",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_rpe", 
        {
            ("Shadow Price",): pd.api.types.is_float_dtype,
            ("Constraint Name", "Constraint Description",): pd.api.types.is_string_dtype,
            ("Time of Occurence",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "Historical_RT_RSG_Commitment", 
        {
            ("TOTAL_ECON_MAX",): pd.api.types.is_float_dtype,
            ("COMMIT_REASON", "NUM_RESOURCES",): pd.api.types.is_string_dtype,
            ("MKT_INT_END_EST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "da_pbc", 
        {
            ("PRELIMINARY_SHADOW_PRICE",): pd.api.types.is_float_dtype,
            ("BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE",): pd.api.types.is_integer_dtype,
            ("CONSTRAINT_NAME", "CURVETYPE", "REASON",): pd.api.types.is_string_dtype,
            ("MARKET_HOUR_EST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "da_bc", 
        {
            ("Shadow Price", "BP1", "PC1", "BP2", "PC2",): pd.api.types.is_float_dtype,
            ("Hour of Occurrence", "Override",): pd.api.types.is_integer_dtype,
            ("Flowgate NERC ID", "Constraint_ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "da_bcsf", 
        {
            ("From KV", "To KV", "Direction",): pd.api.types.is_integer_dtype,
            ("Constraint ID", "Constraint Name", "Contingency Name", "Constraint Type", "Flowgate Name", "Device Type", "Key1", "Key2", "Key3", "From Area", "To Area", "From Station", "To Station",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "MARKET_SETTLEMENT_DATA_SRW", 
        {
            ("DATE",): pd.api.types.is_datetime64_ns_dtype,
            ("BILL_DET",): pd.api.types.is_string_dtype,
            ("HR01", "HR02", "HR03", "HR04", "HR05", "HR06", "HR07", "HR08", "HR09", "HR10", "HR11", "HR12", "HR13", "HR14", "HR15", "HR16", "HR17", "HR18", "HR19", "HR20", "HR21", "HR22", "HR23", "HR24",): pd.api.types.is_float_dtype,
        }
    ),
    (
        "combinedwindsolar", 
        {
            ("ForecastDateTimeEST", "ActualDateTimeEST",): pd.api.types.is_datetime64_ns_dtype,
            ("ForecastHourEndingEST", "ActualHourEndingEST",): pd.api.types.is_integer_dtype,
            ("ForecastWindValue", "ForecastSolarValue", "ActualWindValue", "ActualSolarValue",): pd.api.types.is_float_dtype,
        }
    ),
    (
        "ms_vlr_HIST_SRW", 
        {
            ("OPERATING DATE",): pd.api.types.is_datetime64_ns_dtype,
            ("DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total",): pd.api.types.is_float_dtype,
            ("SETTLEMENT RUN",): pd.api.types.is_integer_dtype,
            ("REGION", "CONSTRAINT",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "SolarForecast", 
        {
            ("DateTimeEST",): pd.api.types.is_datetime64_ns_dtype,
            ("HourEndingEST",): pd.api.types.is_integer_dtype,
            ("Value",): pd.api.types.is_float_dtype,
        }
    ),
    (
        "DA_LMPs", 
        {
            ("MARKET_DAY",): pd.api.types.is_datetime64_ns_dtype,
            ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): pd.api.types.is_float_dtype,
            ("NODE", "TYPE", "VALUE",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "rt_irsf", 
        {
            ("MKTHOUR_EST",): pd.api.types.is_datetime64_ns_dtype,
            ("INTRAREGIONAL_SCHEDULED_FLOW",): pd.api.types.is_float_dtype,
            ("CONSTRAINT_NAME",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "rt_mf", 
        {
            ("Unit Count", "Hour Ending",): pd.api.types.is_integer_dtype,
            ("Time Interval EST",): pd.api.types.is_datetime64_ns_dtype,
            ("Peak Flag", "Region Name", "Fuel Type",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "rt_ex", 
        {
            ("Committed (GW at Economic Maximum) - Forward", "Committed (GW at Economic Maximum) - Real-Time", "Committed (GW at Economic Maximum) - Delta", "Load (GW) - Forward", "Load (GW) - Real-Time", "Load (GW) - Delta", "Net Scheduled Imports (GW) - Forward", "Net Scheduled Imports (GW) - Real-Time", "Net Scheduled Imports (GW) - Delta", "Outages (GW at Economic Maximum) - Forward", "Outages (GW at Economic Maximum) - Real-Time", "Outages (GW at Economic Maximum) - Delta", "Offer Changes (GW at Economic Maximum) - Forward", "Offer Changes (GW at Economic Maximum) - Real-Time", "Offer Changes (GW at Economic Maximum) - Delta",): pd.api.types.is_float_dtype,
            ("Hour", "Real-Time Binding Constraints - (#)",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "df_al", 
        {
            ("LRZ1 MTLF (MWh)", "LRZ1 ActualLoad (MWh)", "LRZ2_7 MTLF (MWh)", "LRZ2_7 ActualLoad (MWh)", "LRZ3_5 MTLF (MWh)", "LRZ3_5 ActualLoad (MWh)", "LRZ4 MTLF (MWh)", "LRZ4 ActualLoad (MWh)", "LRZ6 MTLF (MWh)", "LRZ6 ActualLoad (MWh)", "LRZ8_9_10 MTLF (MWh)", "LRZ8_9_10 ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)",): pd.api.types.is_float_dtype,
            ("HourEnding",): pd.api.types.is_integer_dtype,
            ("Market Day",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rf_al", 
        {
            ("North MTLF (MWh)", "North ActualLoad (MWh)", "Central MTLF (MWh)", "Central ActualLoad (MWh)", "South MTLF (MWh)", "South ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)",): pd.api.types.is_float_dtype,
            ("HourEnding",): pd.api.types.is_integer_dtype,
            ("Market Day",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "da_rpe", 
        {
            ("Shadow Price",): pd.api.types.is_float_dtype,
            ("Hour of Occurence",): pd.api.types.is_integer_dtype,
            ("Constraint Name", "Constraint Description",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "da_ex", 
        {
            ("Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total",): pd.api.types.is_float_dtype,
            ("Hour",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "da_bc_HIST", 
        {
            ("Shadow Price", "BP1", "PC1", "BP2", "PC2",): pd.api.types.is_float_dtype,
            ("Hour of Occurrence", "Override",): pd.api.types.is_integer_dtype,
            ("Constraint Name", "Constraint_ID", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type",): pd.api.types.is_string_dtype,
            ("Market Date",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "cpnode_reszone", 
        {
            ("Reserve Zone",): pd.api.types.is_integer_dtype,
            ("CP Node Name",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "da_co", 
        {
            ("Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "MW", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): pd.api.types.is_float_dtype,
            ("Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope",): pd.api.types.is_integer_dtype,
            ("Region", "Unit Code",): pd.api.types.is_string_dtype,
            ("Date/Time Beginning (EST)", "Date/Time End (EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_co", 
        {
            ("Cleared MW1", "Cleared MW2", "Cleared MW3", "Cleared MW4", "Cleared MW5", "Cleared MW6", "Cleared MW7", "Cleared MW8", "Cleared MW9", "Cleared MW10", "Cleared MW11", "Cleared MW12", "Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): pd.api.types.is_float_dtype,
            ("Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope",): pd.api.types.is_integer_dtype,
            ("Region", "Unit Code",): pd.api.types.is_string_dtype,
            ("Mkthour Begin (EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "Dead_Node_Report", 
        {
            ("PNODE Name",): pd.api.types.is_string_dtype,
            ("Mkt Hour",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "asm_rt_co", 
        {
            ("RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP1", "RegMW1", "RegMCP2", "RegMW2", "RegMCP3", "RegMW3", "RegMCP4", "RegMW4", "RegMCP5", "RegMW5", "RegMCP6", "RegMW6", "RegMCP7", "RegMW7", "RegMCP8", "RegMW8", "RegMCP9", "RegMW9", "RegMCP10", "RegMW10", "RegMCP11", "RegMW11", "RegMCP12", "RegMW12", "SpinMCP1", "SpinMW1", "SpinMCP2", "SpinMW2", "SpinMCP3", "SpinMW3", "SpinMCP4", "SpinMW4", "SpinMCP5", "SpinMW5", "SpinMCP6", "SpinMW6", "SpinMCP7", "SpinMW7", "SpinMCP8", "SpinMW8", "SpinMCP9", "SpinMW9", "SpinMCP10", "SpinMW10", "SpinMCP11", "SpinMW11", "SpinMCP12", "SpinMW12", "SuppMCP1", "SuppMW1", "SuppMCP2", "SuppMW2", "SuppMCP3", "SuppMW3", "SuppMCP4", "SuppMW4", "SuppMCP5", "SuppMW5", "SuppMCP6", "SuppMW6", "SuppMCP7", "SuppMW7", "SuppMCP8", "SuppMW8", "SuppMCP9", "SuppMW9", "SuppMCP10", "SuppMW10", "SuppMCP11", "SuppMW11", "SuppMCP12", "SuppMW12", "StrOfflineOfferRate", "STRMCP1", "STRMW1", "STRMCP2", "STRMW2", "STRMCP3", "STRMW3", "STRMCP4", "STRMW4", "STRMCP5", "STRMW5", "STRMCP6", "STRMW6", "STRMCP7", "STRMW7", "STRMCP8", "STRMW8", "STRMCP9", "STRMW9", "STRMCP10", "STRMW10", "STRMCP11", "STRMW11", "STRMCP12", "STRMW12", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): pd.api.types.is_float_dtype,
            ("Region", "Unit Code",): pd.api.types.is_string_dtype,
            ("Mkthour Begin (EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "asm_da_co", 
        {
            ("RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP", "RegMW", "SpinMCP", "SpinMW", "SuppMCP", "SuppMW", "OfflineSTR", "STRMCP", "STRMW", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): pd.api.types.is_float_dtype,
            ("Region", "Unit Code",): pd.api.types.is_string_dtype,
            ("Date/Time Beginning (EST)", "Date/Time End (EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "M2M_Settlement_srw", 
        {
            ("MISO_SHADOW_PRICE", "CP_SHADOW_PRICE", "MISO_CREDIT", "CP_CREDIT",): pd.api.types.is_float_dtype,
            ("FLOWGATE_ID", "MONITORING_RTO", "CP_RTO", "FLOWGATE_NAME",): pd.api.types.is_string_dtype,
            ("MISO_MKT_FLOW", "MISO_FFE", "CP_MKT_FLOW", "CP_FFE",): pd.api.types.is_integer_dtype,
            ("HOUR_ENDING",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "M2M_Flowgates_as_of", 
        {
            ("Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "M2M_FFE", 
        {
            ("Non Monitoring RTO FFE", "Adjusted FFE",): pd.api.types.is_float_dtype,
            ("NERC Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description",): pd.api.types.is_string_dtype,
            ("Hour Ending",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "Allocation_on_MISO_Flowgates", 
        {
            ("Allocation (MW)",): pd.api.types.is_float_dtype,
            ("Allocation to Rating Percentage",): pd.api.types.is_integer_dtype,
            ("NERC ID", "Flowgate Owner", "Flowgate Description", "Entity", "Direction", "Reciprocal Status on Flowgate",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "rt_pbc", 
        {
            ("PRELIMINARY_SHADOW_PRICE",): pd.api.types.is_float_dtype,
            ("BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE",): pd.api.types.is_integer_dtype,
            ("CONSTRAINT_NAME", "CURVETYPE", "REASON",): pd.api.types.is_string_dtype,
            ("MARKET_HOUR_EST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_bc", 
        {
            ("Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2",): pd.api.types.is_float_dtype,
            ("Override",): pd.api.types.is_integer_dtype,
            ("Flowgate NERC ID", "Constraint ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type",): pd.api.types.is_string_dtype,
            ("Hour of Occurrence",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_or", 
        {
            ("Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2",): pd.api.types.is_float_dtype,
            ("Override",): pd.api.types.is_integer_dtype,
            ("Flowgate NERC ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason",): pd.api.types.is_string_dtype,
            ("Hour of Occurrence",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_fuel_on_margin", 
        {
            ("Hour Ending", "Unit Count",): pd.api.types.is_integer_dtype,
            ("Peak Flag", "Region Name", "Fuel Type",): pd.api.types.is_string_dtype,
            ("Time Interval EST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "5min_expost_mcp", 
        {
            ("RT MCP Regulation", "RT MCP Spin", "RT MCP Supp",): pd.api.types.is_float_dtype,
            ("Zone",): pd.api.types.is_integer_dtype,
            ("Time (EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "5min_exante_mcp", 
        {
            ("RT Ex-Ante MCP Regulation", "RT Ex-Ante MCP Spin", "RT Ex-Ante MCP Supp",): pd.api.types.is_float_dtype,
            ("Zone",): pd.api.types.is_integer_dtype,
            ("Time (EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "ftr_mpma_bids_offers", 
        {
            ("MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10",): pd.api.types.is_float_dtype,
            ("Market Name", "Source", "Sink", "Hedge Type", "Class", "Type", "Asset Owner ID",): pd.api.types.is_string_dtype,
            ("Start Date", "End Date",): pd.api.types.is_datetime64_ns_dtype,
            ("Round",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "ftr_annual_bids_offers", 
        {
            ("MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10",): pd.api.types.is_float_dtype,
            ("Market Name", "Source", "Sink", "Hedge Type", "Class", "Type", "Asset Owner ID",): pd.api.types.is_string_dtype,
            ("Start Date", "End Date",): pd.api.types.is_datetime64_ns_dtype,
            ("Round",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "bids_cb", 
        {
            ("MW", "LMP", "PRICE1", "MW1", "PRICE2", "MW2", "PRICE3", "MW3", "PRICE4", "MW4", "PRICE5", "MW5", "PRICE6", "MW6", "PRICE7", "MW7", "PRICE8", "MW8", "PRICE9", "MW9",): pd.api.types.is_float_dtype,
            ("Market Participant Code", "Region", "Type of Bid", "Bid ID",): pd.api.types.is_string_dtype,
            ("Date/Time Beginning (EST)", "Date/Time End (EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "5MIN_LMP", 
        {
            ("LMP", "CON_LMP", "LOSS_LMP",): pd.api.types.is_float_dtype,
            ("PNODENAME",): pd.api.types.is_string_dtype,
            ("MKTHOUR_EST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "RT_Load_EPNodes", 
        {
            ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): pd.api.types.is_float_dtype,
            ("EPNode", "Value",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "realtimebindingsrpbconstraints", 
        {
            ("Price",): pd.api.types.is_float_dtype,
            ("OVERRIDE", "BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4",): pd.api.types.is_integer_dtype,
            ("Name", "REASON", "CURVETYPE",): pd.api.types.is_string_dtype,
            ("Period",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "realtimebindingconstraints", 
        {
            ("Price",): pd.api.types.is_float_dtype,
            ("OVERRIDE", "BP1", "PC1", "BP2", "PC2",): pd.api.types.is_integer_dtype,
            ("Name", "CURVETYPE",): pd.api.types.is_string_dtype,
            ("Period",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "apiversion", 
        {
            ("Semantic",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "generationoutagesplusminusfivedays", 
        {
            ("Unplanned", "Planned", "Forced", "Derated",): pd.api.types.is_integer_dtype,
            ("OutageMonthDay",): pd.api.types.is_string_dtype,
            ("OutageDate",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_expost_str_mcp", 
        {
            ("RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8",): pd.api.types.is_float_dtype,
            ("Hour Ending",): pd.api.types.is_integer_dtype,
            ("Preliminary/ Final",): pd.api.types.is_string_dtype,
            ("MARKET DATE",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_expost_str_5min_mcp", 
        {
            ("RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8",): pd.api.types.is_float_dtype,
            ("Preliminary/ Final",): pd.api.types.is_string_dtype,
            ("Time(EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_expost_ramp_mcp", 
        {
            ("Reserve Zone 1 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post Hourly",): pd.api.types.is_float_dtype,
            ("Hour Ending",): pd.api.types.is_integer_dtype,
            ("Preliminary / Final",): pd.api.types.is_string_dtype,
            ("Market Date",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rt_expost_ramp_5min_mcp", 
        {
            ("Reserve Zone 1 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post 5 Min",): pd.api.types.is_float_dtype,
            ("Preliminary / Final",): pd.api.types.is_string_dtype,
            ("Time (EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "da_expost_str_mcp", 
        {
            ("Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8",): pd.api.types.is_float_dtype,
            ("Hour Ending",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "da_expost_ramp_mcp", 
        {
            ("Reserve Zone 1 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Post 1 Hour",): pd.api.types.is_float_dtype,
            ("Hour Ending",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "da_exante_str_mcp", 
        {
            ("Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8",): pd.api.types.is_float_dtype,
            ("Hour Ending",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "da_exante_ramp_mcp", 
        {
            ("Reserve Zone 1 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Ante 1 Hour",): pd.api.types.is_float_dtype,
            ("Hour Ending",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "regionaldirectionaltransfer", 
        {
            ("NORTH_SOUTH_LIMIT", "SOUTH_NORTH_LIMIT", "RAW_MW", " UDSFLOW_MW",): pd.api.types.is_integer_dtype,
            ("INTERVALEST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "NAI", 
        {
            ("Value",): pd.api.types.is_float_dtype,
            ("Name",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "Total_Uplift_by_Resource", 
        {
            ("Total Uplift Amount",): pd.api.types.is_float_dtype,
            ("Resource Name",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "ccf_co", 
        {
            ("HOUR1", "HOUR2", "HOUR3", "HOUR4", "HOUR5", "HOUR6", "HOUR7", "HOUR8", "HOUR9", "HOUR10", "HOUR11", "HOUR12", "HOUR13", "HOUR14", "HOUR15", "HOUR16", "HOUR17", "HOUR18", "HOUR19", "HOUR20", "HOUR21", "HOUR22", "HOUR23", "HOUR24",): pd.api.types.is_float_dtype,
            ("CONSTRAINT NAME", "NODE NAME",): pd.api.types.is_string_dtype,
            ("OPERATING DATE",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "ms_vlr_HIST", 
        {
            ("DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total",): pd.api.types.is_float_dtype,
            ("SETTLEMENT RUN",): pd.api.types.is_integer_dtype,
            ("REGION", "CONSTRAINT",): pd.api.types.is_string_dtype,
            ("OPERATING DATE",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "fuelmix", 
        {
            ("ACT", "TOTALMW",): pd.api.types.is_integer_dtype,
            ("CATEGORY",): pd.api.types.is_string_dtype,
            ("INTERVALEST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "ace", 
        {
            ("value",): pd.api.types.is_float_dtype,
            ("instantEST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "cts", 
        {
            ("PJMFORECASTEDLMP",): pd.api.types.is_float_dtype,
            ("CASEAPPROVALDATE", "SOLUTIONTIME",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "WindForecast", 
        {
            ("Value",): pd.api.types.is_float_dtype,
            ("HourEndingEST",): pd.api.types.is_integer_dtype,
            ("DateTimeEST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "Wind", 
        {
            ("ForecastValue", "ActualValue",): pd.api.types.is_float_dtype,
            ("ForecastHourEndingEST", "ActualHourEndingEST",): pd.api.types.is_integer_dtype,
            ("ForecastDateTimeEST", "ActualDateTimeEST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "Solar", 
        {
            ("ForecastValue", "ActualValue",): pd.api.types.is_float_dtype,
            ("ForecastHourEndingEST", "ActualHourEndingEST",): pd.api.types.is_integer_dtype,
            ("ForecastDateTimeEST", "ActualDateTimeEST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "exantelmp", 
        {
            ("LMP", "Loss", "Congestion",): pd.api.types.is_float_dtype,
            ("Name",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "da_exante_lmp", 
        {
            ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
            ("Node", "Type", "Value",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "da_expost_lmp", 
        {
            ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
            ("Node", "Type", "Value",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "rt_lmp_final", 
        {
            ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
            ("Node", "Type", "Value",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "rt_lmp_prelim", 
        {
            ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
            ("Node", "Type", "Value",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "DA_Load_EPNodes", 
        {
            ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): pd.api.types.is_float_dtype,
            ("EPNode", "Value",): pd.api.types.is_string_dtype,
        }
    ),
    (
        "5min_exante_lmp", 
        {
            ("RT Ex-Ante LMP", "RT Ex-Ante MEC", "RT Ex-Ante MLC", "RT Ex-Ante MCC",): pd.api.types.is_float_dtype,
            ("CP Node",): pd.api.types.is_string_dtype,
            ("Time (EST)",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "SolarActual", 
        {
            ("Value",): pd.api.types.is_float_dtype,
            ("HourEndingEST",): pd.api.types.is_integer_dtype,
            ("DateTimeEST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "WindActual", 
        {
            ("Value",): pd.api.types.is_float_dtype,
            ("HourEndingEST",): pd.api.types.is_integer_dtype,
            ("DateTimeEST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "RSG", 
        {
            ("TOTAL_ECON_MAX",): pd.api.types.is_float_dtype,
            ("COMMIT_REASON", "NUM_RESOURCES",): pd.api.types.is_string_dtype,
            ("MKT_INT_END_EST",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "reservebindingconstraints", 
        {
            ("Price",): pd.api.types.is_float_dtype,
            ("Name", "Description",): pd.api.types.is_string_dtype,
            ("Period",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "importtotal5", 
        {
            ("Value",): pd.api.types.is_float_dtype,
            ("Time",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "nsi5miso", 
        {
            ("timestamp",): pd.api.types.is_datetime64_ns_dtype,
            ("NSI",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "nsi1miso", 
        {
            ("NSI",): pd.api.types.is_integer_dtype,
            ("timestamp",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "RT_LMPs",
        {
            ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): pd.api.types.is_float_dtype,
            ("NODE", "TYPE", "VALUE",): pd.api.types.is_string_dtype,
            ("MARKET_DAY",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "dfal_HIST",
        {
            ("MTLF (MWh)", "ActualLoad (MWh)",): pd.api.types.is_float_dtype,
            ("HourEnding",): pd.api.types.is_integer_dtype,
            ("LoadResource Zone",): pd.api.types.is_string_dtype,
            ("MarketDay",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "historical_gen_fuel_mix", 
        {
            ("DA Cleared UDS Generation", "[RT Generation State Estimator",): pd.api.types.is_float_dtype,
            ("HourEnding",): pd.api.types.is_integer_dtype,
            ("Region", "Fuel Type",): pd.api.types.is_string_dtype,
            ("Market Date",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "hwd_HIST", 
        {
            ("MWh",): pd.api.types.is_float_dtype,
            ("Hour Ending",): pd.api.types.is_integer_dtype,
            ("Market Day	",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "sr_hist_is",
        {
            ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): pd.api.types.is_integer_dtype,
            ("INTERFACE",): pd.api.types.is_string_dtype,
            ("MKTDAY",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "rfal_HIST", 
        {
            ("MTLF (MWh)", "Actual Load (MWh)",): pd.api.types.is_float_dtype,
            ("HourEnding",): pd.api.types.is_integer_dtype,
            ("Region", "Footnote",): pd.api.types.is_string_dtype,
            ("Market Day",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "sr_lt",
         {
            ("Minimum (GW)", "Average (GW)", "Maximum (GW)",): pd.api.types.is_float_dtype,
            ("Week Starting",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
    (
        "sr_nd_is",
        {
            ("Hour", "GLHB", "IESO", "MHEB", "PJM", "SOCO", "SWPP", "TVA", "AECI", "LGEE", "Other", "Total",): pd.api.types.is_integer_dtype,
        }
    ),
    (
        "sr_tcdc_group2",
        {
            ("BP1", "PC1", "BP2", "PC2",): pd.api.types.is_float_dtype,
            ("ContingencyName", "ContingencyDescription", "BranchName", "CurveName", "Reason",): pd.api.types.is_string_dtype,
            ("EffectiveTime", "TerminationTime",): pd.api.types.is_datetime64_ns_dtype,
        }
    ),
]


@pytest.mark.parametrize(
    "report_name, columns_mapping", single_df_test_list
)
def test_get_df_single_df_correct_columns(report_name, columns_mapping, datetime_increment_limit, number_of_dfs_to_stop_at):
    dfs = try_to_get_dfs(
        report_name=report_name,
        datetime_increment_limit=datetime_increment_limit,
        number_of_dfs_to_stop_at=number_of_dfs_to_stop_at,
    )

    for df in dfs: 
        columns_mapping_columns = []
        for columns_group in columns_mapping.keys():
            columns_mapping_columns.extend(columns_group)
            
        columns_mapping_columns_set = frozenset(columns_mapping_columns)
        df_columns_set = frozenset(df.columns)

        if columns_mapping_columns_set != df_columns_set:
            raise ValueError(f"Expected columns {columns_mapping_columns_set} do not match df columns {df_columns_set}.")

        for columns_tuple, dtype_checker in columns_mapping.items():
            columns = list(columns_tuple)
            
            assert uses_correct_dtypes(df, columns, dtype_checker), \
                f"For report {report_name}, columns {columns} are not of type {dtype_checker}."


multiple_dfs_test_list = [
    (
        "ms_rnu_srw",
        {
            "MKT TOT": {
                ("JOA_MISO_UPLIFT", "MISO_RT_GFACO_DIST", "MISO_RT_GFAOB_DIST", "MISO_RT_RSG_DIST2", "RT_CC", "DA_RI", "RT_RI", "ASM_RI", "STRDFC_UPLIFT", "CRDFC_UPLIFT", "MISO_PV_MWP_UPLIFT", "MISO_DRR_COMP_UPL", "MISO_TOT_MIL_UPL", "RC_DIST", "TOTAL RNU",): pd.api.types.is_float_dtype,
                ("previous 36 months",): pd.api.types.is_string_dtype,
                ("START", "STOP",): pd.api.types.is_datetime64_ns_dtype,
            },
            "hourly miso_rt_bill_mtr": {
                ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): pd.api.types.is_float_dtype,
                ("CHANNEL",): pd.api.types.is_integer_dtype,
                ("BILL_DETERMINANT",): pd.api.types.is_string_dtype,
                ("STARTTIME",): pd.api.types.is_datetime64_ns_dtype,
            },
            "RT CC JOA column": {
                ("RT CC", "RT JOA", "NET",): pd.api.types.is_float_dtype,
                ("HRBEG",): pd.api.types.is_datetime64_ns_dtype,
            },
        },
    ),
    (
        "PeakHourOverview",
        {
            "SYSTEM RESOURCE CAPACITY": {
                ("Committed + Available Short-Lead Generation", "NSI", "Behind-Meter Generation", "Total Resources",): pd.api.types.is_integer_dtype,
            },
            "SYSTEM OBLIGATION": {
               	("Forecasted Load", "Operating Reserve Requirement", "Total Obligation", "FORECASTED CAPACITY MARGIN",): pd.api.types.is_integer_dtype,
            },
        },
    ),
    (
        "ftr_allocation_stage_1B",
        {
            "Fall": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
            "Spring": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
            "Summer": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
            "Winter": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "ftr_allocation_stage_1A",
        {
            "Fall": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
            "Spring": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
            "Summer": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
            "Winter": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "ftr_allocation_restoration",
        {
            "Fall": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
            "Spring": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
            "Summer": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
            "Winter": {
                ("Limit", "Flow", "Violation",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class", "Stage",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "AncillaryServicesMCP",
        {
            "RealTimeMCP": {
                ("number",): pd.api.types.is_integer_dtype,
                ("GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp",): pd.api.types.is_float_dtype,
            },
            "DayAheadMCP": {
                ("number",): pd.api.types.is_integer_dtype,
                ("GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp",): pd.api.types.is_float_dtype,
            },
        },
    ),
    (
        "da_pr",
        {
            "Table 1": {
                ("Type",): pd.api.types.is_string_dtype,
                ("Demand Fixed", " Demand Price Sensitive", "Demand Virtual", "Demand Total",): pd.api.types.is_float_dtype,
            },
            "Table 2": {
                ("Type",): pd.api.types.is_string_dtype,
                ("Supply Physical", "Supply Virtual", "Supply Total",): pd.api.types.is_float_dtype,
            },
            "Table 3": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): pd.api.types.is_float_dtype,
                ("Hour",): pd.api.types.is_integer_dtype,
            },
            "Table 4": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): pd.api.types.is_float_dtype,
                ("Around the Clock",): pd.api.types.is_string_dtype,
            },
            "Table 5": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): pd.api.types.is_float_dtype,
                ("On-Peak",): pd.api.types.is_string_dtype,  
            },
            "Table 6": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): pd.api.types.is_float_dtype,
                ("Off-Peak",): pd.api.types.is_string_dtype, 
            },
        },
    ),
    (
        "asm_rtmcp_prelim",
        {
            "Table 1": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
                ("MCP Type",): pd.api.types.is_string_dtype,
            },
            "Table 2": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
                ("Zone",): pd.api.types.is_integer_dtype,
                ("Pnode", "MCP Type",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "asm_rtmcp_final",
        {
            "Table 1": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
                ("MCP Type",): pd.api.types.is_string_dtype,
            },
            "Table 2": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
                ("Zone",): pd.api.types.is_integer_dtype,
                ("Pnode", "MCP Type",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "asm_expost_damcp",
        {
            "Table 1": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
                ("MCP Type",): pd.api.types.is_string_dtype,
            },
            "Table 2": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
                ("Zone",): pd.api.types.is_integer_dtype,
                ("Pnode", "MCP Type",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "ftr_annual_results_round_1",
        {
            "Metadata": {
                ("File 1", "File 2", "File 3", "File 4", "File 5", "File 6", "File 7", "File 8", "File 9", "File 10", "File 11", "File 12",): pd.api.types.is_string_dtype,
            },
            "File 1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 2": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 3": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 4": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 5": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 6": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 7": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 8": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 9": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
            "File 10": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
            "File 11": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
            "File 12": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "ftr_annual_results_round_2",
        {
            "Metadata": {
                ("File 1", "File 2", "File 3", "File 4", "File 5", "File 6", "File 7", "File 8", "File 9", "File 10", "File 11", "File 12",): pd.api.types.is_string_dtype,
            },
            "File 1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,

            },
            "File 2": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,

            },
            "File 3": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,

            },
            "File 4": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,

            },
            "File 5": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 6": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 7": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 8": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 9": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
            "File 10": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
            "File 11": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
            "File 12": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "ftr_annual_results_round_3",
        {
            "Metadata": {
                ("File 1", "File 2", "File 3", "File 4", "File 5", "File 6", "File 7", "File 8", "File 9", "File 10", "File 11", "File 12",): pd.api.types.is_string_dtype,
            },
            "File 1": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,

            },
            "File 2": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,

            },
            "File 3": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,

            },
            "File 4": {
                ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
                ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
                ("Round",): pd.api.types.is_integer_dtype,

            },
            "File 5": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 6": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 7": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 8": {
                ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
                ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
                ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
            },
            "File 9": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
            "File 10": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
            "File 11": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
            "File 12": {
                ("ShadowPrice",): pd.api.types.is_float_dtype,
                ("Round",): pd.api.types.is_integer_dtype,
                ("SourceSink", "Class",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "sr_ctsl",
        {
            "Cost Paid by Load - Cur Year": {
                ("Jan Cur Year", "Feb Cur Year", "Mar Cur Year", "Apr Cur Year", "May Cur Year", "Jun Cur Year", "Jul Cur Year", "Aug Cur Year", "Sep Cur Year", "Oct Cur Year", "Nov Cur Year", "Dec Cur Year",): pd.api.types.is_float_dtype,    
                ("Cost Paid by Load (Hourly Avg per Month)",): pd.api.types.is_string_dtype,
            },
            "Cost Paid by Load - Prior Year": {
                ("Jan Prior Year", "Feb Prior Year", "Mar Prior Year", "Apr Prior Year", "May Prior Year", "Jun Prior Year", "Jul Prior Year", "Aug Prior Year", "Sep Prior Year", "Oct Prior Year", "Nov Prior Year", "Dec Prior Year",): pd.api.types.is_float_dtype,
                ("Cost Paid by Load (Hourly Avg per Month)",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "rt_pr",
        {
            "Table 1": {
                ("Demand", "Supply", "Total",): pd.api.types.is_float_dtype,
                ("Type",): pd.api.types.is_string_dtype,
            },
            "Table 2": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): pd.api.types.is_float_dtype,
                ("Hour",): pd.api.types.is_integer_dtype,
            },
            "Table 3": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): pd.api.types.is_float_dtype,
                ("Around the Clock",): pd.api.types.is_string_dtype,
            },
            "Table 4": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): pd.api.types.is_float_dtype,
                ("On-Peak",): pd.api.types.is_string_dtype,  
            },
            "Table 5": {
                ("MISO System", "Illinois Hub", "Michigan Hub", "Minnesota Hub", "Indiana Hub", "Arkansas Hub", "Louisiana Hub", "Texas Hub", "MS.HUB",): pd.api.types.is_float_dtype,
                ("Off-Peak",): pd.api.types.is_string_dtype, 
            },
        },
    ),
    (
        "ms_vlr_srw",
        {
            "Central": {
                ("DA VLR RSG MWP", "RT VLR RSG MWP", "DA+RT Total",): pd.api.types.is_float_dtype,
                ("Constraint",): pd.api.types.is_string_dtype,
            },
            "South": {
                ("DA VLR RSG MWP", "RT VLR RSG MWP", "DA+RT Total",): pd.api.types.is_float_dtype,
                ("Constraint",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "Daily_Uplift_by_Local_Resource_Zone",
        {
            "LRZ 1": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
            "LRZ 10": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
            "LRZ 2": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
            "LRZ 3": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
            "LRZ 4": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
            "LRZ 5": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
            "LRZ 6": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
            "LRZ 7": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
            "LRZ 8": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
            "LRZ 9": {
                ("Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "totalload",
        {
           "ClearedMW": {
               	("Load_Value",): pd.api.types.is_float_dtype,
                ("Load_Hour",): pd.api.types.is_integer_dtype,
           },
           "MediumTermLoadForecast": {
               	("Load_Forecast",): pd.api.types.is_float_dtype,
                ("Hour_End",): pd.api.types.is_integer_dtype,
           },
           "FiveMinTotalLoad": {
               	("Load_Value",): pd.api.types.is_float_dtype,
                ("Load_Time",): pd.api.types.is_datetime64_ns_dtype,
           },
        },
    ),
    (
        "asm_exante_damcp",
        {
           "Table 1": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
                ("MCP Type",): pd.api.types.is_string_dtype,
           },
           "Table 2": {
                ("HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24",): pd.api.types.is_float_dtype,
                ("Pnode", "MCP Type",): pd.api.types.is_string_dtype,
                ("Zone",): pd.api.types.is_integer_dtype,
           },
        },
    ),
    (
        "sr_gfm",
        {
           "RT Generation Fuel Mix Central": {
                ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW",): pd.api.types.is_float_dtype,
	            ("Market Hour Ending",): pd.api.types.is_string_dtype,
           },
           "RT Generation Fuel Mix North": {
                ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW",): pd.api.types.is_float_dtype,
	            ("Market Hour Ending",): pd.api.types.is_string_dtype,
           },
           "RT Generation Fuel Mix South": {
                ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW",): pd.api.types.is_float_dtype,
	            ("Market Hour Ending",): pd.api.types.is_string_dtype,
           },
           "RT Generation Fuel Mix Totals": {
                ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO",): pd.api.types.is_float_dtype,
	            ("Market Hour Ending",): pd.api.types.is_string_dtype,
           },
           "DA Cleared Generation Fuel Mix Central": {
                ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW",): pd.api.types.is_float_dtype,
	            ("Market Hour Ending",): pd.api.types.is_string_dtype,
           },
           "DA Cleared Generation Fuel Mix North": {
                ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW",): pd.api.types.is_float_dtype,
	            ("Market Hour Ending",): pd.api.types.is_string_dtype,
           },
           "DA Cleared Generation Fuel Mix South": {
                ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW",): pd.api.types.is_float_dtype,
	            ("Market Hour Ending",): pd.api.types.is_string_dtype,
           },
           "DA Cleared Generation Fuel Mix Totals": {
                ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO",): pd.api.types.is_float_dtype,
	            ("Market Hour Ending",): pd.api.types.is_string_dtype,
           },
        },
    ),
    (
        "mom",
        {
           "6 DAYS AHEAD DATES": {
	            ("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6",): pd.api.types.is_string_dtype,
           },
           "MISO": {
                ("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6",): pd.api.types.is_float_dtype,
	            ("Resources",): pd.api.types.is_string_dtype,
           },
           "NORTH": {
            	("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6",): pd.api.types.is_float_dtype,
	            ("Resources",): pd.api.types.is_string_dtype,
           },
           "CENTRAL": {
            	("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6",): pd.api.types.is_float_dtype,
	            ("Resources",): pd.api.types.is_string_dtype,
           },
           "NORTH+CENTRAL": {
                ("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6",): pd.api.types.is_float_dtype,
                ("Resources",): pd.api.types.is_string_dtype,
           },
           "SOUTH": {
            	("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6",): pd.api.types.is_float_dtype,
	            ("Resources",): pd.api.types.is_string_dtype,
           },
           "SOLAR HOURLY": {
                ("North", "Central", "South", "MISO",): pd.api.types.is_float_dtype,
                ("DAY HE",): pd.api.types.is_string_dtype,
           },
           "WIND HOURLY": {
                ("North", "Central", "South", "MISO",): pd.api.types.is_float_dtype,
                ("DAY HE",): pd.api.types.is_string_dtype,
           },
           "WIND UNCERTAINTY": {
                ("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6",): pd.api.types.is_float_dtype,
                ("Wind Uncertainty",): pd.api.types.is_string_dtype,
           },
           "LOAD UNCERTAINTY": {
                ("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6",): pd.api.types.is_float_dtype,
                ("Load Uncertainty",): pd.api.types.is_string_dtype,
           },
           "7 DAYS AHEAD DATES": {
	            ("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7",): pd.api.types.is_string_dtype,
           },
           "OUTAGE 7-DAY LOOK-AHEAD": {
                ("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7",): pd.api.types.is_float_dtype,
                ("Location", "Type",): pd.api.types.is_string_dtype,
           },
           "30 DAYS BACK DATES": {
	            ("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "Day 8", "Day 9", "Day 10", "Day 11", "Day 12", "Day 13", "Day 14", "Day 15", "Day 16", "Day 17", "Day 18", "Day 19", "Day 20", "Day 21", "Day 22", "Day 23", "Day 24", "Day 25", "Day 26", "Day 27", "Day 28", "Day 29", "Day 30",): pd.api.types.is_string_dtype,
           },
           "OUTAGE 30-DAY LOOK-BACK": {
                ("Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "Day 8", "Day 9", "Day 10", "Day 11", "Day 12", "Day 13", "Day 14", "Day 15", "Day 16", "Day 17", "Day 18", "Day 19", "Day 20", "Day 21", "Day 22", "Day 23", "Day 24", "Day 25", "Day 26", "Day 27", "Day 28", "Day 29", "Day 30",): pd.api.types.is_float_dtype,
                ("Location", "Type",): pd.api.types.is_string_dtype,
           },
        },
    ),
    (
        "ftr_allocation_summary",
        {
            "Stage 2 Residual": {
                ("STAGE2MW", "STAGE2PAYMENT",): pd.api.types.is_float_dtype,
                ("ID_TOU",): pd.api.types.is_string_dtype,
                ("START_DATE",): pd.api.types.is_datetime64_ns_dtype,
            },
            "ARR Annual Allocation Summary": {
                ("MW",): pd.api.types.is_float_dtype,
                ("MARKET_NAME", "ID_TOU", "SOURCE_NAME", "SINK_NAME", "STAGE", "TYPE",): pd.api.types.is_string_dtype,
                ("DATE_START", "DATE_END",): pd.api.types.is_datetime64_ns_dtype,
            },
        },
    ),
    (
        "MM_Annual_Report",
        {
            "MISO Year 1":
            {
                ("MISO Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "MISO Year 2":
            {
                ("MISO Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "MISO Year 3":
            {
                ("MISO Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "MISO Year 4":
            {
                ("MISO Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "Central Year 1":
            {
                ("Central Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "Central Year 2":
            {
                ("Central Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "Central Year 3":
            {
                ("Central Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "Central Year 4":
            {
                ("Central Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "North Year 1":
            {
                ("North Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "North Year 2":
            {
                ("North Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "North Year 3":
            {
                ("North Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "North Year 4":
            {
                ("North Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "South Year 1":
            {
                ("South Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "South Year 2":
            {
                ("South Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "South Year 3":
            {
                ("South Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "South Year 4":
            {
                ("South Available Margin (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "Transparency Future":
            {
                ("Central Region (MW)", "North Region (MW)", "South Region (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
            "Transparency History":
            {
                ("Central Region (MW)", "North Region (MW)", "South Region (MW)",): pd.api.types.is_float_dtype,
                ("Date",): pd.api.types.is_datetime64_ns_dtype,
            },
        },
    ),
    (
        "ms_rsg_srw", 
        {
            "MKT TOT": {
                ("MISO_RT_RSG_DIST2", "RT_RSG_DIST1", "RT_RSG_MWP", "DA_RSG_MWP", "DA_RSG_DIST",): pd.api.types.is_float_dtype,
                ("previous 36 months",): pd.api.types.is_string_dtype,
                ("START", "STOP",): pd.api.types.is_datetime64_ns_dtype,
            },
            "ATC CMC rate": {
                ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): pd.api.types.is_float_dtype,
                ("CHNL NBR",): pd.api.types.is_integer_dtype,
                ("BILL_DETERMINANT", "CONSTRAINT NAME",): pd.api.types.is_string_dtype,
                ("OPERATING DATE",): pd.api.types.is_datetime64_ns_dtype,
            },
            "MISO DDC rate": {
                ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): pd.api.types.is_float_dtype,
                ("CHNL NBR",): pd.api.types.is_integer_dtype,
                ("BILL_DETERMINANT",): pd.api.types.is_string_dtype,
                ("OPERATING DATE",): pd.api.types.is_datetime64_ns_dtype,
            },
            "VLR DIST": {
                ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): pd.api.types.is_float_dtype,
                ("CHNL NBR",): pd.api.types.is_integer_dtype,
                ("BILL_DETERMINANT",): pd.api.types.is_string_dtype,
                ("OPERATING DATE",): pd.api.types.is_datetime64_ns_dtype,
            },
            "RSG MONTHLY": {
                ("DA NVLR DIST", "DA VLR DIST", "RT VLR DIST", "MISO CMC DIST", "MISO DDC DIST", "MISO RT RSG DIST2",): pd.api.types.is_float_dtype,
                ("OPERATING MONTH",): pd.api.types.is_datetime64_ns_dtype,
            },
        },
    ),
    (
        "ms_ri_srw",
        {
            "MKT TOT": {
                ("DA RI", "RT RI", "TOTAL RI",): pd.api.types.is_float_dtype,
                ("Previous Months",): pd.api.types.is_string_dtype,
                ("START", "STOP",): pd.api.types.is_datetime64_ns_dtype,
            },
            "hourly column Worksheet": {
                ("Total RI hourly", "Total RI cumulative", "DA_RI hourly", "DA_RI cumulative", "RT_RI hourly", "RT_RI cumulative",): pd.api.types.is_float_dtype,
                ("hrend",): pd.api.types.is_integer_dtype,
                ("date",): pd.api.types.is_datetime64_ns_dtype,
            },
        },
    ),
    (
        "ms_ecf_srw",
        {
            "MKT TOT": {
                ("Da Xs Cg Fnd", "Rt Cc", "Rt Xs Cg Fnd", "Ftr Auc Res", "Ao Ftr Mn Alc", "Ftr Yr Alc *", "Tbs Access", "Net Ecf", "Ftr Shrtfll", "Net Ftr Sf", "Ftr Trg Cr Alc", "Ftr Hr Alc", "Hr Mf", "Hourly Ftr Allocation", "Monthly Ftr Allocation",): pd.api.types.is_float_dtype,
                ("Type",): pd.api.types.is_string_dtype,
                ("Start", "Stop",): pd.api.types.is_datetime64_ns_dtype,
            },
            "JOA Hourly Totals": {
                ("DA_JOA", "RT_JOA",): pd.api.types.is_float_dtype,
                ("CNTR_RTO",): pd.api.types.is_string_dtype,
                ("HRBEG",): pd.api.types.is_datetime64_ns_dtype,
            },
            "RT CC JOA column": {
                ("RT CC", "RT JOA", "NET",): pd.api.types.is_float_dtype,
                ("HRBEG",): pd.api.types.is_datetime64_ns_dtype,
            },
            "ECF": {
                ("DA_ECF", "RT_ECF", "DART_ECF", "DART_monthly",): pd.api.types.is_float_dtype,
                ("OD",): pd.api.types.is_datetime64_ns_dtype,
            },
        },
    ),
    (
        "sr_la_rg",
        {
            "Date Columns": {
                ("Column 1", "Column 2", "Column 3", "Column 4", "Column 5", "Column 6", "Column 7", "Column 8", "Column 9", "Column 10", "Column 11", "Column 12", "Column 13", "Column 14",): pd.api.types.is_string_dtype,
            },
            "Table 1": {
                ("Column 1", "Column 2", "Column 3", "Column 4", "Column 5", "Column 6", "Column 7", "Column 8", "Column 9", "Column 10", "Column 11", "Column 12", "Column 13", "Column 14",): pd.api.types.is_float_dtype,
                ("Hourend_EST",): pd.api.types.is_integer_dtype,
                ("Region",): pd.api.types.is_string_dtype,
            },
            "Table 2": {
                ("Column 1", "Column 2", "Column 3", "Column 4", "Column 5", "Column 6", "Column 7", "Column 8", "Column 9", "Column 10", "Column 11", "Column 12", "Column 13", "Column 14",): pd.api.types.is_float_dtype,
                ("Type", "Region",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "da_ex_rg", 
        {
            "Summary": {
                ("Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total",): pd.api.types.is_float_dtype,
                ("Hour Ending",): pd.api.types.is_integer_dtype,
            },
            "Regional Level": {
                ("Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total",): pd.api.types.is_float_dtype,
                ("Hour Ending",): pd.api.types.is_integer_dtype,
                ("Region",): pd.api.types.is_string_dtype,
            },
        },
    ),
    (
        "lmpconsolidatedtable", 
        {
            "Metadata": {
                ("Type",): pd.api.types.is_string_dtype,
	            ("Timing",): pd.api.types.is_datetime64_ns_dtype,
            },
            "Data": {
                ("LMP - FiveMinLMP", "MLC - FiveMinLMP", "MCC - FiveMinLMP", "REGMCP - FiveMinLMP", "REGMILEAGEMCP - FiveMinLMP", "SPINMCP - FiveMinLMP", "SUPPMCP - FiveMinLMP", "STRMCP - FiveMinLMP", "RCUPMCP - FiveMinLMP", "RCDOWNMCP - FiveMinLMP", "LMP - HourlyIntegratedLmp", "MLC - HourlyIntegratedLmp", "MCC - HourlyIntegratedLmp", "LMP - DayAheadExAnteLmp", "MLC - DayAheadExAnteLmp", "MCC - DayAheadExAnteLmp", "LMP - DayAheadExPostLmp", "MLC - DayAheadExPostLmp", "MCC - DayAheadExPostLmp",): pd.api.types.is_float_dtype,
	            ("Name",): pd.api.types.is_string_dtype,
            },
        }
    ),
]


@pytest.mark.parametrize(
    "report_name, dfs_mapping", multiple_dfs_test_list
)
def test_get_df_multiple_dfs_correct_columns_and_matching_df_names(report_name, dfs_mapping, datetime_increment_limit, number_of_dfs_to_stop_at):
    dfs = try_to_get_dfs(
        report_name=report_name,
        datetime_increment_limit=datetime_increment_limit,
        number_of_dfs_to_stop_at=number_of_dfs_to_stop_at,
    )

    for df in dfs:
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

            for columns_tuple, dtype_checker in columns_mapping.items():
                columns = list(columns_tuple)

                assert uses_correct_dtypes(res_df, columns, dtype_checker), \
                    f"For multi-df report {report_name}, df {df_name}, columns {columns} do not pass {dtype_checker.__name__}."


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


@pytest.mark.parametrize(
    "direction, target, ddatetime, expected", [
        (4, "DA_Load_EPNodes", datetime.datetime(year=2024, month=10, day=21), datetime.datetime(year=2024, month=10, day=25)),
        (1, "da_exante_lmp", datetime.datetime(year=2024, month=10, day=26), datetime.datetime(year=2024, month=10, day=27)),
        (1, "da_expost_lmp", datetime.datetime(year=2024, month=10, day=26), datetime.datetime(year=2024, month=10, day=27)),
        (-1, "DA_LMPs", datetime.datetime(year=2024, month=7, day=1), datetime.datetime(year=2024, month=4, day=1)),
        (0, "DA_LMPs", datetime.datetime(year=2024, month=11, day=1), datetime.datetime(year=2024, month=11, day=1)),
        (-3, "rt_expost_str_5min_mcp", datetime.datetime(year=2024, month=10, day=1), datetime.datetime(year=2024, month=7, day=1)),
        (1, "MARKET_SETTLEMENT_DATA_SRW", datetime.datetime(year=2024, month=10, day=1), datetime.datetime(year=2024, month=10, day=1)),
        (1, "M2M_Settlement_srw", datetime.datetime(year=2024, month=10, day=1), datetime.datetime(year=2025, month=10, day=1)),
        (1, "Allocation_on_MISO_Flowgates", datetime.datetime(year=2024, month=10, day=29), datetime.datetime(year=2024, month=10, day=30)),
    ]
)
def test_MISOMarketReports_add_to_datetime(
        direction,
        target, 
        ddatetime,
        expected, 
):
    new_datetime = MISOReports.add_to_datetime(
        report_name=target,
        ddatetime=ddatetime, 
        direction=direction,
    )

    assert new_datetime == expected, f"Expected {expected}, got {new_datetime}."
    

nsi_test_list = [
    "nsi1",
    "nsi5",
]


@pytest.mark.parametrize(
    "report_name", nsi_test_list
)
def test_get_df_nsi_with_changing_columns(report_name):
    """Edge case tests for nsi reports which have changing columns.
    The assumption is that aside from timestamp, the columns are all ints.
    """
    df = MISOReports.get_df(
        report_name=report_name,
    )

    int_columns = df.columns.difference(["timestamp"])

    assert pd.api.types.is_datetime64_ns_dtype(df["timestamp"])
    assert df[int_columns].dtypes.apply(lambda x: pd.api.types.is_integer_dtype(x)).all()


ftr_mpma_results_test_list = [
    "ftr_mpma_results",
]


@pytest.mark.parametrize(
    "report_name", ftr_mpma_results_test_list
)
def test_get_df_ftr_mpma_results_with_changing_columns(report_name, datetime_increment_limit, number_of_dfs_to_stop_at):
    """Edge case tests for ftr_mpma_results report which has changing columns.
    The assumption is that the report will always give 3 sections of files with
    the same amount of files for each section. Each file within their respective
    sections should have the same typing.
    """
    dfs = try_to_get_dfs(
        report_name=report_name,
        datetime_increment_limit=datetime_increment_limit,
        number_of_dfs_to_stop_at=number_of_dfs_to_stop_at,
    )

    for df in dfs:
        for i, name in enumerate(df[MULTI_DF_NAMES_COLUMN]):
            if name == "Metadata":
                n_files = len(df[MULTI_DF_DFS_COLUMN].iloc[i].columns)
                assert n_files % 3 == 0, f"Expected number of columns to be a multiple of 3, got {n_files}."
                break

        types_1 = {
            ("Limit", "Flow", "Violation", "MarginalCost",): pd.api.types.is_float_dtype,
            ("DeviceName", "DeviceType", "ControlArea", "Direction", "Description", "Contingency", "Class",): pd.api.types.is_string_dtype,
            ("Round",): pd.api.types.is_integer_dtype,
        }

        types_2 = {
            ("MW", "ClearingPrice",): pd.api.types.is_float_dtype,
            ("FTRID", "Category", "MarketParticipant", "Source", "Sink", "HedgeType", "Type", "Class",): pd.api.types.is_string_dtype,
            ("StartDate", "EndDate",): pd.api.types.is_datetime64_ns_dtype,
            ("Round",): pd.api.types.is_integer_dtype,
        }

        types_3 = {
            ("ShadowPrice",): pd.api.types.is_float_dtype,
            ("Round",): pd.api.types.is_integer_dtype,
            ("SourceSink", "Class",): pd.api.types.is_string_dtype,
        }

        types_dict = {
            0: types_1,
            1: types_2,
            2: types_3,   
        }
        
        files_per_section = n_files // 3
        for i, name in enumerate(df[MULTI_DF_NAMES_COLUMN]):
            if name != "Metadata":
                reg = re.search(r"File (\d+)", name)
                if reg is None:
                    raise ValueError(f"Expected name to match regex, got {name}.")
                
                file_number = int(reg.group(1))

                # Assuming file_number starts at 1.
                section = (file_number - 1) // files_per_section
                types = types_dict[section]

                for columns, dtype_checker in types.items():
                    assert uses_correct_dtypes(df[MULTI_DF_DFS_COLUMN].iloc[i], columns, dtype_checker), \
                        f"For multi-df report {report_name}, df {name}, columns {columns} do not pass {dtype_checker.__name__}."
                
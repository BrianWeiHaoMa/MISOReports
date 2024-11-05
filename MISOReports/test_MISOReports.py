import pytest
import datetime

import pandas as pd, pandas
import numpy as np, numpy

from MISOReports.MISOReports import (
    MISORTWDDataBrokerURLBuilder,
    MISORTWDBIReporterURLBuilder,
    MISOMarketReportsURLBuilder,
    MISOReports,
)


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


@pytest.mark.long
def test_MISORTWDData_get_df_completes_and_has_something_or_is_not_implemented():
    mappings = MISOReports.report_mappings

    expected_columns = frozenset({
            ('INTERVALEST', 'CATEGORY', 'ACT', 'TOTALMW'),
            ('instantEST', 'value'),
            ('CASEAPPROVALDATE', 'SOLUTIONTIME', 'PJMFORECASTEDLMP'),
            ('ForecastDateTimeEST', 'ForecastHourEndingEST', 'ForecastWindValue', 'ForecastSolarValue', 'ActualDateTimeEST', 'ActualHourEndingEST', 'ActualWindValue', 'ActualSolarValue'),
            ('DateTimeEST', 'HourEndingEST', 'Value'),
            ('ForecastDateTimeEST', 'ForecastHourEndingEST', 'ForecastValue', 'ActualDateTimeEST', 'ActualHourEndingEST', 'ActualValue'),
            ('Name', 'LMP', 'Loss', 'Congestion'),
            ('timestamp', 'AEC', 'AECI', 'CSWS', 'GLHB', 'LGEE', 'MHEB', 'MISO', 'OKGE', 'ONT', 'PJM', 'SOCO', 'SPA', 'SWPP', 'TVA', 'WAUE'),
            ('timestamp', 'NSI'),
            ('Time', 'Value'),
            ('Name', 'Price', 'Period', 'Description'),
            ('MKT_INT_END_EST', 'COMMIT_REASON', 'TOTAL_ECON_MAX', 'NUM_RESOURCES'),
            ('Name', 'Value'),
            ('INTERVALEST', 'NORTH_SOUTH_LIMIT', 'SOUTH_NORTH_LIMIT', 'RAW_MW', 'UDSFLOW_MW'),
            ('INTERVALEST', 'NORTH_SOUTH_LIMIT', 'SOUTH_NORTH_LIMIT', 'RAW_MW', ' UDSFLOW_MW'),
            ('OutageDate', 'OutageMonthDay', 'Unplanned', 'Planned', 'Forced', 'Derated'),
            ('Semantic',),
            ('Name', 'LMP', 'MLC', 'MCC', 'REGMCP', 'REGMILEAGEMCP', 'SPINMCP', 'SUPPMCP', 'STRMCP', 'RCUPMCP', 'RCDOWNMCP', 'LMP.1', 'MLC.1', 'MCC.1', 'LMP.2', 'MLC.2', 'MCC.2', 'LMP.3', 'MLC.3', 'MCC.3'),
            ('Name', 'Period', 'Price', 'OVERRIDE', 'CURVETYPE', 'BP1', 'PC1', 'BP2', 'PC2'),
            ('Name', 'Period', 'Price', 'OVERRIDE', 'REASON', 'CURVETYPE', 'BP1', 'PC1', 'BP2', 'PC2', 'BP3', 'PC3', 'BP4', 'PC4'),
    })
    
    for k, v in mappings.items():
        if type(v.url_builder) == MISORTWDDataBrokerURLBuilder:
            try: 
                df = MISOReports.get_df(k)

                assert isinstance(df, pd.DataFrame)
                assert not df.empty
                
                df_columns = tuple(df.columns)
                assert df_columns in expected_columns, \
                    f"Columns {df_columns} do not match any expected format."

            except NotImplementedError:
                pass
        

@pytest.mark.long
def test_get_df_every_report_example_url_returns_non_empty_df():
    mappings = MISOReports.report_mappings

    # These reports have no non-empty tables as of 2024-11-02.
    empty_reports = set(
        [
            "da_M2M_Settlement_srw",
        ],
    )

    for report_name, report in mappings.items():
        try:
            df = MISOReports.get_df(
                report_name=report_name,
                url=report.example_url,
            )

            assert not df.columns.empty
            if report_name not in empty_reports:
                assert not df.empty
        except NotImplementedError as e:
            pass


report_columns_type_mappings: dict[str, dict[tuple[str], type]] = {
    "rt_bc_HIST": {
        ("Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
        ("Override",): pandas.core.arrays.integer.Int64Dtype,
        ("Flowgate NERCID", "Constraint_ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type",): pandas.core.arrays.string_.StringDtype,
        ("Market Date", "Hour of Occurrence",): numpy.dtypes.DateTime64DType,
    },
    "RT_UDS_Approved_Case_Percentage": {
        ("Percentage",): numpy.dtypes.Float64DType,
        ("UDS Case ID",): pandas.core.arrays.string_.StringDtype,
        ("Dispatch Interval",): numpy.dtypes.DateTime64DType,
    },
    "Resource_Uplift_by_Commitment_Reason": {
        ("ECONOMIC MAX",): numpy.dtypes.Float64DType,
        ("LOCAL RESOURCE ZONE",): pandas.core.arrays.integer.Int64Dtype,
        ("REASON", "REASON ID",): pandas.core.arrays.string_.StringDtype,
        ("STARTTIME",): numpy.dtypes.DateTime64DType,
    },
    "rt_rpe": {
        ("Shadow Price",): numpy.dtypes.Float64DType,
        ("Constraint Name", "Constraint Description",): pandas.core.arrays.string_.StringDtype,
        ("Time of Occurence",): numpy.dtypes.DateTime64DType,
    },
    "Historical_RT_RSG_Commitment": {
        ("TOTAL_ECON_MAX",): numpy.dtypes.Float64DType,
        ("COMMIT_REASON", "NUM_RESOURCES",): pandas.core.arrays.string_.StringDtype,
        ("MKT_INT_END_EST",): numpy.dtypes.DateTime64DType,
    },
    "da_pbc": {
        ("PRELIMINARY_SHADOW_PRICE",): numpy.dtypes.Float64DType,
        ("BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE",): pandas.core.arrays.integer.Int64Dtype,
        ("CONSTRAINT_NAME", "CURVETYPE", "REASON",): pandas.core.arrays.string_.StringDtype,
        ("MARKET_HOUR_EST",): numpy.dtypes.DateTime64DType,
    },
    "da_bc": {
        ("Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
        ("Hour of Occurrence", "Override",): pandas.core.arrays.integer.Int64Dtype,
        ("Flowgate NERC ID", "Constraint_ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason",): pandas.core.arrays.string_.StringDtype,
    },
    "da_bcsf": {
        ("From KV", "To KV",): pandas.core.arrays.integer.Int64Dtype,
        ("Constraint ID", "Direction", "Constraint Name", "Contingency Name", "Constraint Type", "Flowgate Name", "Device Type", "Key1", "Key2", "Key3", "From Area", "To Area", "From Station", "To Station",): pandas.core.arrays.string_.StringDtype,
    },
    "MARKET_SETTLEMENT_DATA_SRW": {
        ("DATE",): numpy.dtypes.DateTime64DType,
        ("BILL_DET",): pandas.core.arrays.string_.StringDtype,
        ("HR01", "HR02", "HR03", "HR04", "HR05", "HR06", "HR07", "HR08", "HR09", "HR10", "HR11", "HR12", "HR13", "HR14", "HR15", "HR16", "HR17", "HR18", "HR19", "HR20", "HR21", "HR22", "HR23", "HR24",): numpy.dtypes.Float64DType,
    },
    "combinedwindsolar": {
        ("ForecastDateTimeEST", "ActualDateTimeEST",): numpy.dtypes.DateTime64DType,
        ("ForecastHourEndingEST", "ActualHourEndingEST",): pandas.core.arrays.integer.Int64Dtype,
        ("ForecastWindValue", "ForecastSolarValue", "ActualWindValue", "ActualSolarValue",): numpy.dtypes.Float64DType,
    },
    "ms_vlr_HIST_SRW": {
        ("OPERATING DATE",): numpy.dtypes.DateTime64DType,
        ("SETTLEMENT RUN", "DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total",): numpy.dtypes.Float64DType,
        ("REGION", "CONSTRAINT",): pandas.core.arrays.string_.StringDtype,
    },
    "SolarForecast": {
        ("DateTimeEST",): numpy.dtypes.DateTime64DType,
        ("HourEndingEST",): pandas.core.arrays.integer.Int64Dtype,
        ("Value",): numpy.dtypes.Float64DType,
    },
    "DA_LMPs": {
        ("MARKET_DAY",): numpy.dtypes.DateTime64DType,
        ("HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24",): numpy.dtypes.Float64DType,
        ("NODE", "TYPE", "VALUE",): pandas.core.arrays.string_.StringDtype,
    },
    "rt_irsf": {
        ("MKTHOUR_EST",): numpy.dtypes.DateTime64DType,
        ("INTRAREGIONAL_SCHEDULED_FLOW",): numpy.dtypes.Float64DType,
        ("CONSTRAINT_NAME",): pandas.core.arrays.string_.StringDtype,
    },
    "rt_mf": {
        ("Unit Count", "Hour Ending",): pandas.core.arrays.integer.Int64Dtype,
        ("Time Interval EST",): numpy.dtypes.DateTime64DType,
        ("Peak Flag", "Region Name", "Fuel Type",): pandas.core.arrays.string_.StringDtype,
    },
    "rt_ex": {
        ("Committed (GW at Economic Maximum) - Forward", "Committed (GW at Economic Maximum) - Real-Time", "Committed (GW at Economic Maximum) - Delta", "Load (GW) - Forward", "Load (GW) - Real-Time", "Load (GW) - Delta", "Net Scheduled Imports (GW) - Forward", "Net Scheduled Imports (GW) - Real-Time", "Net Scheduled Imports (GW) - Delta", "Outages (GW at Economic Maximum) - Forward", "Outages (GW at Economic Maximum) - Real-Time", "Outages (GW at Economic Maximum) - Delta", "Offer Changes (GW at Economic Maximum) - Forward", "Offer Changes (GW at Economic Maximum) - Real-Time", "Offer Changes (GW at Economic Maximum) - Delta",): numpy.dtypes.Float64DType,
        ("Hour", "Real-Time Binding Constraints - (#)",): pandas.core.arrays.integer.Int64Dtype,
    },
    "df_al": {
        ("LRZ1 MTLF (MWh)", "LRZ1 ActualLoad (MWh)", "LRZ2_7 MTLF (MWh)", "LRZ2_7 ActualLoad (MWh)", "LRZ3_5 MTLF (MWh)", "LRZ3_5 ActualLoad (MWh)", "LRZ4 MTLF (MWh)", "LRZ4 ActualLoad (MWh)", "LRZ6 MTLF (MWh)", "LRZ6 ActualLoad (MWh)", "LRZ8_9_10 MTLF (MWh)", "LRZ8_9_10 ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)",): numpy.dtypes.Float64DType,
        ("HourEnding",): pandas.core.arrays.integer.Int64Dtype,
        ("Market Day",): numpy.dtypes.DateTime64DType,
    },
    "rf_al": {
        ("North MTLF (MWh)", "North ActualLoad (MWh)", "Central MTLF (MWh)", "Central ActualLoad (MWh)", "South MTLF (MWh)", "South ActualLoad (MWh)", "MISO MTLF (MWh)", "MISO ActualLoad (MWh)",): numpy.dtypes.Float64DType,
        ("HourEnding",): pandas.core.arrays.integer.Int64Dtype,
        ("Market Day",): numpy.dtypes.DateTime64DType,
    },
    "da_rpe": {
        ("Shadow Price",): numpy.dtypes.Float64DType,
        ("Hour of Occurence",): pandas.core.arrays.integer.Int64Dtype,
        ("Constraint Name", "Constraint Description",): pandas.core.arrays.string_.StringDtype,
    },
    "da_ex": {
        ("Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total",): numpy.dtypes.Float64DType,
        ("Hour",): pandas.core.arrays.integer.Int64Dtype,
    },
    "da_ex_rg": {
        ("Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total",): numpy.dtypes.Float64DType,
        ("Hour Ending",): pandas.core.arrays.integer.Int64Dtype,
    },
    "da_bc_HIST": {
        ("Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
        ("Constraint_ID", "Hour of Occurrence", "Override",): pandas.core.arrays.integer.Int64Dtype,
        ("Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type",): pandas.core.arrays.string_.StringDtype,
        ("Market Date",): numpy.dtypes.DateTime64DType,
    },
    "cpnode_reszone": {
        ("Reserve Zone",): pandas.core.arrays.integer.Int64Dtype,
        ("CP Node Name",): pandas.core.arrays.string_.StringDtype,
    },
    "da_co": {
        ("Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "MW", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): numpy.dtypes.Float64DType,
        ("Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope",): pandas.core.arrays.integer.Int64Dtype,
        ("Region", "Unit Code",): pandas.core.arrays.string_.StringDtype,
        ("Date/Time Beginning (EST)", "Date/Time End (EST)",): numpy.dtypes.DateTime64DType,
    },
    "rt_co": {
        ("Cleared MW1", "Cleared MW2", "Cleared MW3", "Cleared MW4", "Cleared MW5", "Cleared MW6", "Cleared MW7", "Cleared MW8", "Cleared MW9", "Cleared MW10", "Cleared MW11", "Cleared MW12", "Economic Max", "Economic Min", "Emergency Max", "Emergency Min", "Self Scheduled MW", "Target MW Reduction", "Curtailment Offer Price", "Price1", "MW1", "Price2", "MW2", "Price3", "MW3", "Price4", "MW4", "Price5", "MW5", "Price6", "MW6", "Price7", "MW7", "Price8", "MW8", "Price9", "MW9", "Price10", "MW10", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): numpy.dtypes.Float64DType,
        ("Economic Flag", "Emergency Flag", "Must Run Flag", "Unit Available Flag", "Slope",): pandas.core.arrays.integer.Int64Dtype,
        ("Region", "Unit Code",): pandas.core.arrays.string_.StringDtype,
        ("Mkthour Begin (EST)",): numpy.dtypes.DateTime64DType,
    },
    "Dead_Node_Report": {
        ("PNODE Name",): pandas.core.arrays.string_.StringDtype,
        ("Mkt Hour",): numpy.dtypes.DateTime64DType,
    },
    "asm_rt_co": {
        ("RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP1", "RegMW1", "RegMCP2", "RegMW2", "RegMCP3", "RegMW3", "RegMCP4", "RegMW4", "RegMCP5", "RegMW5", "RegMCP6", "RegMW6", "RegMCP7", "RegMW7", "RegMCP8", "RegMW8", "RegMCP9", "RegMW9", "RegMCP10", "RegMW10", "RegMCP11", "RegMW11", "RegMCP12", "RegMW12", "SpinMCP1", "SpinMW1", "SpinMCP2", "SpinMW2", "SpinMCP3", "SpinMW3", "SpinMCP4", "SpinMW4", "SpinMCP5", "SpinMW5", "SpinMCP6", "SpinMW6", "SpinMCP7", "SpinMW7", "SpinMCP8", "SpinMW8", "SpinMCP9", "SpinMW9", "SpinMCP10", "SpinMW10", "SpinMCP11", "SpinMW11", "SpinMCP12", "SpinMW12", "SuppMCP1", "SuppMW1", "SuppMCP2", "SuppMW2", "SuppMCP3", "SuppMW3", "SuppMCP4", "SuppMW4", "SuppMCP5", "SuppMW5", "SuppMCP6", "SuppMW6", "SuppMCP7", "SuppMW7", "SuppMCP8", "SuppMW8", "SuppMCP9", "SuppMW9", "SuppMCP10", "SuppMW10", "SuppMCP11", "SuppMW11", "SuppMCP12", "SuppMW12", "StrOfflineOfferRate", "STRMCP1", "STRMW1", "STRMCP2", "STRMW2", "STRMCP3", "STRMW3", "STRMCP4", "STRMW4", "STRMCP5", "STRMW5", "STRMCP6", "STRMW6", "STRMCP7", "STRMW7", "STRMCP8", "STRMW8", "STRMCP9", "STRMW9", "STRMCP10", "STRMW10", "STRMCP11", "STRMW11", "STRMCP12", "STRMW12", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): numpy.dtypes.Float64DType,
        ("Region", "Unit Code",): pandas.core.arrays.string_.StringDtype,
        ("Mkthour Begin (EST)",): numpy.dtypes.DateTime64DType,
    },
    "asm_da_co": {
        ("RegulationMax", "RegulationMin", "RegulationOffer Price", "RegulationSelfScheduleMW", "SpinningOffer Price", "SpinSelfScheduleMW", "OnlineSupplementalOffer", "OnlineSupplementalSelfScheduleMW", "OfflineSupplementalOffer", "OfflineSupplementalSelfScheduleMW", "RegMCP", "RegMW", "SpinMCP", "SpinMW", "SuppMCP", "SuppMW", "OfflineSTR", "STRMCP", "STRMW", "MinEnergyStorageLevel", "MaxEnergyStorageLevel", "EmerMinEnergyStorageLevel", "EmerMaxEnergyStorageLevel",): numpy.dtypes.Float64DType,
        ("Region", "Unit Code",): pandas.core.arrays.string_.StringDtype,
        ("Date/Time Beginning (EST)", "Date/Time End (EST)",): numpy.dtypes.DateTime64DType,
    },
    "M2M_Settlement_srw": {
        ("MISO_SHADOW_PRICE", "MISO_MKT_FLOW", "MISO_FFE", "CP_SHADOW_PRICE", "CP_MKT_FLOW", "CP_FFE", "MISO_CREDIT", "CP_CREDIT",): numpy.dtypes.Float64DType,
        ("FLOWGATE_ID",): pandas.core.arrays.integer.Int64Dtype,
        ("MONITORING_RTO", "CP_RTO", "FLOWGATE_NAME",): pandas.core.arrays.string_.StringDtype,
        ("HOUR_ENDING",): numpy.dtypes.DateTime64DType,
    },
    "M2M_Flowgates_as_of": {
        ("Flowgate ID",): pandas.core.arrays.integer.Int64Dtype,
        ("Monitoring RTO", "Non Monitoring RTO", "Flowgate Description",): pandas.core.arrays.string_.StringDtype,
    },
    "M2M_FFE": {
        ("Non Monitoring RTO FFE", "Adjusted FFE",): numpy.dtypes.Float64DType,
        ("NERC Flowgate ID",): pandas.core.arrays.integer.Int64Dtype,
        ("Monitoring RTO", "Non Monitoring RTO", "Flowgate Description",): pandas.core.arrays.string_.StringDtype,
        ("Hour Ending",): numpy.dtypes.DateTime64DType,
    },
    "Allocation_on_MISO_Flowgates": {
        ("Allocation (MW)",): numpy.dtypes.Float64DType,
        ("NERC ID", "Allocation to Rating Percentage",): pandas.core.arrays.integer.Int64Dtype,
        ("Flowgate Owner", "Flowgate Description", "Entity", "Direction", "Reciprocal Status on Flowgate",): pandas.core.arrays.string_.StringDtype,
    },
    "rt_pbc": {
        ("PRELIMINARY_SHADOW_PRICE",): numpy.dtypes.Float64DType,
        ("BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4", "OVERRIDE",): pandas.core.arrays.integer.Int64Dtype,
        ("CONSTRAINT_NAME", "CURVETYPE", "REASON",): pandas.core.arrays.string_.StringDtype,
        ("MARKET_HOUR_EST",): numpy.dtypes.DateTime64DType,
    },
    "rt_bc": {
        ("Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
        ("Override",): pandas.core.arrays.integer.Int64Dtype,
        ("Flowgate NERC ID", "Constraint ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type",): pandas.core.arrays.string_.StringDtype,
        ("Hour of Occurrence",): numpy.dtypes.DateTime64DType,
    },
    "rt_or": {
        ("Preliminary Shadow Price", "BP1", "PC1", "BP2", "PC2",): numpy.dtypes.Float64DType,
        ("Override",): pandas.core.arrays.integer.Int64Dtype,
        ("Flowgate NERC ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason",): pandas.core.arrays.string_.StringDtype,
        ("Hour of Occurrence",): numpy.dtypes.DateTime64DType,
    },
    "rt_fuel_on_margin": {
        ("Hour Ending", "Unit Count",): pandas.core.arrays.integer.Int64Dtype,
        ("Peak Flag", "Region Name", "Fuel Type",): pandas.core.arrays.string_.StringDtype,
        ("Time Interval EST",): numpy.dtypes.DateTime64DType,
    },
}


def test_get_df_correct_column_types():
    def get_dtype_frozenset(
        df: pd.DataFrame,
        columns: list[str],
    ):
        dtypes = df[columns].dtypes
        res = []
        for k in dtypes.index:
            res.append(type(dtypes[k]))
        return frozenset(res)

    report_mappings = MISOReports.report_mappings

    for report_name, columns_mapping in report_columns_type_mappings.items():
        df = MISOReports.get_df(
            report_name=report_name,
            url=report_mappings[report_name].example_url,
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


@pytest.mark.completion
def test_get_df_has_correct_column_types_check_for_every_report():
    reports = frozenset(MISOReports.report_mappings.keys())
    correct_column_types_check_reports = frozenset(report_columns_type_mappings.keys())
    
    assert correct_column_types_check_reports == reports, \
        "Not all reports are checked for correct column types."
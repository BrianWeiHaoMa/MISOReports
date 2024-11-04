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
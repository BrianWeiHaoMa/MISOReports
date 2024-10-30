import pytest
import datetime
import pandas as pd

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
        
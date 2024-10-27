import pytest
import datetime

from MISOReports.MISOReports import (
    MISORTWDDataBrokerURLBuilder,
    MISORTWDBIReporterURLBuilder,
    MISOMarketReportsURLBuilder,
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
    "target, supported_extensions, url_generator, ddatetime, file_extension, expected", [
        ("DA_Load_EPNodes", ["zip"], "url_generator_YYYYmmdd_last", datetime.datetime(year=2024, month=10, day=21), "zip", "https://docs.misoenergy.org/marketreports/DA_Load_EPNodes_20241021.zip"),
        ("da_exante_lmp", ["csv"], "url_generator_YYYYmmdd_first", datetime.datetime(year=2024, month=10, day=26), "csv", "https://docs.misoenergy.org/marketreports/20241026_da_exante_lmp.csv"),
        ("da_expost_lmp", ["csv"], "url_generator_YYYYmmdd_first", datetime.datetime(year=2024, month=10, day=26), "csv", "https://docs.misoenergy.org/marketreports/20241026_da_expost_lmp.csv"),
        ("DA_LMPs", ["zip"], "url_generator_YYYY_current_month_name_to_two_months_later_name_first", datetime.datetime(year=2024, month=7, day=1), "zip", "https://docs.misoenergy.org/marketreports/2024-Jul-Sep_DA_LMPs.zip"),
        ("rt_expost_str_5min_mcp", ["xlsx"], "url_generator_YYYYmm_first", datetime.datetime(year=2024, month=10, day=1), "xlsx", "https://docs.misoenergy.org/marketreports/202410_rt_expost_str_5min_mcp.xlsx"),
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
        url_generator=lambda dt, tgt: getattr(url_builder, url_generator)(dt, tgt),
    )

    assert url_builder.build_url(ddatetime=ddatetime, file_extension=file_extension) == expected

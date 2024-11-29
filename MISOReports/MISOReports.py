import uuid
from abc import ABC, abstractmethod
from typing import Callable
import datetime

import requests
import pandas as pd
from dateutil.relativedelta import relativedelta

from MISOReports import parsers


class Data:
    """A class to hold relevant download data.
    """
    def __init__(
        self,
        df: pd.DataFrame,
        response: requests.Response,
    ):
        """Constructor for Data class.

        :param pd.DataFrame df: The tabular data from the report.
        :param requests.Response response: The response from the download.
        """
        self.df = df
        self.response = response


class URLBuilder(ABC):
    """A class to build URLs for MISO reports.
    """
    target_placeholder = str(uuid.uuid4())
    extension_placeholder = str(uuid.uuid4())
    
    def __init__(
        self,
        target: str,
        supported_extensions: list[str],
        default_extension: str | None = None,
    ):
        """Constructor for URLBuilder class.

        :param str target: A string to be used in the URL to identify the report.
        :param list[str] supported_extensions: The different file types available for download.
        :param str | None default_extension: The default file type to download, defaults to None
        """
        self.target = target
        self.supported_extensions = supported_extensions
        self.default_extension = default_extension

    @abstractmethod
    def build_url(
        self,
        file_extension: str | None,
        ddatetime: datetime.datetime | None,
    ) -> str:
        """Builds the URL to download from.

        :param str | None file_extension: The file type to download. If None, the default extension is used.
        :param datetime.datetime | None ddatetime: The datetime to download the report for.
        :return str: A URL to download the report from.
        """
        pass

    def _build_url_extension_check(
        self,
        file_extension: str | None,
    ) -> str:
        """Checks the file extension and returns it if it is supported.

        :param str | None file_extension: The file extension to check. If None, the default extension is used.
        :return str: The file extension if it is supported.
        """
        if file_extension is None:
            if self.default_extension is None:
                raise ValueError("No file extension provided and no default extension set.")

            file_extension = self.default_extension

        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file extension: {file_extension}")

        return file_extension
    
    def add_to_datetime(
        self,
        ddatetime: datetime.datetime | None,
        direction: int,
    ) -> datetime.datetime | None:
        """Changes the datetime by one unit in the direction specified according to URL generator if this
        URL builder uses it, otherwise leaves it unchanged.

        :param datetime.datetime | None ddatetime: The datetime to change.
        :param int direction: The multiple for the increment (negative for backwards increment).
        :return datetime.datetime: The new datetime.
        """
        return ddatetime
    
    
class MISORTWDDataBrokerURLBuilder(URLBuilder):
    def __init__(
        self,
        target: str,
        supported_extensions: list[str],
        default_extension: str | None = None,
    ):
        super().__init__(
            target=target, 
            supported_extensions=supported_extensions,
            default_extension=default_extension,
        )

        self._format_url = f"https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType={target}&returnType={URLBuilder.extension_placeholder}"

    def build_url(
        self,
        file_extension: str | None,
        ddatetime: datetime.datetime | None = None,
    ) -> str:
        file_extension = self._build_url_extension_check(file_extension)
        
        res = self._format_url.replace(URLBuilder.extension_placeholder, file_extension)
        return res


class MISORTWDBIReporterURLBuilder(URLBuilder):
    def __init__(
        self,
        target: str,
        supported_extensions: list[str],
        default_extension: str | None = None,
    ):
        super().__init__(
            target=target, 
            supported_extensions=supported_extensions,
            default_extension=default_extension,
        )

        self._format_url = f"https://api.misoenergy.org/MISORTWDBIReporter/Reporter.asmx?messageType={target}&returnType={URLBuilder.extension_placeholder}"

    def build_url(
        self,
        file_extension: str | None,
        ddatetime: datetime.datetime | None = None,
    ) -> str:
        file_extension = self._build_url_extension_check(file_extension)
        
        res = self._format_url.replace(URLBuilder.extension_placeholder, file_extension)
        return res
    

class MISOMarketReportsURLBuilder(URLBuilder):
    def __init__(
        self,
        target: str,
        supported_extensions: list[str],
        url_generator: Callable[[datetime.datetime | None, str], str],
        default_extension: str | None = None,
    ):
        """Constructor for MISOMarketReportsURLBuilder class.

        :param str target: The target of the URL.
        :param list[str] supported_extensions: The supported extensions for the URL.
        :param Callable[[datetime.datetime  |  None, str], str] url_generator: The function to generate the URL.
        :param str | None default_extension: The default file type to download, defaults to None
        """
        super().__init__(
            target=target, 
            supported_extensions=supported_extensions,
            default_extension=default_extension,
        )

        self.url_generator = url_generator
        self.increment_mappings: dict[Callable[[datetime.datetime | None, str], str], relativedelta] = {}

    def build_url(
        self,
        file_extension: str | None,
        ddatetime: datetime.datetime | None,
    ) -> str:
        file_extension = self._build_url_extension_check(file_extension)
        
        res = self.url_generator(ddatetime, self.target)
        res = res.replace(URLBuilder.extension_placeholder, file_extension)
        return res
    
    def add_to_datetime(
        self,
        ddatetime: datetime.datetime | None,
        direction: int,
    ) -> datetime.datetime | None:
        """Changes the datetime by one unit (according to the URL generator) 
        in the direction specified.

        :param datetime.datetime | None ddatetime: The datetime to change.
        :param int direction: The multiple for the increment (negative for backwards increment).
        :return datetime.datetime: The new datetime.
        """
        default_increment_mappings: dict[Callable[[datetime.datetime | None, str], str], relativedelta] = {
            MISOMarketReportsURLBuilder.url_generator_YYYY_current_month_name_to_two_months_later_name_first: relativedelta(months=3),
            MISOMarketReportsURLBuilder.url_generator_YYYY_underscore_current_month_name_to_two_months_later_name_first: relativedelta(months=3),
            MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first: relativedelta(days=1),
            MISOMarketReportsURLBuilder.url_generator_YYYYmm_first: relativedelta(months=1),
            MISOMarketReportsURLBuilder.url_generator_YYYY_first: relativedelta(years=1),
            MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last: relativedelta(days=1),
            MISOMarketReportsURLBuilder.url_generator_YYYY_mm_dd_last: relativedelta(days=1),
            MISOMarketReportsURLBuilder.url_generator_YYYY_last: relativedelta(years=1),
            MISOMarketReportsURLBuilder.url_generator_no_date: relativedelta(days=0),
            MISOMarketReportsURLBuilder.url_generator_mmddYYYY_last: relativedelta(days=1),
            MISOMarketReportsURLBuilder.url_generator_dddYYYY_last_but_as_nth_day_in_year_and_no_underscore: relativedelta(days=1),
        }

        self.increment_mappings.update(default_increment_mappings)

        if self.url_generator not in self.increment_mappings.keys():
            raise ValueError("This URL generator has no mapped increment.")    

        if ddatetime is None:
            return None
        else:
            return ddatetime + direction * self.increment_mappings[self.url_generator]

    @staticmethod    
    def _url_generator_datetime_first(
        ddatetime: datetime.datetime | None,
        target: str,
        datetime_format: str,
    ) -> str:
        if ddatetime is None:
            raise ValueError("ddatetime required for this URL builder.")

        format_string = f"https://docs.misoenergy.org/marketreports/{datetime_format}_{target}.{URLBuilder.extension_placeholder}"
        res = ddatetime.strftime(format_string)
        return res
    
    @staticmethod
    def url_generator_YYYYmmdd_first(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        return MISOMarketReportsURLBuilder._url_generator_datetime_first(ddatetime, target, "%Y%m%d")
    
    @staticmethod
    def url_generator_YYYYmm_first(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        return MISOMarketReportsURLBuilder._url_generator_datetime_first(ddatetime, target, "%Y%m")
    
    @staticmethod
    def url_generator_YYYY_first(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        return MISOMarketReportsURLBuilder._url_generator_datetime_first(ddatetime, target, "%Y")
    
    @staticmethod
    def url_generator_YYYY_current_month_name_to_two_months_later_name_first(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        if ddatetime is None:
            raise ValueError("ddatetime required for this URL builder.")

        new_month = ddatetime.month + 2 if ddatetime.month + 2 < 13 else ((ddatetime.month + 2) % 13) + 1
        two_months_later_datetime = ddatetime.replace(month=new_month)
        datetime_part = f"{ddatetime.strftime('%Y')}-{ddatetime.strftime('%b')}-{two_months_later_datetime.strftime('%b')}" 
        res = f"https://docs.misoenergy.org/marketreports/{datetime_part}_{target}.{URLBuilder.extension_placeholder}"
        return res

    @staticmethod
    def url_generator_YYYY_underscore_current_month_name_to_two_months_later_name_first(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        if ddatetime is None:
            raise ValueError("ddatetime required for this URL builder.")

        new_month = ddatetime.month + 2 if ddatetime.month + 2 < 13 else ((ddatetime.month + 2) % 13) + 1
        two_months_later_datetime = ddatetime.replace(month=new_month)
        datetime_part = f"{ddatetime.strftime('%Y')}_{ddatetime.strftime('%b')}-{two_months_later_datetime.strftime('%b')}" 
        res = f"https://docs.misoenergy.org/marketreports/{datetime_part}_{target}.{URLBuilder.extension_placeholder}"
        return res
    
    @staticmethod
    def url_generator_YYYYmmdd_last(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        if ddatetime is None:
            raise ValueError("ddatetime required for this URL builder.")

        res = f"https://docs.misoenergy.org/marketreports/{target}_{ddatetime.strftime('%Y%m%d')}.{URLBuilder.extension_placeholder}"
        return res
    
    @staticmethod
    def url_generator_YYYY_mm_dd_last(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        if ddatetime is None:
            raise ValueError("ddatetime required for this URL builder.")

        res = f"https://docs.misoenergy.org/marketreports/{target}_{ddatetime.strftime('%Y_%m_%d')}.{URLBuilder.extension_placeholder}"
        return res
    
    @staticmethod
    def url_generator_YYYY_last(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        if ddatetime is None:
            raise ValueError("ddatetime required for this URL builder.")

        res = f"https://docs.misoenergy.org/marketreports/{target}_{ddatetime.strftime('%Y')}.{URLBuilder.extension_placeholder}"
        return res
    
    @staticmethod
    def url_generator_no_date(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        res = f"https://docs.misoenergy.org/marketreports/{target}.{URLBuilder.extension_placeholder}"
        return res
    
    @staticmethod
    def url_generator_mmddYYYY_last(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        if ddatetime is None:
            raise ValueError("ddatetime required for this URL builder.")

        res = f"https://docs.misoenergy.org/marketreports/{target}_{ddatetime.strftime('%m%d%Y')}.{URLBuilder.extension_placeholder}"
        return res
    
    @staticmethod
    def url_generator_dddYYYY_last_but_as_nth_day_in_year_and_no_underscore(
        ddatetime: datetime.datetime | None,
        target: str,
    ) -> str:
        if ddatetime is None:
            raise ValueError("ddatetime required for this URL builder.")

        res = f"https://docs.misoenergy.org/marketreports/{target}{ddatetime.strftime('%j%Y')}.{URLBuilder.extension_placeholder}"
        return res


class Report:
    """A representation of a report for download.
    """
    def __init__(
        self,
        url_builder: URLBuilder,
        type_to_parse: str,
        parser: Callable[[requests.Response], pd.DataFrame],
        example_url: str,
        example_datetime: datetime.datetime | None = None,
    ):
        """Constructor for Report class.

        :param URLBuilder url_builder: The URL builder to be used for the report.
        :param str type_to_parse: The type of the file to pass as input into the parser.
        :param Callable[[requests.Response], pd.DataFrame] parser: The parser for the report.
        :param str example_url: An example URL for the report.
        :param datetime.datetime | None example_datetime: An example datetime for the report (this should match the example_url).
        """
        self.url_builder = url_builder
        self.type_to_parse = type_to_parse
        self.report_parser = parser
        self.example_url = example_url
        self.example_datetime = example_datetime


class MISOReports:
    """A class for downloading MISO reports.
    """
    @staticmethod
    def get_url(
        report_name: str,
        file_extension: str | None = None,
        ddatetime: datetime.datetime | None = None,
    ) -> str:
        """Get the URL for the report.

        :param str report_name: The name of the report.
        :param str file_extension: The type of file to download.
        :param datetime.datetime | None ddatetime: The date of the report, defaults to None
        :return str: The URL to download the report from.
        """
        if report_name not in MISOReports.report_mappings:
            raise ValueError(f"Unsupported report: {report_name}")
        
        report = MISOReports.report_mappings[report_name]
        
        res = report.url_builder.build_url(
            file_extension=file_extension, 
            ddatetime=ddatetime,
        )

        return res
    
    @staticmethod
    def get_response(
        report_name: str,
        file_extension: str | None = None, 
        ddatetime: datetime.datetime | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """Get the response for the report download.

        :param str report_name: The name of the report.
        :param str file_extension: The type of file to download.
        :param datetime.datetime | None ddatetime: The date of the report, defaults to None
        :param int | None timeout: The timeout for the request, defaults to None
        """
        url = MISOReports.get_url(
            report_name=report_name, 
            file_extension=file_extension, 
            ddatetime=ddatetime,
        )

        res = MISOReports._get_response_helper(
            url=url,
            timeout=timeout,
        )

        return res
    
    @staticmethod
    def _get_response_helper(
        url: str,
        timeout: int | None = None,
    ) -> requests.Response:
        """Helper function to get the response in the report download.

        :param str url: The URL to download the report from.
        :param int | None timeout: The timeout limit for the request, defaults to None
        :return requests.Response: The response object for the request.
        """
        res = requests.get(
            url=url,
            timeout=timeout,
        )

        res.raise_for_status()
        
        return res
    
    @staticmethod
    def get_df(
        report_name: str,
        url: str | None = None,
        ddatetime: datetime.datetime | None = None,
        timeout: int | None = None,
    ) -> pd.DataFrame:
        """Get a parsed DataFrame for the report.

        :param str report_name: The name of the report.
        :param str | None url: A url to download directly from, defaults to None
        :param datetime.datetime | None ddatetime: The date of the report, defaults to None
        :param int | None timeout: The timeout for the request, defaults to None
        :return pd.DataFrame: A DataFrame containing the data of the report.
        """
        data = MISOReports.get_data(
            report_name=report_name,
            url=url,
            ddatetime=ddatetime,
            timeout=timeout,
        )
        
        return data.df

    @staticmethod
    def get_data(
        report_name: str,
        url: str | None = None,
        ddatetime: datetime.datetime | None = None,
        timeout: int | None = None,
    ) -> Data:
        """Gets the relevant data for the report.

        :param str report_name: The name of the report.
        :param str | None url: The url to download from, defaults to None
        :param datetime.datetime | None ddatetime: The target datetime to download the report for, defaults to None
        :param int | None timeout: The timeout for the request, defaults to None
        :return Data: An object containing the DataFrame and the response.
        """
        report = MISOReports.report_mappings[report_name]

        if url is not None:
            response = MISOReports._get_response_helper(
                url=url, 
                timeout=timeout,
            )
        else:
            response = MISOReports.get_response(
                report_name=report_name, 
                file_extension=report.type_to_parse, 
                ddatetime=ddatetime,
                timeout=timeout,
            )

        df = report.report_parser(response)

        res = Data(
            df=df,
            response=response,
        )

        return res
    

    report_mappings: dict[str, Report] = {
        "rt_bc_HIST": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_bc_HIST",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_rt_bc_HIST,
            example_url="https://docs.misoenergy.org/marketreports/2024_rt_bc_HIST.csv",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "RT_UDS_Approved_Case_Percentage": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="RT_UDS_Approved_Case_Percentage",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_RT_UDS_Approved_Case_Percentage,
            example_url="https://docs.misoenergy.org/marketreports/20241023_RT_UDS_Approved_Case_Percentage.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=23),
        ),

        "Resource_Uplift_by_Commitment_Reason": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="Resource_Uplift_by_Commitment_Reason",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_Resource_Uplift_by_Commitment_Reason,
            example_url="https://docs.misoenergy.org/marketreports/20241009_Resource_Uplift_by_Commitment_Reason.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=9),
        ),

        "rt_rpe": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_rpe",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_rt_rpe,
            example_url="https://docs.misoenergy.org/marketreports/20241101_rt_rpe.xls",
            example_datetime=datetime.datetime(year=2024, month=11, day=1),
        ),

        "Historical_RT_RSG_Commitment": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="Historical_RT_RSG_Commitment",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_Historical_RT_RSG_Commitment,
            example_url="https://docs.misoenergy.org/marketreports/2024_Historical_RT_RSG_Commitment.csv",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "da_pr": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="da_pr",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_da_pr,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_pr.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "da_pbc": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="da_pbc",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_da_pbc,
            example_url="https://docs.misoenergy.org/marketreports/20220107_da_pbc.csv",
            example_datetime=datetime.datetime(year=2022, month=1, day=7),
        ),

        "da_bc": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="da_bc",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_da_bc,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_bc.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "da_bcsf": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="da_bcsf",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_da_bcsf,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_bcsf.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "rt_pr": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_pr",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_rt_pr,
            example_url="https://docs.misoenergy.org/marketreports/20241026_rt_pr.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=26),
        ),

        "rt_irsf": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_irsf",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_rt_irsf,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_irsf.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_mf": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_mf",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_rt_mf,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_mf.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_ex": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_ex",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_rt_ex,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_ex.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_pbc": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_pbc",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_rt_pbc,
            example_url="https://docs.misoenergy.org/marketreports/20241001_rt_pbc.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=1),
        ),

        "rt_bc": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_bc",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_rt_bc,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_bc.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_or": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_or",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_rt_or,
            example_url="https://docs.misoenergy.org/marketreports/20240910_rt_or.xls",
            example_datetime=datetime.datetime(year=2024, month=9, day=10),
        ),

        "rt_fuel_on_margin": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_fuel_on_margin",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_rt_fuel_on_margin,
            example_url="https://docs.misoenergy.org/marketreports/2023_rt_fuel_on_margin.zip",
            example_datetime=datetime.datetime(year=2023, month=1, day=1),
        ),

        "Total_Uplift_by_Resource": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="Total_Uplift_by_Resource",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_Total_Uplift_by_Resource,
            example_url="https://docs.misoenergy.org/marketreports/20241001_Total_Uplift_by_Resource.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=1),
        ),

        "ms_vlr_srw": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_vlr_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_ms_vlr_srw,
            example_url="https://docs.misoenergy.org/marketreports/20240901_ms_vlr_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=9, day=1),
        ),

        "ms_rsg_srw": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_rsg_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_ms_rsg_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241126_ms_rsg_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=11, day=26),
        ),

        "ms_rnu_srw": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_rnu_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_ms_rnu_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241029_ms_rnu_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "ms_ri_srw": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_ri_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_ms_ri_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241029_ms_ri_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "MARKET_SETTLEMENT_DATA_SRW": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="MARKET_SETTLEMENT_DATA_SRW",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_no_date,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_MARKET_SETTLEMENT_DATA_SRW,
            example_url="https://docs.misoenergy.org/marketreports/MARKET_SETTLEMENT_DATA_SRW.zip",
        ),

        "ms_vlr_HIST_SRW": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_vlr_HIST_SRW",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_ms_vlr_HIST_SRW,
            example_url="https://docs.misoenergy.org/marketreports/2024_ms_vlr_HIST_SRW.xlsx",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "ms_ecf_srw": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_ecf_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_ms_ecf_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241126_ms_ecf_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=11, day=26),
        ),

        "ccf_co": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="ccf_co",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_ccf_co,
            example_url="https://docs.misoenergy.org/marketreports/20241020_ccf_co.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=20),
        ),

        "ms_vlr_HIST": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_vlr_HIST",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_ms_vlr_HIST,
            example_url="https://docs.misoenergy.org/marketreports/2022_ms_vlr_HIST.csv",
            example_datetime=datetime.datetime(year=2022, month=1, day=1),
        ),

        "Daily_Uplift_by_Local_Resource_Zone": Report( # Checked 2024-11-24.
            url_builder=MISOMarketReportsURLBuilder(
                target="Daily_Uplift_by_Local_Resource_Zone",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_Daily_Uplift_by_Local_Resource_Zone,
            example_url="https://docs.misoenergy.org/marketreports/20240320_Daily_Uplift_by_Local_Resource_Zone.xlsx",
            example_datetime=datetime.datetime(year=2024, month=3, day=20),
        ),

        "fuelmix": Report( # Checked 2024-11-24.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getfuelmix",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_fuelmix,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getfuelmix&returnType=csv",
        ),

        "ace": Report( # Checked 2024-11-24.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getace",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_ace,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getace&returnType=csv",
        ),

        "AncillaryServicesMCP": Report( # Checked 2024-11-24.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getAncillaryServicesMCP",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_AncillaryServicesMCP,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getAncillaryServicesMCP&returnType=csv",
        ),

        "cts": Report( # Checked 2024-11-24.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getcts",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_cts,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcts&returnType=csv",
        ),

        "combinedwindsolar": Report( # Checked 2024-11-24.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getcombinedwindsolar",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_combinedwindsolar,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcombinedwindsolar&returnType=csv",
        ),

        "WindForecast": Report( # Checked 2024-11-24.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWindForecast",
                supported_extensions=["xml", "json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=parsers.parse_WindForecast,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindForecast&returnType=json",
        ),

        "Wind": Report( # Checked 2024-11-24.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWind",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_Wind,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWind&returnType=csv",
        ),

        "SolarForecast": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolarForecast",
                supported_extensions=["xml", "json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=parsers.parse_SolarForecast,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarForecast&returnType=json",
        ),

        "Solar": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolar",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_Solar,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolar&returnType=csv",
        ),

        "exantelmp": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getexantelmp",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_exantelmp,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getexantelmp&returnType=csv",
        ),

        "da_exante_lmp": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="da_exante_lmp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_da_exante_lmp,
            example_url="https://docs.misoenergy.org/marketreports/20241026_da_exante_lmp.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=26),
        ),

        "da_expost_lmp": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="da_expost_lmp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_da_expost_lmp,
            example_url="https://docs.misoenergy.org/marketreports/20241026_da_expost_lmp.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=26),
        ),

        "rt_lmp_final": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_lmp_final",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_rt_lmp_final,
            example_url="https://docs.misoenergy.org/marketreports/20241021_rt_lmp_final.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=21),
        ),

        "rt_lmp_prelim": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_lmp_prelim",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_rt_lmp_prelim,
            example_url="https://docs.misoenergy.org/marketreports/20241125_rt_lmp_prelim.csv",
            example_datetime=datetime.datetime(year=2024, month=11, day=25),
        ),

        "DA_Load_EPNodes": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="DA_Load_EPNodes",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_DA_Load_EPNodes,
            example_url="https://docs.misoenergy.org/marketreports/DA_Load_EPNodes_20241021.zip",
            example_datetime=datetime.datetime(year=2024, month=10, day=21),
        ),

        "DA_LMPs": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="DA_LMPs",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_current_month_name_to_two_months_later_name_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_DA_LMPs,
            example_url="https://docs.misoenergy.org/marketreports/2024-Jul-Sep_DA_LMPs.zip",
            example_datetime=datetime.datetime(year=2024, month=7, day=1),
        ),

        "5min_exante_lmp": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="5min_exante_lmp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_5min_exante_lmp,
            example_url="https://docs.misoenergy.org/marketreports/20241025_5min_exante_lmp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=25),
        ),

        "nsi1": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi1",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_nsi1,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1&returnType=csv",
        ),

        "nsi5": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi5",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_nsi5,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5&returnType=csv",
        ),

        "nsi1miso": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi1miso",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_nsi1miso,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1miso&returnType=csv",
        ),

        "nsi5miso": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi5miso",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_nsi5miso,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5miso&returnType=csv",
        ),

        "importtotal5": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getimporttotal5",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="json",
            parser=parsers.parse_importtotal5,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getimporttotal5&returnType=json",
        ),

        "reservebindingconstraints": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getreservebindingconstraints",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_reservebindingconstraints,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getreservebindingconstraints&returnType=csv",
        ),

        "RSG": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getRSG",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_RSG,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getRSG&returnType=csv",
        ),

        "totalload": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="gettotalload",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_totalload,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=gettotalload&returnType=csv",
        ),

        "WindActual": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWindActual",
                supported_extensions=["xml", "json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=parsers.parse_WindActual,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindActual&returnType=json",
        ),

        "SolarActual": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolarActual",
                supported_extensions=["xml", "json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=parsers.parse_SolarActual,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarActual&returnType=json",
        ),

        "NAI": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getNAI",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_NAI,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getNAI&returnType=csv",
        ),

        "regionaldirectionaltransfer": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getregionaldirectionaltransfer",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_regionaldirectionaltransfer,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getregionaldirectionaltransfer&returnType=csv",
        ),

        "generationoutagesplusminusfivedays": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getgenerationoutagesplusminusfivedays",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_generationoutagesplusminusfivedays,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getgenerationoutagesplusminusfivedays&returnType=csv",
        ),

        "apiversion": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getapiversion",
                supported_extensions=["json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=parsers.parse_apiversion,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getapiversion&returnType=json",
        ),

        "lmpconsolidatedtable": Report( # TODO re-evaluate column parsing. Potential of abnormal sideways formatting.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getlmpconsolidatedtable",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_lmpconsolidatedtable,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getlmpconsolidatedtable&returnType=csv",
        ),

        "realtimebindingconstraints": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getrealtimebindingconstraints",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_realtimebindingconstraints,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getrealtimebindingconstraints&returnType=csv",
        ),

        "realtimebindingsrpbconstraints": Report( # Checked 2024-11-26.
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getrealtimebindingsrpbconstraints",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_realtimebindingsrpbconstraints,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getrealtimebindingsrpbconstraints&returnType=csv",
        ),

        "RT_Load_EPNodes": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="RT_Load_EPNodes",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_RT_Load_EPNodes,
            example_url="https://docs.misoenergy.org/marketreports/RT_Load_EPNodes_20241018.zip",
            example_datetime=datetime.datetime(year=2024, month=10, day=18),
        ),

        "5MIN_LMP": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="5MIN_LMP",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_5MIN_LMP,
            example_url="https://docs.misoenergy.org/marketreports/20241021_5MIN_LMP.zip",
            example_datetime=datetime.datetime(year=2024, month=10, day=21),
        ),

        "bids_cb": Report( # Checked 2024-11-26.
            url_builder=MISOMarketReportsURLBuilder(
                target="bids_cb",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_bids_cb,
            example_url="https://docs.misoenergy.org/marketreports/20240801_bids_cb.zip",
            example_datetime=datetime.datetime(year=2024, month=8, day=1),
        ),

        "asm_exante_damcp": Report( # Checked 2024-11-27.
                url_builder=MISOMarketReportsURLBuilder(
                target="asm_exante_damcp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_asm_exante_damcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_asm_exante_damcp.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "ftr_allocation_restoration": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_restoration",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_allocation_restoration,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_restoration.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_allocation_stage_1A": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_stage_1A",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_allocation_stage_1A,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1A.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_allocation_stage_1B": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_stage_1B",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_allocation_stage_1B,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1B.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_allocation_summary": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_summary",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_allocation_summary,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_summary.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_annual_results_round_1": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_results_round_1",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_annual_results_round_1,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_annual_results_round_1.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_annual_results_round_2": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_results_round_2",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_annual_results_round_2,
            example_url="https://docs.misoenergy.org/marketreports/20240501_ftr_annual_results_round_2.zip",
            example_datetime=datetime.datetime(year=2024, month=5, day=1),
        ),

        "ftr_annual_results_round_3": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_results_round_3",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_annual_results_round_3,
            example_url="https://docs.misoenergy.org/marketreports/20240101_ftr_annual_results_round_3.zip",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "ftr_annual_bids_offers": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_bids_offers",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_annual_bids_offers,
            example_url="https://docs.misoenergy.org/marketreports/2023_ftr_annual_bids_offers.zip",
            example_datetime=datetime.datetime(year=2023, month=1, day=1),
        ),

        "ftr_mpma_results": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_mpma_results",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_mpma_results,
            example_url="https://docs.misoenergy.org/marketreports/20241101_ftr_mpma_results.zip",
            example_datetime=datetime.datetime(year=2024, month=11, day=1),
        ),

        "ftr_mpma_bids_offers": Report( # Checked 2024-11-27.
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_mpma_bids_offers",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_ftr_mpma_bids_offers,
            example_url="https://docs.misoenergy.org/marketreports/20240801_ftr_mpma_bids_offers.zip",
            example_datetime=datetime.datetime(year=2024, month=8, day=1),
        ),

        "asm_expost_damcp": Report( # Checked 2024-11-27.
                url_builder=MISOMarketReportsURLBuilder(
                target="asm_expost_damcp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_asm_expost_damcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_asm_expost_damcp.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "asm_rtmcp_final": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="asm_rtmcp_final",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_asm_rtmcp_final,
            example_url="https://docs.misoenergy.org/marketreports/20241026_asm_rtmcp_final.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=26),
        ),

        "asm_rtmcp_prelim": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="asm_rtmcp_prelim",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_asm_rtmcp_prelim,
            example_url="https://docs.misoenergy.org/marketreports/20241110_asm_rtmcp_prelim.csv",
            example_datetime=datetime.datetime(year=2024, month=11, day=5),
        ),

        "5min_exante_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="5min_exante_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_5min_exante_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_5min_exante_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "5min_expost_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="5min_expost_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_5min_expost_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241028_5min_expost_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=28),
        ),

        "da_exante_ramp_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_exante_ramp_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_da_exante_ramp_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_exante_ramp_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "da_exante_str_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_exante_str_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_da_exante_str_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_exante_str_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "da_expost_ramp_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_expost_ramp_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_da_expost_ramp_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_expost_ramp_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "da_expost_str_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_expost_str_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_da_expost_str_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_expost_str_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_expost_ramp_5min_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_expost_ramp_5min_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmm_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_rt_expost_ramp_5min_mcp,
            example_url="https://docs.misoenergy.org/marketreports/202410_rt_expost_ramp_5min_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=1),
        ),

        "rt_expost_ramp_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_expost_ramp_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmm_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_rt_expost_ramp_mcp,
            example_url="https://docs.misoenergy.org/marketreports/202410_rt_expost_ramp_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=1),
        ),

        "rt_expost_str_5min_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_expost_str_5min_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmm_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_rt_expost_str_5min_mcp,
            example_url="https://docs.misoenergy.org/marketreports/202409_rt_expost_str_5min_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=9, day=1),
        ),

        "rt_expost_str_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_expost_str_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmm_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_rt_expost_str_mcp,
            example_url="https://docs.misoenergy.org/marketreports/202410_rt_expost_str_mcp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=1),
        ),

        "Allocation_on_MISO_Flowgates": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="Allocation_on_MISO_Flowgates",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_mm_dd_last,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_Allocation_on_MISO_Flowgates,
            example_url="https://docs.misoenergy.org/marketreports/Allocation_on_MISO_Flowgates_2024_10_29.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "M2M_FFE": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="M2M_FFE",
                supported_extensions=["CSV"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_mm_dd_last,
                default_extension="CSV",
            ),
            type_to_parse="CSV",
            parser=parsers.parse_M2M_FFE,
            example_url="https://docs.misoenergy.org/marketreports/M2M_FFE_2024_10_29.CSV",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "M2M_Flowgates_as_of": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="M2M_Flowgates_as_of",
                supported_extensions=["CSV"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
                default_extension="CSV",
            ),
            type_to_parse="CSV",
            parser=parsers.parse_M2M_Flowgates_as_of,
            example_url="https://docs.misoenergy.org/marketreports/M2M_Flowgates_as_of_20241030.CSV",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        # Every download URL as of 2024-11-02 offered for this report was empty.
        "da_M2M_Settlement_srw": Report( 
                url_builder=MISOMarketReportsURLBuilder(
                target="da_M2M_Settlement_srw",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_last,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_da_M2M_Settlement_srw,
            example_url="https://docs.misoenergy.org/marketreports/da_M2M_Settlement_srw_2024.csv",
            example_datetime=datetime.datetime(year=2024, month=11, day=2),
        ),

        "M2M_Settlement_srw": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="M2M_Settlement_srw",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_last,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_M2M_Settlement_srw,
            example_url="https://docs.misoenergy.org/marketreports/M2M_Settlement_srw_2024.csv",
            example_datetime=datetime.datetime(year=2024, month=11, day=2),
        ),

        "MM_Annual_Report": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="MM_Annual_Report",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_MM_Annual_Report,
            example_url="https://docs.misoenergy.org/marketreports/20241030_MM_Annual_Report.zip",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "asm_da_co": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="asm_da_co",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_asm_da_co,
            example_url="https://docs.misoenergy.org/marketreports/20240801_asm_da_co.zip",
            example_datetime=datetime.datetime(year=2024, month=8, day=1),
        ),

        "asm_rt_co": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="asm_rt_co",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_asm_rt_co,
            example_url="https://docs.misoenergy.org/marketreports/20240801_asm_rt_co.zip",
            example_datetime=datetime.datetime(year=2024, month=8, day=1),
        ),

        "Dead_Node_Report": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="Dead_Node_Report",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_Dead_Node_Report,
            example_url="https://docs.misoenergy.org/marketreports/Dead_Node_Report_20241030.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_co": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="rt_co",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_rt_co,
            example_url="https://docs.misoenergy.org/marketreports/20240801_rt_co.zip",
            example_datetime=datetime.datetime(year=2024, month=8, day=1),
        ),

        "da_co": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="da_co",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_da_co,
            example_url="https://docs.misoenergy.org/marketreports/20240801_da_co.zip",
            example_datetime=datetime.datetime(year=2024, month=8, day=1),
        ),

        "cpnode_reszone": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="cpnode_reszone",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_cpnode_reszone,
            example_url="https://docs.misoenergy.org/marketreports/20241002_cpnode_reszone.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=2),
        ),

        
        "sr_ctsl": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="sr_ctsl",
                supported_extensions=["pdf"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="pdf",
            ),
            type_to_parse="pdf",
            parser=parsers.parse_sr_ctsl,
            example_url="https://docs.misoenergy.org/marketreports/20241020_sr_ctsl.pdf",
            example_datetime=datetime.datetime(year=2024, month=10, day=20),
        ),

        "df_al": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="df_al",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_df_al,
            example_url="https://docs.misoenergy.org/marketreports/20241030_df_al.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rf_al": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="rf_al",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_rf_al,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rf_al.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "da_bc_HIST": Report(
                url_builder=MISOMarketReportsURLBuilder(
                target="da_bc_HIST",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_da_bc_HIST,
            example_url="https://docs.misoenergy.org/marketreports/2024_da_bc_HIST.csv",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "da_ex_rg": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_ex_rg",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_da_ex_rg,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_ex_rg.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "da_ex": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_ex",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_da_ex,
            example_url="https://docs.misoenergy.org/marketreports/20220321_da_ex.xls",
            example_datetime=datetime.datetime(year=2022, month=3, day=21),
        ),

        "da_rpe": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_rpe",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_da_rpe,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_rpe.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "RT_LMPs": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="RT_LMPs",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_underscore_current_month_name_to_two_months_later_name_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=parsers.parse_RT_LMPs,
            example_url="https://docs.misoenergy.org/marketreports/2024_Jul-Sep_RT_LMPs.zip",
            example_datetime=datetime.datetime(year=2024, month=7, day=1),
        ),

        "sr_gfm": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="sr_gfm",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_sr_gfm,
            example_url="https://docs.misoenergy.org/marketreports/20241030_sr_gfm.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "dfal_HIST": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="dfal_HIST",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_dfal_HIST,
            example_url="https://docs.misoenergy.org/marketreports/20241111_dfal_HIST.xls",
            example_datetime=datetime.datetime(year=2024, month=11, day=11),
        ),

        "historical_gen_fuel_mix": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="historical_gen_fuel_mix",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_last,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_historical_gen_fuel_mix,
            example_url="https://docs.misoenergy.org/marketreports/historical_gen_fuel_mix_2023.xlsx",
            example_datetime=datetime.datetime(year=2023, month=1, day=1),
        ),

        "hwd_HIST": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="hwd_HIST",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_hwd_HIST,
            example_url="https://docs.misoenergy.org/marketreports/20241111_hwd_HIST.csv",
            example_datetime=datetime.datetime(year=2024, month=11, day=11),
        ),

        "sr_hist_is": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="sr_hist_is",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_sr_hist_is,
            example_url="https://docs.misoenergy.org/marketreports/2024_sr_hist_is.csv",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "rfal_HIST": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rfal_HIST",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_rfal_HIST,
            example_url="https://docs.misoenergy.org/marketreports/20241111_rfal_HIST.xls",
            example_datetime=datetime.datetime(year=2024, month=11, day=11),
        ),

        "sr_lt": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="sr_lt",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_sr_lt,
            example_url="https://docs.misoenergy.org/marketreports/20241028_sr_lt.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=28),
        ),

        "sr_la_rg": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="sr_la_rg",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_sr_la_rg,
            example_url="https://docs.misoenergy.org/marketreports/20241024_sr_la_rg.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=24),
        ),

        "mom": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="mom",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=parsers.parse_mom,
            example_url="https://docs.misoenergy.org/marketreports/20241020_mom.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=20),
        ),

        "sr_nd_is": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="sr_nd_is",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=parsers.parse_sr_nd_is,
            example_url="https://docs.misoenergy.org/marketreports/20241020_sr_nd_is.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=20),
        ),

        "PeakHourOverview": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="PeakHourOverview",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_mmddYYYY_last,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_PeakHourOverview,
            example_url="https://docs.misoenergy.org/marketreports/PeakHourOverview_03052022.csv",
            example_datetime=datetime.datetime(year=2022, month=3, day=5),
        ),

        "sr_tcdc_group2": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="sr_tcdc_group2",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_sr_tcdc_group2,
            example_url="https://docs.misoenergy.org/marketreports/2024_sr_tcdc_group2.csv",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "MISOdaily": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="MISOdaily",
                supported_extensions=["xml"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_dddYYYY_last_but_as_nth_day_in_year_and_no_underscore,
                default_extension="xml",
            ),
            type_to_parse="xml",
            parser=parsers.parse_MISOdaily,
            example_url="https://docs.misoenergy.org/marketreports/MISOdaily3042024.xml",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        
        "MISOsamedaydemand": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="MISOsamedaydemand",
                supported_extensions=["xml"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_no_date,
                default_extension="xml",
            ),
            type_to_parse="xml",
            parser=parsers.parse_MISOsamedaydemand,
            example_url="https://docs.misoenergy.org/marketreports/MISOsamedaydemand.xml",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "currentinterval": Report(
            url_builder=MISORTWDBIReporterURLBuilder(
                target="currentinterval",
                supported_extensions=["csv"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=parsers.parse_currentinterval,
            example_url="https://api.misoenergy.org/MISORTWDBIReporter/Reporter.asmx?messageType=currentinterval&returnType=csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

    }

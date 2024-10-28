import uuid
from abc import ABC, abstractmethod
from typing import Callable
import datetime
import json

import requests
import pandas as pd
from io import StringIO


class URLBuilder(ABC):
    target_placeholder = str(uuid.uuid4())
    extension_placeholder = str(uuid.uuid4())
    
    def __init__(
        self,
        target: str,
        supported_extensions: list[str],
    ):
        self.target = target
        self.supported_extensions = supported_extensions

    @abstractmethod
    def build_url(
        self,
        file_extension: str,
        ddatetime: datetime.datetime | None,
    ) -> str:
        pass
    
    
class MISORTWDDataBrokerURLBuilder(URLBuilder):
    def __init__(
        self,
        target: str,
        supported_extensions: list[str],
    ):
        super().__init__(
            target=target, 
            supported_extensions=supported_extensions
        )

        self._format_url = f"https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType={target}&returnType={URLBuilder.extension_placeholder}"

    def build_url(
        self,
        file_extension: str,
        ddatetime: datetime.datetime | None = None,
    ) -> str:
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file extension: {file_extension}")
        
        res = self._format_url.replace(URLBuilder.extension_placeholder, file_extension)
        return res


class MISORTWDBIReporterURLBuilder(URLBuilder):
    def __init__(
        self,
        target: str,
        supported_extensions: list[str],
    ):
        super().__init__(
            target=target, 
            supported_extensions=supported_extensions
        )

        self._format_url = f"https://api.misoenergy.org/MISORTWDBIReporter/Reporter.asmx?messageType={target}&returnType={URLBuilder.extension_placeholder}"

    def build_url(
        self,
        file_extension: str,
        ddatetime: datetime.datetime | None = None,
    ) -> str:
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file extension: {file_extension}")
        
        res = self._format_url.replace(URLBuilder.extension_placeholder, file_extension)
        return res
    

class MISOMarketReportsURLBuilder(URLBuilder):
    def __init__(
        self,
        target: str,
        supported_extensions: list[str],
        url_generator: Callable[[datetime.datetime, str], str],
    ):
        super().__init__(
            target=target, 
            supported_extensions=supported_extensions
        )

        self.url_generator = url_generator

    def build_url(
        self,
        file_extension: str,
        ddatetime: datetime.datetime | None,
    ) -> str:
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file extension: {file_extension}")
        
        if ddatetime is None:
            raise ValueError(f"ddatetime is required")
        
        res = self.url_generator(ddatetime, self.target)
        res = res.replace(URLBuilder.extension_placeholder, file_extension)
        return res

    @staticmethod    
    def _url_generator_datetime_first(
        ddatetime: datetime.datetime,
        target: str,
        datetime_format: str,
    ) -> str:
        format_string = f"https://docs.misoenergy.org/marketreports/{datetime_format}_{target}.{URLBuilder.extension_placeholder}"
        res = ddatetime.strftime(format_string)
        return res
    
    @staticmethod
    def url_generator_YYYYmmdd_first(
        ddatetime: datetime.datetime,
        target: str,
    ) -> str:
        return MISOMarketReportsURLBuilder._url_generator_datetime_first(ddatetime, target, "%Y%m%d")
    
    @staticmethod
    def url_generator_YYYYmm_first(
        ddatetime: datetime.datetime,
        target: str,
    ) -> str:
        return MISOMarketReportsURLBuilder._url_generator_datetime_first(ddatetime, target, "%Y%m")
    
    @staticmethod
    def url_generator_YYYY_current_month_name_to_two_months_later_name_first(
        ddatetime: datetime.datetime,
        target: str,
    ) -> str:
        new_month = ddatetime.month + 2 if ddatetime.month + 2 < 13 else ((ddatetime.month + 2) % 13) + 1
        two_months_later_datetime = ddatetime.replace(month=new_month)
        datetime_part = f"{ddatetime.strftime('%Y')}-{ddatetime.strftime('%b')}-{two_months_later_datetime.strftime('%b')}" 
        res = f"https://docs.misoenergy.org/marketreports/{datetime_part}_{target}.{URLBuilder.extension_placeholder}"
        return res
    
    @staticmethod
    def url_generator_YYYYmmdd_last(
        ddatetime: datetime.datetime,
        target: str,
    ) -> str:
        res = f"https://docs.misoenergy.org/marketreports/{target}_{ddatetime.strftime('%Y%m%d')}.{URLBuilder.extension_placeholder}"
        return res


class MISOReports:
    class Report:
        def __init__(
            self,
            url_builder: URLBuilder,
            type_to_parse: str,
            parser: Callable[[requests.Response], pd.DataFrame] | None,
        ):
            self.url_builder = url_builder
            self.type_to_parse = type_to_parse
            self.report_parser = parser

    
    class ReportParsers:
        @staticmethod
        def parse_fuelmix(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=StringIO(csv_data),
                parse_dates=[
                    "INTERVALEST",
                ],
                date_format={
                    "INTERVALEST": "%Y-%m-%d %I:%M:%S %p",
                },
            )

            return df
        
        @staticmethod
        def parse_ace(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=StringIO(csv_data),
                parse_dates=[
                    "instantEST",
                ],
                date_format={
                    "instantEST": "%Y-%m-%d %I:%M:%S %p",
                },
            )

            return df
        
        @staticmethod
        def parse_AncillaryServicesMCP(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 2 csv tables")
        
        @staticmethod
        def parse_cts(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=StringIO(csv_data),
                parse_dates=[
                    "CASEAPPROVALDATE", 
                    "SOLUTIONTIME",
                ],
                date_format={
                    "CASEAPPROVALDATE": "%Y-%m-%d %I:%M:%S %p",
                    "SOLUTIONTIME": "%Y-%m-%d %I:%M:%S %p",
                },
            )

            return df
        
        @staticmethod
        def parse_combinedwindsolar(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=StringIO(csv_data),
                parse_dates=[
                    "ForecastDateTimeEST", 
                    "ActualDateTimeEST",
                ],
                date_format={
                    "ForecastDateTimeEST": "%Y-%m-%d %I:%M:%S %p",
                    "ActualDateTimeEST": "%Y-%m-%d %I:%M:%S %p",
                },
                dtype={
                    "ActualHourEndingEST": pd.Int64Dtype(),
                }
            )

            return df
        
        @staticmethod
        def parse_WindForecast(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            dictionary = json.loads(text)

            df = pd.DataFrame(
                data=dictionary["Forecast"],
            ).astype(
                dtype={
                    "HourEndingEST": pd.Int64Dtype(),
                    "Value": pd.Float64Dtype(),
                }
            )

            df["DateTimeEST"] = pd.to_datetime(df["DateTimeEST"], format="%Y-%m-%d %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_wind(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=StringIO(csv_data),
                parse_dates=[
                    "ForecastDateTimeEST", 
                    "ActualDateTimeEST",
                ],
                date_format={
                    "ForecastDateTimeEST": "%Y-%m-%d %I:%M:%S %p",
                    "ActualDateTimeEST": "%Y-%m-%d %I:%M:%S %p",
                },
            )

            return df
        
        @staticmethod
        def parse_SolarForecast(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            dictionary = json.loads(text)

            df = pd.DataFrame(
                data=dictionary["Forecast"],
            ).astype(
                dtype={
                    "HourEndingEST": pd.Int64Dtype(),
                    "Value": pd.Float64Dtype(),
                }
            )

            df["DateTimeEST"] = pd.to_datetime(df["DateTimeEST"], format="%Y-%m-%d %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_Solar(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=StringIO(csv_data),
                parse_dates=[
                    "ForecastDateTimeEST", 
                    "ActualDateTimeEST",
                ],
                date_format={
                    "INTERVALEST": "%Y-%m-%d %I:%M:%S %p",
                    "ActualDateTimeEST": "%Y-%m-%d %I:%M:%S %p",
                },
                dtype={
                    "ActualHourEndingEST": pd.Int64Dtype(),
                }
            )

            return df
            

    report_mappings: dict[str, Report] = {
        "fuelmix": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getfuelmix",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_fuelmix,
        ),

        "ace": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getace",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_ace,
        ),

        "AncillaryServicesMCP": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getAncillaryServicesMCP",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_AncillaryServicesMCP,
        ),

        "cts": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getcts",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_cts,
        ),

        "combinedwindsolar": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getcombinedwindsolar",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_combinedwindsolar,
        ),

        "WindForecast": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWindForecast",
                supported_extensions=["xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_WindForecast,
        ),

        "Wind": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWind",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_combinedwindsolar,
        ),

        "SolarForecast": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolarForecast",
                supported_extensions=["xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_SolarForecast,
        ),

        "Solar": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolar",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_Solar,
        ),
    }

    @staticmethod
    def get_url(
        report_name: str,
        file_extension: str,
        ddatetime: datetime.datetime | None = None,
    ) -> str:
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
        file_extension: str, 
        ddatetime: datetime.datetime | None = None,
    ) -> requests.Response:
        url = MISOReports.get_url(report_name, file_extension, ddatetime)
        
        res = requests.get(url)
        if res.status_code != 200:
            raise requests.exceptions.RequestException(f"Request status code: {res.status_code}")

        return res
    
    @staticmethod
    def get_df(
        report_name: str,
        ddatetime: datetime.datetime | None = None,
    ) -> pd.DataFrame:

        report = MISOReports.report_mappings[report_name]

        response = MISOReports.get_response(
            report_name=report_name, 
            file_extension=report.type_to_parse, 
            ddatetime=ddatetime,
        )

        df = report.report_parser(response)
        
        return df


if __name__ == "__main__":
    a = "SolarForecast"
    print(MISOReports.get_df(a).head(2))
    print(MISOReports.get_df(a).dtypes)

    # print(MISOReports.get_response("AncillaryServicesMCP", "csv").text)
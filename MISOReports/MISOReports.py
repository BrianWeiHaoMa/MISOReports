import uuid
from abc import ABC, abstractmethod
from typing import Callable
import datetime
import json
import zipfile
import io

import requests
import pandas as pd


class URLBuilder(ABC):
    """A class to build URLs for MISO reports.
    """
    target_placeholder = str(uuid.uuid4())
    extension_placeholder = str(uuid.uuid4())
    
    def __init__(
        self,
        target: str,
        supported_extensions: list[str],
    ):
        """Constructor for URLBuilder class.

        :param str target: A string to be used in the URL to identify the report.
        :param list[str] supported_extensions: The different file types available for download.
        """
        self.target = target
        self.supported_extensions = supported_extensions

    @abstractmethod
    def build_url(
        self,
        file_extension: str,
        ddatetime: datetime.datetime | None,
    ) -> str:
        """Builds the URL to download from.

        :param str file_extension: The file type to download.
        :param datetime.datetime | None ddatetime: The date/datetime to download the report for.
        :return str: A URL to download the report from.
        """
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
    """A class for downloading MISO reports.
    """
    class Report:
        """A representation of a report for download.
        """
        def __init__(
            self,
            url_builder: URLBuilder,
            type_to_parse: str,
            parser: Callable[[requests.Response], pd.DataFrame],
        ):
            self.url_builder = url_builder
            self.type_to_parse = type_to_parse
            self.report_parser = parser

    
    class ReportParsers:
        """A class to hold the parsers for the different reports.

        :raises NotImplementedError: The parsing for the report has not 
            been implemented due to design decisions.
        """
        @staticmethod
        def parse_fuelmix(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
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
                filepath_or_buffer=io.StringIO(csv_data),
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
            raise NotImplementedError("Result contains 2 csv tables.")
        
        @staticmethod
        def parse_cts(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
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
                filepath_or_buffer=io.StringIO(csv_data),
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
        def parse_Wind(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
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
                filepath_or_buffer=io.StringIO(csv_data),
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
        def parse_exantelmp(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            return df
        
        @staticmethod
        def parse_da_exante_lmp(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[4:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            return df
        
        @staticmethod
        def parse_da_expost_lmp(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[4:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            return df
        
        @staticmethod
        def parse_rt_lmp_final(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[4:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            return df
        
        @staticmethod
        def parse_rt_lmp_prelim(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[4:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            return df
        
        @staticmethod
        def parse_DA_Load_EPNodes(
            res: requests.Response,
        ) -> pd.DataFrame:
            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                text = z.read(z.namelist()[0]).decode("utf-8")

            csv_data = "\n".join(text.splitlines()[4:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            return df
        
        @staticmethod
        def parse_DA_LMPs(
            res: requests.Response,
        ) -> pd.DataFrame:
            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                text = z.read(z.namelist()[0]).decode("utf-8")

            csv_data = "\n".join(text.splitlines()[1:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "MARKET_DAY", 
                ],
                date_format={
                    "MARKET_DAY": "%m/%d/%Y",
                },
            )

            return df
        
        @staticmethod
        def parse_5min_exante_lmp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=3,
            )

            return df
        
        @staticmethod
        def parse_nsi1(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "timestamp", 
                ],
                date_format="%Y-%m-%d %H:%M:%S",
            )

            return df
        
        @staticmethod
        def parse_nsi5(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "timestamp", 
                ],
                date_format="%Y-%m-%d %H:%M:%S",
            )

            return df
            
        @staticmethod
        def parse_nsi1miso(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "timestamp", 
                ],
                date_format="%Y-%m-%d %H:%M:%S",
            )

            return df
        
        @staticmethod
        def parse_nsi5miso(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "timestamp", 
                ],
                date_format="%Y-%m-%d %H:%M:%S",
            )

            return df
        
        @staticmethod
        def parse_importtotal5(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            dictionary = json.loads(text)

            df = pd.DataFrame(
                data=dictionary
            )

            df['Time'] = pd.to_datetime(df['Time'], format="%Y-%m-%d %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_reservebindingconstraints(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "Period", 
                ],
                date_format="%Y-%m-%dT%H:%M:%S",
            )

            return df
        
        @staticmethod
        def parse_totalload(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 3 csv tables.")
        
        @staticmethod
        def parse_RSG(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "MKT_INT_END_EST", 
                ],
                date_format="%Y-%m-%d %H:%M:%S %p",
            )

            return df
        
        @staticmethod
        def parse_WindActual(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            dictionary = json.loads(text)

            df = pd.DataFrame(
                data=dictionary["instance"],
            ).astype(
                dtype={
                    "HourEndingEST": pd.Int64Dtype(),
                    "Value": pd.Float64Dtype(),
                }
            )

            df["DateTimeEST"] = pd.to_datetime(df["DateTimeEST"], format="%Y-%m-%d %I:%M:%S %p")

            return df  

        @staticmethod
        def parse_SolarActual(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            dictionary = json.loads(text)

            df = pd.DataFrame(
                data=dictionary["instance"],
            ).astype(
                dtype={
                    "HourEndingEST": pd.Int64Dtype(),
                    "Value": pd.Float64Dtype(),
                }
            )

            df["DateTimeEST"] = pd.to_datetime(df["DateTimeEST"], format="%Y-%m-%d %I:%M:%S %p")

            return df 

        @staticmethod
        def parse_NAI(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            return df  
        
        @staticmethod
        def parse_regionaldirectionaltransfer(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "INTERVALEST", 
                ],
                date_format="%Y-%m-%d %H:%M:%S %p",
            )

            return df  
        
        @staticmethod
        def parse_generationoutagesplusminusfivedays(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "OutageDate", 
                ],
                date_format="%Y-%m-%d %H:%M:%S %p",
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
            parser=ReportParsers.parse_Wind,
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

        "exantelmp": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getexantelmp",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_exantelmp,
        ),

        "da_exante_lmp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_exante_lmp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_exante_lmp,
        ),

        "da_expost_lmp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_expost_lmp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_expost_lmp,
        ),

        "rt_lmp_final": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_lmp_final",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_lmp_final,
        ),

        "rt_lmp_prelim": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_lmp_prelim",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_lmp_prelim,
        ),

        "DA_Load_EPNodes": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="DA_Load_EPNodes",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_DA_Load_EPNodes,
        ),

        "DA_LMPs": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="DA_LMPs",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_current_month_name_to_two_months_later_name_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_DA_LMPs,
        ),

        "5min_exante_lmp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="5min_exante_lmp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_5min_exante_lmp,
        ),

        "nsi1": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi1",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi1,
        ),

        "nsi5": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi5",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi5,
        ),

        "nsi1miso": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi1miso",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi1miso,
        ),

        "nsi5miso": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi5miso",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi5miso,
        ),

        "importtotal5": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getimporttotal5",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_importtotal5,
        ),

        "reservebindingconstraints": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getreservebindingconstraints",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_reservebindingconstraints
        ),

        "RSG": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getRSG",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_RSG
        ),

        "totalload": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="gettotalload",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_totalload
        ),

        "WindActual": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWindActual",
                supported_extensions=["xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_WindActual
        ),

        "SolarActual": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolarActual",
                supported_extensions=["xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_SolarActual
        ),

        "NAI": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getNAI",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_NAI
        ),

        "regionaldirectionaltransfer": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getregionaldirectionaltransfer",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_regionaldirectionaltransfer
        ),

        "generationoutagesplusminusfivedays": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getgenerationoutagesplusminusfivedays",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_generationoutagesplusminusfivedays
        ),
    }

    @staticmethod
    def get_url(
        report_name: str,
        file_extension: str,
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
        file_extension: str, 
        ddatetime: datetime.datetime | None = None,
    ) -> requests.Response:
        """Get the response for the report download.

        :param str report_name: The name of the report.
        :param str file_extension: The type of file to download.
        :param datetime.datetime | None ddatetime: The date of the report, defaults to None
        """
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
        """Get a parsed DataFrame for the report.

        :param str report_name: The name of the report.
        :param datetime.datetime | None ddatetime: The date of the report, defaults to None
        :return pd.DataFrame: A DataFrame containing the data of the report.
        """
        report = MISOReports.report_mappings[report_name]

        response = MISOReports.get_response(
            report_name=report_name, 
            file_extension=report.type_to_parse, 
            ddatetime=ddatetime,
        )

        df = report.report_parser(response)
        
        return df

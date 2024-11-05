import uuid
from abc import ABC, abstractmethod
from typing import Callable
import datetime
import json
import zipfile
import io

import requests
import pandas as pd, pandas
import numpy as np, numpy


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
        url_generator: Callable[[datetime.datetime | None, str], str],
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
        
        res = self.url_generator(ddatetime, self.target)
        res = res.replace(URLBuilder.extension_placeholder, file_extension)
        return res

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
            example_url: str,
        ):
            """Constructor for Report class.

            :param URLBuilder url_builder: The URL builder to be used for the report.
            :param str type_to_parse: The type of the file to pass as input into the parser.
            :param Callable[[requests.Response], pd.DataFrame] parser: The parser for the report.
            :param str example_url: A working URL example for the report.
            """
            self.url_builder = url_builder
            self.type_to_parse = type_to_parse
            self.report_parser = parser
            self.example_url = example_url

    
    class ReportParsers:
        """A class to hold the parsers for the different reports.

        :raises NotImplementedError: The parsing for the report has not 
            been implemented due to design decisions.
        """
        @staticmethod
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
                }
            )

            df[["Preliminary Shadow Price"]] = df[["Preliminary Shadow Price"]].replace(r'[\$,()]', '', regex=True)
            df[["BP1", "PC1", "BP2", "PC2", "Preliminary Shadow Price"]] = df[["BP1", "PC1", "BP2", "PC2", "Preliminary Shadow Price"]].astype(numpy.dtypes.Float64DType())
            df[["Override"]] = df[["Override"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Market Date"]] = df[["Market Date"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["Hour of Occurrence"]] = df[["Hour of Occurrence"]].apply(pd.to_datetime, format="%H:%M")
            df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]] = df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]].astype(pandas.core.arrays.string_.StringDtype())

            return df

        @staticmethod
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

        @staticmethod
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

        @staticmethod
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

        @staticmethod
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

        @staticmethod
        def parse_da_pr(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result has an atypical format.")

        @staticmethod
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

        @staticmethod
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

        @staticmethod
        def parse_da_bcsf(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=3,
            )

            df[["From KV", "To KV"]] = df[["From KV", "To KV"]].round().astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Constraint ID", "Direction", "Constraint Name", "Contingency Name", "Constraint Type", "Flowgate Name", "Device Type", "Key1", "Key2", "Key3", "From Area", "To Area", "From Station", "To Station"]] = df[["Constraint ID", "Direction", "Constraint Name", "Contingency Name", "Constraint Type", "Flowgate Name", "Device Type", "Key1", "Key2", "Key3", "From Area", "To Area", "From Station", "To Station"]].astype(pandas.core.arrays.string_.StringDtype())

            return df

        @staticmethod
        def parse_rt_pr(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result has an atypical format.")

        @staticmethod
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

        @staticmethod
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

        @staticmethod
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

        @staticmethod
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

        @staticmethod
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
            df[["Flowgate NERC ID", "Constraint ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]] = df[["Flowgate NERC ID", "Constraint ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Hour of Occurrence"]] = df[["Hour of Occurrence"]].apply(pd.to_datetime, format="%H:%M")

            return df

        @staticmethod
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
            df[["Flowgate NERC ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason"]] = df[["Flowgate NERC ID", "Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Hour of Occurrence"]] = df[["Hour of Occurrence"]].apply(pd.to_datetime, format="%H:%M")

            return df

        @staticmethod
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

        @staticmethod
        def parse_Total_Uplift_by_Resource(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=6,
            ).iloc[:-2]

            return df

        @staticmethod
        def parse_ms_vlr_srw(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 2 csv tables.")

        @staticmethod
        def parse_ms_rsg_srw(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=7,
            ).iloc[:-2]

            df["previous 36 months"] = df["previous 36 months"].astype(pd.StringDtype())

            df = df.drop(columns=["Unnamed: 6"])

            return df

        @staticmethod
        def parse_ms_rnu_srw(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=8,
            ).iloc[:-2]

            df["previous 36 months"] = df["previous 36 months"].astype(pd.StringDtype())

            return df

        @staticmethod
        def parse_ms_ri_srw(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=7,
                dtype={
                    "Previous Months": pd.StringDtype(),
                }
            ).iloc[:-2]

            df = df.drop(columns=["Unnamed: 5"])

            return df

        @staticmethod
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

        @staticmethod
        def parse_ms_vlr_HIST_SRW(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=3,
            ).iloc[:-2]

            df[["OPERATING DATE"]] = df[["OPERATING DATE"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["SETTLEMENT RUN", "DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total"]] = df[["SETTLEMENT RUN", "DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total"]].astype(numpy.dtypes.Float64DType())
            df[["REGION", "CONSTRAINT"]] = df[["REGION", "CONSTRAINT"]].astype(pandas.core.arrays.string_.StringDtype())

            return df

        @staticmethod
        def parse_ms_ecf_srw(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=6,
                dtype={
                    "Unnamed: 0": pd.StringDtype(),
                }
            ).iloc[:-3]

            return df

        @staticmethod
        def parse_ccf_co(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[4:-1])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "OPERATING DATE",
                ],
                date_format="%m/%d/%Y",
            )

            hours = ["HOUR" + str(i) for i in range(1, 25)]
            df[hours] = df[hours].astype(float)

            return df

        @staticmethod
        def parse_ms_vlr_HIST(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[3:-3])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                parse_dates=[
                    "OPERATING DATE",
                ],
                date_format="%m/%d/%Y",
            )

            return df

        @staticmethod
        def parse_Daily_Uplift_by_Local_Resource_Zone(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 10 csv tables.")

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
                date_format="%Y-%m-%d %I:%M:%S %p",
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
                date_format="%Y-%m-%d %I:%M:%S %p",
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
                date_format="%Y-%m-%d %I:%M:%S %p",
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
            )

            df[["ForecastDateTimeEST", "ActualDateTimeEST"]] = df[["ForecastDateTimeEST", "ActualDateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")
            df[["ForecastHourEndingEST", "ActualHourEndingEST"]] = df[["ForecastHourEndingEST", "ActualHourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["ForecastWindValue", "ForecastSolarValue", "ActualWindValue", "ActualSolarValue"]] = df[["ForecastWindValue", "ForecastSolarValue", "ActualWindValue", "ActualSolarValue"]].astype(numpy.dtypes.Float64DType())

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
                },
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
                date_format="%Y-%m-%d %I:%M:%S %p",
                dtype={
                    "ActualHourEndingEST": pd.Int64Dtype(),
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
            )

            df[["DateTimeEST"]] = df[["DateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")
            df[["HourEndingEST"]] = df[["HourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())

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
                date_format="%Y-%m-%d %I:%M:%S %p",
                dtype={
                    "ActualHourEndingEST": pd.Int64Dtype(),
                },
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
            )

            df[["MARKET_DAY"]] = df[["MARKET_DAY"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
            df[["NODE", "TYPE", "VALUE"]] = df[["NODE", "TYPE", "VALUE"]].astype(pandas.core.arrays.string_.StringDtype())

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
            )

            df[["Unplanned", "Planned", "Forced", "Derated"]] = df[["Unplanned", "Planned", "Forced", "Derated"]].astype(pandas.core.arrays.integer.Int64Dtype())  
            df[["OutageDate"]] = df[["OutageDate"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S %p")
            df[["OutageMonthDay"]] = df[["OutageMonthDay"]].astype(pandas.core.arrays.string_.StringDtype())

            return df  
        
        @staticmethod
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
        
        @staticmethod
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
        
        @staticmethod
        def parse_realtimebindingconstraints(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["Price"]] = df[["Price"]].astype(numpy.dtypes.Float64DType())
            df[["BP1", "PC1", "BP2", "PC2"]] = df[["BP1", "PC1", "BP2", "PC2"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Period"]] = df[["Period"]].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S")
            df[["Name", "OVERRIDE", "CURVETYPE"]] = df[["Name", "OVERRIDE", "CURVETYPE"]].astype(pandas.core.arrays.string_.StringDtype())
            
            return df
        
        @staticmethod
        def parse_realtimebindingsrpbconstraints(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["Price"]] = df[["Price"]].astype(numpy.dtypes.Float64DType())
            df[["BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4"]] = df[["BP1", "PC1", "BP2", "PC2", "BP3", "PC3", "BP4", "PC4"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Period"]] = df[["Period"]].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S")
            df[["Name", "OVERRIDE", "REASON", "CURVETYPE"]] = df[["Name", "OVERRIDE", "REASON", "CURVETYPE"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_RT_Load_EPNodes(
            res: requests.Response,
        ) -> pd.DataFrame:
            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                text = z.read(z.namelist()[0]).decode("utf-8")

            csv_data = "\n".join(text.splitlines()[4:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )[:-3]

            df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
            df[["EPNode", "Value"]] = df[["EPNode", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
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
        
        @staticmethod
        def parse_bids_cb(
            res: requests.Response,
        ) -> pd.DataFrame:
            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                csv_data = z.read(z.namelist()[0]).decode("utf-8")

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["MW", "LMP", "PRICE1", "MW1", "PRICE2", "MW2", "PRICE3", "MW3", "PRICE4", "MW4", "PRICE5", "MW5", "PRICE6", "MW6", "PRICE7", "MW7", "PRICE8", "MW8", "PRICE9", "MW9"]] = df[["MW", "LMP", "PRICE1", "MW1", "PRICE2", "MW2", "PRICE3", "MW3", "PRICE4", "MW4", "PRICE5", "MW5", "PRICE6", "MW6", "PRICE7", "MW7", "PRICE8", "MW8", "PRICE9", "MW9"]].astype(numpy.dtypes.Float64DType())
            df[["Market Participant Code"]] = df[["Market Participant Code"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Date/Time Beginning (EST)", "Date/Time End (EST)"]] = df[["Date/Time Beginning (EST)", "Date/Time End (EST)"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
            df[["Region", "Type of Bid", "Bid ID"]] = df[["Region", "Type of Bid", "Bid ID"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_asm_exante_damcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 2 csv tables.")
        
        @staticmethod
        def parse_ftr_allocation_restoration(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 4 csv tables.")

        @staticmethod
        def parse_ftr_allocation_stage_1A(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 4 csv tables.")
        
        @staticmethod
        def parse_ftr_allocation_stage_1B(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 4 csv tables.")

        @staticmethod
        def parse_ftr_allocation_summary(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 2 csv tables.")
        
        @staticmethod
        def parse_ftr_annual_results_round_1(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 12 csv tables.")

        @staticmethod
        def parse_ftr_annual_results_round_2(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 12 csv tables.")

        @staticmethod
        def parse_ftr_annual_results_round_3(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 12 csv tables.")

        @staticmethod
        def parse_ftr_annual_bids_offers(
            res: requests.Response,
        ) -> pd.DataFrame:
            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                csv_data = z.read(z.namelist()[0]).decode("utf-8")

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )[:-3]

            df[["MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10"]] = df[["MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10"]].astype(numpy.dtypes.Float64DType())
            df[["Asset Owner ID", "Market Name", "Source", "Sink", "Hedge Type", "Class", "Type", "Round"]] = df[["Asset Owner ID", "Market Name", "Source", "Sink", "Hedge Type", "Class", "Type", "Round"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Start Date", "End Date"]] = df[["Start Date", "End Date"]].apply(pd.to_datetime, format="%m/%d/%Y")
            
            return df
        
        @staticmethod
        def parse_ftr_mpma_results(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 12 csv tables.")

        @staticmethod
        def parse_ftr_mpma_bids_offers(
            res: requests.Response,
        ) -> pd.DataFrame:
            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                csv_data = z.read(z.namelist()[0]).decode("utf-8")

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )[:-3]

            df[["MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10"]] = df[["MW1", "PRICE1", "MW2", "PRICE2", "MW3", "PRICE3", "MW4", "PRICE4", "MW5", "PRICE5", "MW6", "PRICE6", "MW7", "PRICE7", "MW8", "PRICE8", "MW9", "PRICE9", "MW10", "PRICE10"]].astype(numpy.dtypes.Float64DType())
            df[["Asset Owner ID", "Market Name", "Source", "Sink", "Hedge Type", "Class", "Type", "Round"]] = df[["Asset Owner ID", "Market Name", "Source", "Sink", "Hedge Type", "Class", "Type", "Round"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Start Date", "End Date"]] = df[["Start Date", "End Date"]].apply(pd.to_datetime, format="%m/%d/%Y")

            return df
        
        @staticmethod
        def parse_asm_expost_damcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 2 csv tables.")
        
        @staticmethod
        def parse_asm_rtmcp_final(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 2 csv tables.")
        
        @staticmethod
        def parse_asm_rtmcp_prelim(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 2 csv tables.")
        
        @staticmethod
        def parse_5min_exante_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=3,
            ).iloc[:-3]

            df[["RT Ex-Ante MCP Regulation", "RT Ex-Ante MCP Spin", "RT Ex-Ante MCP Supp"]] = df[["RT Ex-Ante MCP Regulation", "RT Ex-Ante MCP Spin", "RT Ex-Ante MCP Supp"]].astype(numpy.dtypes.Float64DType())
            df[["Zone"]] = df[["Zone"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Time (EST)"]] = df[["Time (EST)"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_5min_expost_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=3,
            ).iloc[:-3]

            df[["RT MCP Regulation", "RT MCP Spin", "RT MCP Supp"]] = df[["RT MCP Regulation", "RT MCP Spin", "RT MCP Supp"]].astype(numpy.dtypes.Float64DType())
            df[["Zone"]] = df[["Zone"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Time (EST)"]] = df[["Time (EST)"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_da_exante_ramp_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains atypical column arrangement.")
        
        @staticmethod
        def parse_da_exante_str_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains atypical column arrangement.")
        
        @staticmethod
        def parse_da_expost_ramp_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains atypical column arrangement.")
        
        @staticmethod
        def parse_da_expost_str_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains atypical column arrangement.")
        
        @staticmethod
        def parse_rt_expost_ramp_5min_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains atypical column arrangement.")
        
        @staticmethod
        def parse_rt_expost_ramp_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains atypical column arrangement.")
        
        @staticmethod
        def parse_rt_expost_str_5min_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains atypical column arrangement.")
        
        @staticmethod
        def parse_rt_expost_str_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains atypical column arrangement.")
        
        @staticmethod
        def parse_Allocation_on_MISO_Flowgates(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[:-2])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                thousands=',',
            )

            df[["Allocation (MW)"]] = df[["Allocation (MW)"]].astype(numpy.dtypes.Float64DType())
            df[["Allocation to Rating Percentage"]] = df[["Allocation to Rating Percentage"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["NERC ID", "Flowgate Owner", "Flowgate Description", "Entity", "Direction", "Reciprocal Status on Flowgate"]] = df[["NERC ID", "Flowgate Owner", "Flowgate Description", "Entity", "Direction", "Reciprocal Status on Flowgate"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_M2M_FFE(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[:-2])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                thousands=',',
            )

            df[["Adjusted FFE", "Non Monitoring RTO FFE"]] = df[["Adjusted FFE", "Non Monitoring RTO FFE"]].astype(numpy.dtypes.Float64DType())
            df[["NERC Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description"]] = df[["NERC Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Hour Ending"]] = df[["Hour Ending"]].apply(pd.to_datetime, format="%m/%d/%Y  %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_M2M_Flowgates_as_of(
            res: requests.Response,
        ) -> pd.DataFrame:
            csv_data = res.text

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description"]] = df[["Flowgate ID", "Monitoring RTO", "Non Monitoring RTO", "Flowgate Description"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_da_M2M_Settlement_srw(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Data not typically provided.")
        
        @staticmethod
        def parse_M2M_Settlement_srw(
            res: requests.Response,
        ) -> pd.DataFrame:
            csv_data = res.text

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df["HOUR_ENDING"] = [(datetime.datetime.strptime(dtime.replace(" 24:00:00", " 00:00:00"), "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S") if dtime.endswith("24:00:00") else dtime for dtime in df["HOUR_ENDING"]]
            
            df[["MISO_SHADOW_PRICE", "MISO_MKT_FLOW", "MISO_FFE", "CP_SHADOW_PRICE", "CP_MKT_FLOW", "CP_FFE", "MISO_CREDIT", "CP_CREDIT"]] = df[["MISO_SHADOW_PRICE", "MISO_MKT_FLOW", "MISO_FFE", "CP_SHADOW_PRICE", "CP_MKT_FLOW", "CP_FFE", "MISO_CREDIT", "CP_CREDIT"]].astype(numpy.dtypes.Float64DType())
            df[["FLOWGATE_ID", "MONITORING_RTO", "CP_RTO", "FLOWGATE_NAME"]] = df[["FLOWGATE_ID", "MONITORING_RTO", "CP_RTO", "FLOWGATE_NAME"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["HOUR_ENDING"]] = df[["HOUR_ENDING"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")

            return df
        
        @staticmethod
        def parse_MM_Annual_Report(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Result contains 5 .xlsx files.")
        
        @staticmethod
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
        
        @staticmethod
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
        
        @staticmethod
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
        
        @staticmethod
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
        
        @staticmethod
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
        
        @staticmethod
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
        
        @staticmethod
        def parse_sr_ctsl(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Data in pdf format.")

        @staticmethod
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
        
        @staticmethod
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
        
        @staticmethod
        def parse_da_bc_HIST(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:-3])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df["Shadow Price"] = df["Shadow Price"].replace(r'[\$,()]', '', regex=True)

            df[["Shadow Price", "BP1", "PC1", "BP2", "PC2"]] = df[["Shadow Price", "BP1", "PC1", "BP2", "PC2"]].astype(numpy.dtypes.Float64DType())
            df[["Hour of Occurrence", "Override"]] = df[["Hour of Occurrence", "Override"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Market Date"]] = df[["Market Date"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["Constraint Name", "Constraint_ID", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]] = df[["Constraint Name", "Constraint_ID", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_da_ex_rg(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=6,
            ).iloc[:-3]

            df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total"]] = df[["Demand Cleared (GWh) - Physical - Fixed", "Demand Cleared (GWh) - Physical - Price Sen.", "Demand Cleared (GWh) - Virtual", "Demand Cleared (GWh) - Total", "Supply Cleared (GWh) - Physical", "Supply Cleared (GWh) - Virtual", "Supply Cleared (GWh) - Total", "Net Scheduled Imports (GWh)", "Generation Resources Offered (GW at Econ. Max) - Must Run", "Generation Resources Offered (GW at Econ. Max) - Economic", "Generation Resources Offered (GW at Econ. Max) - Emergency", "Generation Resources Offered (GW at Econ. Max) - Total", "Generation Resources Offered (GW at Econ. Min) - Must Run", "Generation Resources Offered (GW at Econ. Min) - Economic", "Generation Resources Offered (GW at Econ. Min) - Emergency", "Generation Resources Offered (GW at Econ. Min) - Total"]].astype(numpy.dtypes.Float64DType())

            return df
        
        @staticmethod
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
        
        @staticmethod
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


    report_mappings: dict[str, Report] = {
        "rt_bc_HIST": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_bc_HIST",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_bc_HIST,
            example_url="https://docs.misoenergy.org/marketreports/2024_rt_bc_HIST.csv",
        ),

        "RT_UDS_Approved_Case_Percentage": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="RT_UDS_Approved_Case_Percentage",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_RT_UDS_Approved_Case_Percentage,
            example_url="https://docs.misoenergy.org/marketreports/20241023_RT_UDS_Approved_Case_Percentage.csv",
        ),

        "Resource_Uplift_by_Commitment_Reason": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="Resource_Uplift_by_Commitment_Reason",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_Resource_Uplift_by_Commitment_Reason,
            example_url="https://docs.misoenergy.org/marketreports/20241009_Resource_Uplift_by_Commitment_Reason.xlsx",
        ),

        "rt_rpe": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_rpe",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_rpe,
            example_url="https://docs.misoenergy.org/marketreports/20241101_rt_rpe.xls",
        ),

        "Historical_RT_RSG_Commitment": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="Historical_RT_RSG_Commitment",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_Historical_RT_RSG_Commitment,
            example_url="https://docs.misoenergy.org/marketreports/2024_Historical_RT_RSG_Commitment.csv",
        ),

        "da_pr": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_pr",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_da_pr,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_pr.xls",
        ),

        "da_pbc": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_pbc",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_pbc,
            example_url="https://docs.misoenergy.org/marketreports/20220107_da_pbc.csv",
        ),

        "da_bc": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_bc",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_da_bc,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_bc.xls",
        ),

        "da_bcsf": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_bcsf",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_da_bcsf,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_bcsf.xls",
        ),

        "rt_pr": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_pr",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_pr,
            example_url="https://docs.misoenergy.org/marketreports/20241026_rt_pr.xls",
        ),

        "rt_irsf": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_irsf",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_irsf,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_irsf.csv",
        ),

        "rt_mf": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_mf",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_rt_mf,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_mf.xlsx",
        ),

        "rt_ex": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_ex",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_ex,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_ex.xls",
        ),

        "rt_pbc": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_pbc",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_pbc,
            example_url="https://docs.misoenergy.org/marketreports/20241001_rt_pbc.csv",
        ),

        "rt_bc": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_bc",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_bc,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_bc.xls",
        ),

        "rt_or": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_or",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_or,
            example_url="https://docs.misoenergy.org/marketreports/20240910_rt_or.xls",
        ),

        "rt_fuel_on_margin": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_fuel_on_margin",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_rt_fuel_on_margin,
            example_url="https://docs.misoenergy.org/marketreports/2023_rt_fuel_on_margin.zip",
        ),

        "Total_Uplift_by_Resource": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="Total_Uplift_by_Resource",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_Total_Uplift_by_Resource,
            example_url="https://docs.misoenergy.org/marketreports/20241001_Total_Uplift_by_Resource.xlsx",
        ),

        "ms_vlr_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_vlr_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_vlr_srw,
            example_url="https://docs.misoenergy.org/marketreports/20240901_ms_vlr_srw.xlsx",
        ),

        "ms_rsg_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_rsg_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_rsg_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241104_ms_rsg_srw.xlsx",
        ),

        "ms_rnu_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_rnu_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_rnu_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241029_ms_rnu_srw.xlsx",
        ),

        "ms_ri_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_ri_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_ri_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241029_ms_ri_srw.xlsx",
        ),

        "MARKET_SETTLEMENT_DATA_SRW": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="MARKET_SETTLEMENT_DATA_SRW",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_no_date
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_MARKET_SETTLEMENT_DATA_SRW,
            example_url="https://docs.misoenergy.org/marketreports/MARKET_SETTLEMENT_DATA_SRW.zip",
        ),

        "ms_vlr_HIST_SRW": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_vlr_HIST_SRW",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_vlr_HIST_SRW,
            example_url="https://docs.misoenergy.org/marketreports/2024_ms_vlr_HIST_SRW.xlsx",
        ),

        "ms_ecf_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_ecf_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_ecf_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241029_ms_ecf_srw.xlsx",
        ),


        "ccf_co": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ccf_co",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_ccf_co,
            example_url="https://docs.misoenergy.org/marketreports/20241020_ccf_co.csv",
        ),

        "ms_vlr_HIST": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_vlr_HIST",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_ms_vlr_HIST,
            example_url="https://docs.misoenergy.org/marketreports/2022_ms_vlr_HIST.csv",
        ),

        "Daily_Uplift_by_Local_Resource_Zone": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="Daily_Uplift_by_Local_Resource_Zone",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_Daily_Uplift_by_Local_Resource_Zone,
            example_url="https://docs.misoenergy.org/marketreports/20241020_Daily_Uplift_by_Local_Resource_Zone.xlsx",
        ),

        "fuelmix": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getfuelmix",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_fuelmix,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getfuelmix&returnType=csv",
        ),

        "ace": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getace",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_ace,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getace&returnType=csv",
        ),

        "AncillaryServicesMCP": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getAncillaryServicesMCP",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_AncillaryServicesMCP,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getAncillaryServicesMCP&returnType=csv",
        ),

        "cts": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getcts",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_cts,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcts&returnType=csv",
        ),

        "combinedwindsolar": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getcombinedwindsolar",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_combinedwindsolar,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcombinedwindsolar&returnType=csv",
        ),

        "WindForecast": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWindForecast",
                supported_extensions=["xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_WindForecast,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindForecast&returnType=json",
        ),

        "Wind": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWind",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_Wind,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWind&returnType=csv",
        ),

        "SolarForecast": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolarForecast",
                supported_extensions=["xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_SolarForecast,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarForecast&returnType=json",
        ),

        "Solar": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolar",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_Solar,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolar&returnType=csv",
        ),

        "exantelmp": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getexantelmp",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_exantelmp,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getexantelmp&returnType=csv",
        ),

        "da_exante_lmp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_exante_lmp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_exante_lmp,
            example_url="https://docs.misoenergy.org/marketreports/20241026_da_exante_lmp.csv",
        ),

        "da_expost_lmp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_expost_lmp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_expost_lmp,
            example_url="https://docs.misoenergy.org/marketreports/20241026_da_expost_lmp.csv",
        ),

        "rt_lmp_final": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_lmp_final",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_lmp_final,
            example_url="https://docs.misoenergy.org/marketreports/20241021_rt_lmp_final.csv",
        ),

        "rt_lmp_prelim": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_lmp_prelim",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_lmp_prelim,
            example_url="https://docs.misoenergy.org/marketreports/20241103_rt_lmp_prelim.csv",
        ),

        "DA_Load_EPNodes": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="DA_Load_EPNodes",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_DA_Load_EPNodes,
            example_url="https://docs.misoenergy.org/marketreports/DA_Load_EPNodes_20241021.zip",
        ),

        "DA_LMPs": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="DA_LMPs",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_current_month_name_to_two_months_later_name_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_DA_LMPs,
            example_url="https://docs.misoenergy.org/marketreports/2024-Jul-Sep_DA_LMPs.zip",
        ),

        "5min_exante_lmp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="5min_exante_lmp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_5min_exante_lmp,
            example_url="https://docs.misoenergy.org/marketreports/20241025_5min_exante_lmp.xlsx",
        ),

        "nsi1": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi1",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi1,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1&returnType=csv",
        ),

        "nsi5": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi5",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi5,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5&returnType=csv",
        ),

        "nsi1miso": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi1miso",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi1miso,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1miso&returnType=csv",
        ),

        "nsi5miso": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi5miso",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi5miso,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5miso&returnType=csv",
        ),

        "importtotal5": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getimporttotal5",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_importtotal5,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getimporttotal5&returnType=json",
        ),

        "reservebindingconstraints": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getreservebindingconstraints",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_reservebindingconstraints,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getreservebindingconstraints&returnType=csv",
        ),

        "RSG": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getRSG",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_RSG,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getRSG&returnType=csv",
        ),

        "totalload": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="gettotalload",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_totalload,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=gettotalload&returnType=csv",
        ),

        "WindActual": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWindActual",
                supported_extensions=["xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_WindActual,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindActual&returnType=json",
        ),

        "SolarActual": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolarActual",
                supported_extensions=["xml", "json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_SolarActual,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarActual&returnType=json",
        ),

        "NAI": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getNAI",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_NAI,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getNAI&returnType=csv",
        ),

        "regionaldirectionaltransfer": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getregionaldirectionaltransfer",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_regionaldirectionaltransfer,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getregionaldirectionaltransfer&returnType=csv",
        ),

        "generationoutagesplusminusfivedays": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getgenerationoutagesplusminusfivedays",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_generationoutagesplusminusfivedays,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getgenerationoutagesplusminusfivedays&returnType=csv",
        ),

        "apiversion": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getapiversion",
                supported_extensions=["json"],
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_apiversion,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getapiversion&returnType=json",
        ),

        "lmpconsolidatedtable": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getlmpconsolidatedtable",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_lmpconsolidatedtable,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getlmpconsolidatedtable&returnType=csv",
        ),

        "realtimebindingconstraints": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getrealtimebindingconstraints",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_realtimebindingconstraints,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getrealtimebindingconstraints&returnType=csv",
        ),

        "realtimebindingsrpbconstraints": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getrealtimebindingsrpbconstraints",
                supported_extensions=["csv", "xml", "json"],
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_realtimebindingsrpbconstraints,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getrealtimebindingsrpbconstraints&returnType=csv",
        ),

        "RT_Load_EPNodes": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="RT_Load_EPNodes",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_RT_Load_EPNodes,
            example_url="https://docs.misoenergy.org/marketreports/RT_Load_EPNodes_20241018.zip",
        ),

        "5MIN_LMP": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="5MIN_LMP",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_5MIN_LMP,
            example_url="https://docs.misoenergy.org/marketreports/20241021_5MIN_LMP.zip",
        ),

        "bids_cb": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="bids_cb",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_bids_cb,
            example_url="https://docs.misoenergy.org/marketreports/20240801_bids_cb.zip",
        ),
        
        "asm_exante_damcp": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="asm_exante_damcp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_asm_exante_damcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_asm_exante_damcp.csv",
        ),

        "ftr_allocation_restoration": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_restoration",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_allocation_restoration,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_restoration.zip",
        ),

        "ftr_allocation_stage_1A": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_stage_1A",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_allocation_stage_1A,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1A.zip",
        ),

        "ftr_allocation_stage_1B": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_stage_1B",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_allocation_stage_1B,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1B.zip",
        ),

        "ftr_allocation_summary": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_summary",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_allocation_summary,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_summary.zip",
        ),

        "ftr_annual_results_round_1": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_results_round_1",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_annual_results_round_1,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_annual_results_round_1.zip",
        ),

        "ftr_annual_results_round_2": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_results_round_2",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_annual_results_round_2,
            example_url="https://docs.misoenergy.org/marketreports/20240501_ftr_annual_results_round_2.zip",
        ),

        "ftr_annual_results_round_3": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_results_round_3",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_annual_results_round_3,
            example_url="https://docs.misoenergy.org/marketreports/20240101_ftr_annual_results_round_3.zip",
        ),

        "ftr_annual_bids_offers": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_bids_offers",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_annual_bids_offers,
            example_url="https://docs.misoenergy.org/marketreports/2023_ftr_annual_bids_offers.zip",
        ),

        "ftr_mpma_results": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_mpma_results",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_mpma_results,
            example_url="https://docs.misoenergy.org/marketreports/20241101_ftr_mpma_results.zip",
        ),

        "ftr_mpma_bids_offers": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_mpma_bids_offers",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_mpma_bids_offers,
            example_url="https://docs.misoenergy.org/marketreports/20240801_ftr_mpma_bids_offers.zip",
        ),

        "asm_expost_damcp": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="asm_expost_damcp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_asm_expost_damcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_asm_expost_damcp.csv",
        ),

        "asm_rtmcp_final": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="asm_rtmcp_final",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_asm_rtmcp_final,
            example_url="https://docs.misoenergy.org/marketreports/20241026_asm_rtmcp_final.csv",
        ),

        "asm_rtmcp_prelim": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="asm_rtmcp_prelim",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_asm_rtmcp_prelim,
            example_url="https://docs.misoenergy.org/marketreports/20241029_asm_rtmcp_prelim.csv",
        ),

        "5min_exante_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="5min_exante_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_5min_exante_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_5min_exante_mcp.xlsx",
        ),

        "5min_expost_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="5min_expost_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_5min_expost_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241028_5min_expost_mcp.xlsx",
        ),

        "da_exante_ramp_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_exante_ramp_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_da_exante_ramp_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_exante_ramp_mcp.xlsx",
        ),

        "da_exante_str_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_exante_str_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_da_exante_str_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_exante_str_mcp.xlsx",
        ),

        "da_expost_ramp_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_expost_ramp_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_da_expost_ramp_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_expost_ramp_mcp.xlsx",
        ),

        "da_expost_str_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_expost_str_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_da_expost_str_mcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_expost_str_mcp.xlsx",
        ),

        "rt_expost_ramp_5min_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_expost_ramp_5min_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmm_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_rt_expost_ramp_5min_mcp,
            example_url="https://docs.misoenergy.org/marketreports/202410_rt_expost_ramp_5min_mcp.xlsx",
        ),

        "rt_expost_ramp_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_expost_ramp_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmm_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_rt_expost_ramp_mcp,
            example_url="https://docs.misoenergy.org/marketreports/202410_rt_expost_ramp_mcp.xlsx",
        ),

        "rt_expost_str_5min_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_expost_str_5min_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmm_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_rt_expost_str_5min_mcp,
            example_url="https://docs.misoenergy.org/marketreports/202409_rt_expost_str_5min_mcp.xlsx",
        ),

        "rt_expost_str_mcp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_expost_str_mcp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmm_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_rt_expost_str_mcp,
            example_url="https://docs.misoenergy.org/marketreports/202410_rt_expost_str_mcp.xlsx",
        ),

        "Allocation_on_MISO_Flowgates": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="Allocation_on_MISO_Flowgates",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_mm_dd_last,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_Allocation_on_MISO_Flowgates,
            example_url="https://docs.misoenergy.org/marketreports/Allocation_on_MISO_Flowgates_2024_10_29.csv",
        ),

        "M2M_FFE": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="M2M_FFE",
                supported_extensions=["CSV"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_mm_dd_last,
            ),
            type_to_parse="CSV",
            parser=ReportParsers.parse_M2M_FFE,
            example_url="https://docs.misoenergy.org/marketreports/M2M_FFE_2024_10_29.CSV",
        ),

        "M2M_Flowgates_as_of": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="M2M_Flowgates_as_of",
                supported_extensions=["CSV"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
            ),
            type_to_parse="CSV",
            parser=ReportParsers.parse_M2M_Flowgates_as_of,
            example_url="https://docs.misoenergy.org/marketreports/M2M_Flowgates_as_of_20241030.CSV",
        ),

        # Every download URL as of 2024-11-02 offered for this report was empty.
        "da_M2M_Settlement_srw": Report( 
             url_builder=MISOMarketReportsURLBuilder(
                target="da_M2M_Settlement_srw",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_last,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_M2M_Settlement_srw,
            example_url="https://docs.misoenergy.org/marketreports/da_M2M_Settlement_srw_2024.csv",
        ),

        "M2M_Settlement_srw": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="M2M_Settlement_srw",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_last,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_M2M_Settlement_srw,
            example_url="https://docs.misoenergy.org/marketreports/M2M_Settlement_srw_2024.csv",
        ),

        "MM_Annual_Report": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="MM_Annual_Report",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_MM_Annual_Report,
            example_url="https://docs.misoenergy.org/marketreports/20241030_MM_Annual_Report.zip",
        ),

        "asm_da_co": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="asm_da_co",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_asm_da_co,
            example_url="https://docs.misoenergy.org/marketreports/20240801_asm_da_co.zip",
        ),

        "asm_rt_co": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="asm_rt_co",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_asm_rt_co,
            example_url="https://docs.misoenergy.org/marketreports/20240801_asm_rt_co.zip",
        ),

        "Dead_Node_Report": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="Dead_Node_Report",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_Dead_Node_Report,
            example_url="https://docs.misoenergy.org/marketreports/Dead_Node_Report_20241030.xls",
        ),

        "rt_co": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="rt_co",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_rt_co,
            example_url="https://docs.misoenergy.org/marketreports/20240801_rt_co.zip",
        ),

        "da_co": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="da_co",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_da_co,
            example_url="https://docs.misoenergy.org/marketreports/20240801_da_co.zip",
        ),

        "cpnode_reszone": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="cpnode_reszone",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_cpnode_reszone,
            example_url="https://docs.misoenergy.org/marketreports/20241002_cpnode_reszone.xlsx"
        ),
        
        "sr_ctsl": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="sr_ctsl",
                supported_extensions=["pdf"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="pdf",
            parser=ReportParsers.parse_sr_ctsl,
            example_url="https://docs.misoenergy.org/marketreports/20241020_sr_ctsl.pdf",
        ),

        "df_al": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="df_al",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_df_al,
            example_url="https://docs.misoenergy.org/marketreports/20241030_df_al.xls",
        ),

        "rf_al": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="rf_al",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rf_al,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rf_al.xls",
        ),

        "da_bc_HIST": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="da_bc_HIST",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_bc_HIST,
            example_url="https://docs.misoenergy.org/marketreports/2024_da_bc_HIST.csv",
        ),

        "da_ex_rg": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_ex_rg",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_da_ex_rg,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_ex_rg.xlsx",
        ),

        "da_ex": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_ex",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_da_ex,
            example_url="https://docs.misoenergy.org/marketreports/20220321_da_ex.xls",
        ),

        "da_rpe": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_rpe",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_da_rpe,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_rpe.xls",
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
        url = MISOReports.get_url(
            report_name=report_name, 
            file_extension=file_extension, 
            ddatetime=ddatetime,
        )

        return MISOReports._get_response_helper(url)
    
    @staticmethod
    def _get_response_helper(
        url: str,
    ) -> requests.Response:
        res = requests.get(
            url=url,
            timeout=30,
        )

        res.raise_for_status()

        if res.status_code != 200:
            raise requests.exceptions.RequestException(f"Request status code: {res.status_code}")
        
        return res
    
    @staticmethod
    def get_df(
        report_name: str,
        url: str | None = None,
        ddatetime: datetime.datetime | None = None,
    ) -> pd.DataFrame:
        """Get a parsed DataFrame for the report.

        :param str report_name: The name of the report.
        :param str | None url: A url to download directly from, defaults to None
        :param datetime.datetime | None ddatetime: The date of the report, defaults to None
        :return pd.DataFrame: A DataFrame containing the data of the report.
        """
        report = MISOReports.report_mappings[report_name]

        if url is not None:
            response = MISOReports._get_response_helper(url)
        else:
            response = MISOReports.get_response(
                report_name=report_name, 
                file_extension=report.type_to_parse, 
                ddatetime=ddatetime,
            )

        df = report.report_parser(response)
        
        return df

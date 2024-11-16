import uuid
from abc import ABC, abstractmethod
from typing import Callable
import datetime
import json
import zipfile
import io
from xml.etree import ElementTree as ET

import requests
import pandas as pd, pandas
import numpy as np, numpy
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import pdfplumber

MULTI_DF_NAMES_COLUMN = "names"
MULTI_DF_DFS_COLUMN = "dfs"


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
        :param datetime.datetime | None ddatetime: The date/datetime to download the report for.
        :return str: A URL to download the report from.
        """
        pass

    def _build_url_extension_check(
        self,
        file_extension: str | None,
    ) -> str:
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
        super().__init__(
            target=target, 
            supported_extensions=supported_extensions,
            default_extension=default_extension,
        )

        self.url_generator = url_generator

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
        increment_mappings: dict[Callable[[datetime.datetime | None, str], str], relativedelta] = {
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

        if self.url_generator not in increment_mappings.keys():
            raise ValueError("This URL generator has no mapped increment.")    

        if ddatetime is None:
            return None
        else:
            return ddatetime + direction * increment_mappings[self.url_generator]

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
            example_datetime: datetime.datetime | None = None,
        ):
            """Constructor for Report class.

            :param URLBuilder url_builder: The URL builder to be used for the report.
            :param str type_to_parse: The type of the file to pass as input into the parser.
            :param Callable[[requests.Response], pd.DataFrame] parser: The parser for the report.
            :param str example_url: A working URL example for the report.
            :param datetime.datetime | None example_datetime: An example datetime for the report.
            """
            self.url_builder = url_builder
            self.type_to_parse = type_to_parse
            self.report_parser = parser
            self.example_url = example_url
            self.example_datetime = example_datetime

    
    class ReportParsers:
        """A class to hold the parsers for the different reports.

        :raises NotImplementedError: The parsing for the report has not 
            been implemented due to design decisions.
        """
        @staticmethod
        def parse_currentinterval(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(text),   
            )

            df[["LMP", "MLC", "MCC"]] = df[["LMP", "MLC", "MCC"]].astype(numpy.dtypes.Float64DType())
            df[["INTERVAL"]] = df[["INTERVAL"]].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S")
            df[["CPNODE"]] = df[["CPNODE"]].astype(pandas.core.arrays.string_.StringDtype())

            return df

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
                }, 
                low_memory=False,
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
            df1 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=6,
                nrows=2,
            )
            df1.rename(columns={df1.columns[0]: "Type"}, inplace=True)
            df1.drop(labels=df1.columns[5:], axis=1, inplace=True)
            df1[["Type"]] = df1[["Type"]].astype(pandas.core.arrays.string_.StringDtype())
            df1[["Demand Fixed", " Demand Price Sensitive", "Demand Virtual", "Demand Total"]] = df1[["Demand Fixed", " Demand Price Sensitive", "Demand Virtual", "Demand Total"]].astype(numpy.dtypes.Float64DType())

            df2 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=9,
                nrows=3,
            )
            df2.rename(columns={df2.columns[0]: "Type"}, inplace=True)
            df2.drop(labels=df2.columns[4:], axis=1, inplace=True)
            df2[["Type"]] = df2[["Type"]].astype(pandas.core.arrays.string_.StringDtype())
            df2[["Supply Physical", "Supply Virtual", "Supply Total"]] = df2[["Supply Physical", "Supply Virtual", "Supply Total"]].astype(numpy.dtypes.Float64DType())

            df3 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=14,
                nrows=24,
            )
            shared_column_names = list(df3.columns)[1:]

            df3.rename(columns={df3.columns[0]: "Hour"}, inplace=True)
            df3[["Hour"]] = df3[["Hour"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
            df3[shared_column_names] = df3[shared_column_names].astype(numpy.dtypes.Float64DType())            

            df4 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=39,
                nrows=3,
                names=["Around the Clock"] + shared_column_names,
            )

            df5 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=43,
                nrows=3,
                names=["On-Peak"] + shared_column_names,
            )

            df6 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=47,
                nrows=3,
                names=["Off-Peak"] + shared_column_names,
            )

            bottom_dfs = [df4, df5, df6]
            for i in range(len(bottom_dfs)):
                first_column = bottom_dfs[i].columns[0]
                bottom_dfs[i][[first_column]] = bottom_dfs[i][[first_column]].astype(pandas.core.arrays.string_.StringDtype())
                bottom_dfs[i][shared_column_names] = bottom_dfs[i][shared_column_names].astype(numpy.dtypes.Float64DType())

            # No names written for any of the tables in the report.
            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                        f"Table {i}" for i in range(1, 7)
                ], 
                MULTI_DF_DFS_COLUMN: [
                        df1, 
                        df2, 
                        df3,
                ] + bottom_dfs,
            })

            return df

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

            df[["From KV", "To KV", "Direction"]] = df[["From KV", "To KV", "Direction"]].round().astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Constraint ID", "Constraint Name", "Contingency Name", "Constraint Type", "Flowgate Name", "Device Type", "Key1", "Key2", "Key3", "From Area", "To Area", "From Station", "To Station"]] = df[["Constraint ID", "Constraint Name", "Contingency Name", "Constraint Type", "Flowgate Name", "Device Type", "Key1", "Key2", "Key3", "From Area", "To Area", "From Station", "To Station"]].astype(pandas.core.arrays.string_.StringDtype())

            return df

        @staticmethod
        def parse_rt_pr(
            res: requests.Response,
        ) -> pd.DataFrame:
            df1 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=6,
                nrows=1,
            )
            df1.rename(columns={df1.columns[0]: "Type"}, inplace=True)
            df1.drop(labels=df1.columns[4:], axis=1, inplace=True)
            df1[["Type"]] = df1[["Type"]].astype(pandas.core.arrays.string_.StringDtype())
            df1[["Demand", "Supply", "Total"]] = df1[["Demand", "Supply", "Total"]].astype(numpy.dtypes.Float64DType())

            df2 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=8,
                nrows=2,
            )
            df2.rename(columns={df2.columns[0]: "Type"}, inplace=True)
            df2.drop(labels=df2.columns[4:], axis=1, inplace=True)
            df2[["Type"]] = df2[["Type"]].astype(pandas.core.arrays.string_.StringDtype())
            df2[["Demand", "Supply", "Total"]] = df2[["Demand", "Supply", "Total"]].astype(numpy.dtypes.Float64DType())

            df3 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=11,
                nrows=24,
            )
            shared_column_names = list(df3.columns)[1:]

            df3.rename(columns={df3.columns[0]: "Hour"}, inplace=True)
            df3[["Hour"]] = df3[["Hour"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
            df3[shared_column_names] = df3[shared_column_names].astype(numpy.dtypes.Float64DType())            

            df4 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=36,
                nrows=3,
                names=["Around the Clock"] + shared_column_names,
            )

            df5 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=40,
                nrows=3,
                names=["On-Peak"] + shared_column_names,
            )

            df6 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=44,
                nrows=3,
                names=["Off-Peak"] + shared_column_names,
            )

            bottom_dfs = [df4, df5, df6]
            for i in range(len(bottom_dfs)):
                first_column = bottom_dfs[i].columns[0]
                bottom_dfs[i][[first_column]] = bottom_dfs[i][[first_column]].astype(pandas.core.arrays.string_.StringDtype())
                bottom_dfs[i][shared_column_names] = bottom_dfs[i][shared_column_names].astype(numpy.dtypes.Float64DType())

            # No names written for any of the tables in the report.
            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                        f"Table {i}" for i in range(1, 7)
                ], 
                MULTI_DF_DFS_COLUMN: [
                        df1, 
                        df2, 
                        df3,
                ] + bottom_dfs,
            })

            return df

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
            df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]] = df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Constraint ID", "Flowgate NERC ID"]] = df[["Constraint ID", "Flowgate NERC ID"]].astype(pandas.core.arrays.integer.Int64Dtype()).astype(pandas.core.arrays.string_.StringDtype())            
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
            df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason"]] = df[["Constraint Name", "Branch Name ( Branch Type / From CA / To CA )", "Contingency Description", "Constraint Description", "Curve Type", "Reason"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Flowgate NERC ID"]] = df[["Flowgate NERC ID"]].astype(pandas.core.arrays.integer.Int64Dtype()).astype(pandas.core.arrays.string_.StringDtype())            
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

            df[["Total Uplift Amount"]] = df[["Total Uplift Amount"]].astype(numpy.dtypes.Float64DType())
            df[["Resource Name"]] = df[["Resource Name"]].astype(pandas.core.arrays.string_.StringDtype())

            return df

        @staticmethod
        def parse_ms_vlr_srw(
            res: requests.Response,
        ) -> pd.DataFrame:
            float_columns = ["DA VLR RSG MWP", "RT VLR RSG MWP", "DA+RT Total"]
            string_columns = ["Constraint"]
            column_names = string_columns + float_columns

            df1 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=7,
                nrows=3,
                usecols=column_names,
            )
            df1[float_columns] = df1[float_columns].astype(numpy.dtypes.Float64DType())
            df1[string_columns] = df1[string_columns].astype(pandas.core.arrays.string_.StringDtype())

            df2 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=15,
                nrows=7,
                usecols=column_names,
            )
            df2[float_columns] = df2[float_columns].astype(numpy.dtypes.Float64DType())
            df2[string_columns] = df2[string_columns].astype(pandas.core.arrays.string_.StringDtype())

            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                        f"Table {i}" for i in range(1, 3)
                ], 
                MULTI_DF_DFS_COLUMN: [
                        df1, 
                        df2, 
                ],
            })

            return df

        @staticmethod
        def parse_ms_rsg_srw(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=7,
            ).iloc[:-2]

            df[["MISO_RT_RSG_DIST2", "RT_RSG_DIST1", "RT_RSG_MWP", "DA_RSG_MWP", "DA_RSG_DIST"]] = df[["MISO_RT_RSG_DIST2", "RT_RSG_DIST1", "RT_RSG_MWP", "DA_RSG_MWP", "DA_RSG_DIST"]].astype(numpy.dtypes.Float64DType())
            df[["previous 36 months"]] = df[["previous 36 months"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["START", "STOP"]] = df[["START", "STOP"]].apply(pd.to_datetime, format="%m/%d/%Y")
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

            df[["JOA_MISO_UPLIFT", "MISO_RT_GFACO_DIST", "MISO_RT_GFAOB_DIST", "MISO_RT_RSG_DIST2", "RT_CC", "DA_RI", "RT_RI", "ASM_RI", "STRDFC_UPLIFT", "CRDFC_UPLIFT", "MISO_PV_MWP_UPLIFT", "MISO_DRR_COMP_UPL", "MISO_TOT_MIL_UPL", "RC_DIST", "TOTAL RNU"]] = df[["JOA_MISO_UPLIFT", "MISO_RT_GFACO_DIST", "MISO_RT_GFAOB_DIST", "MISO_RT_RSG_DIST2", "RT_CC", "DA_RI", "RT_RI", "ASM_RI", "STRDFC_UPLIFT", "CRDFC_UPLIFT", "MISO_PV_MWP_UPLIFT", "MISO_DRR_COMP_UPL", "MISO_TOT_MIL_UPL", "RC_DIST", "TOTAL RNU"]].astype(numpy.dtypes.Float64DType())
            df[["previous 36 months"]] = df[["previous 36 months"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["START", "STOP"]] = df[["START", "STOP"]].apply(pd.to_datetime, format="$m/$d/Y")
            
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

            df[["DA RI", "RT RI", "TOTAL RI"]] = df[["DA RI", "RT RI", "TOTAL RI"]].astype(numpy.dtypes.Float64DType())
            df[["Previous Months"]] = df[["Previous Months"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["START", "STOP"]] = df[["START", "STOP"]].apply(pd.to_datetime, format="%m/%d/%Y")
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
            ).iloc[:-3]

            df[["Da Xs Cg Fnd", "Rt Cc", "Rt Xs Cg Fnd", "Ftr Auc Res", "Ao Ftr Mn Alc", "Ftr Yr Alc *", "Tbs Access", "Net Ecf", "Ftr Shrtfll", "Net Ftr Sf", "Ftr Trg Cr Alc", "Ftr Hr Alc", "Hr Mf", "Hourly Ftr Allocation", "Monthly Ftr Allocation"]] = df[["Da Xs Cg Fnd", "Rt Cc", "Rt Xs Cg Fnd", "Ftr Auc Res", "Ao Ftr Mn Alc", "Ftr Yr Alc *", "Tbs Access", "Net Ecf", "Ftr Shrtfll", "Net Ftr Sf", "Ftr Trg Cr Alc", "Ftr Hr Alc", "Hr Mf", "Hourly Ftr Allocation", "Monthly Ftr Allocation"]].replace(',','', regex=True).astype(numpy.dtypes.Float64DType())
            df[["Unnamed: 0"]] = df[["Unnamed: 0"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Start", "Stop"]] = df[["Start", "Stop"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df = df.drop(columns=["Unnamed: 11"])

            return df

        @staticmethod
        def parse_ccf_co(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[4:-1])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["HOUR1", "HOUR2", "HOUR3", "HOUR4", "HOUR5", "HOUR6", "HOUR7", "HOUR8", "HOUR9", "HOUR10", "HOUR11", "HOUR12", "HOUR13", "HOUR14", "HOUR15", "HOUR16", "HOUR17", "HOUR18", "HOUR19", "HOUR20", "HOUR21", "HOUR22", "HOUR23", "HOUR24"]] = df[["HOUR1", "HOUR2", "HOUR3", "HOUR4", "HOUR5", "HOUR6", "HOUR7", "HOUR8", "HOUR9", "HOUR10", "HOUR11", "HOUR12", "HOUR13", "HOUR14", "HOUR15", "HOUR16", "HOUR17", "HOUR18", "HOUR19", "HOUR20", "HOUR21", "HOUR22", "HOUR23", "HOUR24"]].astype(numpy.dtypes.Float64DType())
            df[["CONSTRAINT NAME", "NODE NAME"]] = df[["CONSTRAINT NAME", "NODE NAME"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["OPERATING DATE"]] = df[["OPERATING DATE"]].apply(pd.to_datetime, format="%m/%d/%Y")

            return df

        @staticmethod
        def parse_ms_vlr_HIST(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[3:-3])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total"]] = df[["DA_VLR_MWP", "RT_VLR_MWP", "DA+RT Total"]].astype(numpy.dtypes.Float64DType())
            df[["SETTLEMENT RUN"]] = df[["SETTLEMENT RUN"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["REGION", "CONSTRAINT"]] = df[["REGION", "CONSTRAINT"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["OPERATING DATE"]] = df[["OPERATING DATE"]].apply(pd.to_datetime, format="%m/%d/%Y")

            return df

        @staticmethod
        def parse_Daily_Uplift_by_Local_Resource_Zone(
            res: requests.Response,
        ) -> pd.DataFrame:
            df0 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=9,
                nrows=1,
            )

            month_string = df0.iloc[0, 0]
            year_string = df0.iloc[0, 1]
            
            if type(year_string) == str and type(month_string) == str:
                year_string = year_string[-4:]
            else:
                raise ValueError("Unexpected: year_string or month_string is not a string.")
            
            date_string = f"{month_string} {year_string}"
            month_days = pd.Period(date_string, freq='M').days_in_month
            n_rows = month_days + 1
            
            def parse_report_part(skiprows: int) -> pd.DataFrame:
                df = pd.read_excel(
                    io=io.BytesIO(res.content),
                    skiprows=skiprows,
                    nrows=n_rows,
                )
                df.rename(columns={df.columns[1]: "Date"}, inplace=True)
                df.drop(labels=df.columns[0], axis=1, inplace=True)

                df[["Date"]] = df[["Date"]].astype(pandas.core.arrays.string_.StringDtype())
                df[["Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments\n"]] = df[["Day Ahead Capacity", "Day Ahead VLR", "Real Time Capacity", "Real Time VLR", "Real Time Transmission Reliability", "Price Volatility Make Whole Payments\n"]].astype(numpy.dtypes.Float64DType())

                return df

            dfs = [] # There should be 10 dfs.

            for i in range(10):
                df = parse_report_part(9 + (4 + n_rows) * i)
                dfs.append(df)

            table_names = [
                "LRZ 1",
                "LRZ 10",
                "LRZ 2",
                "LRZ 3",
                "LRZ 4",
                "LRZ 5",
                "LRZ 6",
                "LRZ 7",
                "LRZ 8",
                "LRZ 9",
            ]

            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: table_names, 
                MULTI_DF_DFS_COLUMN: dfs,
            })

            return df

        @staticmethod
        def parse_fuelmix(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["ACT", "TOTALMW"]] = df[["ACT", "TOTALMW"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["CATEGORY"]] = df[["CATEGORY"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["INTERVALEST"]] = df[["INTERVALEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_ace(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["value"]] = df[["value"]].astype(numpy.dtypes.Float64DType())
            df[["instantEST"]] = df[["instantEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_AncillaryServicesMCP(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv1, csv2, csv3 = text.split("\n\n")

            df1 = pd.read_csv(
                filepath_or_buffer=io.StringIO("\n".join(csv1.split(","))),
            )

            df1[["RefId"]] = df1[["RefId"]].astype(pandas.core.arrays.string_.StringDtype())

            csv2_lines = csv2.splitlines()
            
            df2 = pd.read_csv(
                filepath_or_buffer=io.StringIO("\n".join(csv2_lines[1:])),
            )

            df2.rename(columns={" GenRegMCP": "GenRegMCP"}, inplace=True)

            df2[["number"]] = df2[["number"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df2[["GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp"]] = df2[["GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp"]].astype(numpy.dtypes.Float64DType())
    
            csv3_lines = csv3.splitlines()

            df3 = pd.read_csv(
                filepath_or_buffer=io.StringIO("\n".join(csv3_lines[1:])),
            )

            df3[["number"]] = df3[["number"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df3[["GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp"]] = df3[["GenRegMCP", "GenSpinMCP", "GenSuppMCP", "StrMcp", "DemandRegMcp", "DemandSpinMcp", "DemandSuppMCP", "RcpUpMcp", "RcpDownMcp"]].astype(numpy.dtypes.Float64DType())
            
            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                        "Interval", 
                        f"{csv2_lines[0]}", 
                        f"{csv3_lines[0]}"
                ], 
                MULTI_DF_DFS_COLUMN: [
                        df1, 
                        df2, 
                        df3
                ],
            })
            
            return df
        
        @staticmethod
        def parse_cts(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["PJMFORECASTEDLMP"]] = df[["PJMFORECASTEDLMP"]].astype(numpy.dtypes.Float64DType())
            df[["CASEAPPROVALDATE", "SOLUTIONTIME"]] = df[["CASEAPPROVALDATE", "SOLUTIONTIME"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

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
            )

            df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())
            df[["HourEndingEST"]] = df[["HourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["DateTimeEST"]] = df[["DateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_Wind(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["ForecastValue", "ActualValue"]] = df[["ForecastValue", "ActualValue"]].astype(numpy.dtypes.Float64DType())
            df[["ForecastHourEndingEST", "ActualHourEndingEST"]] = df[["ForecastHourEndingEST", "ActualHourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["ForecastDateTimeEST", "ActualDateTimeEST"]] = df[["ForecastDateTimeEST", "ActualDateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

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
            )

            df[["ForecastValue", "ActualValue"]] = df[["ForecastValue", "ActualValue"]].astype(numpy.dtypes.Float64DType())
            df[["ForecastHourEndingEST", "ActualHourEndingEST"]] = df[["ForecastHourEndingEST", "ActualHourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["ForecastDateTimeEST", "ActualDateTimeEST"]] = df[["ForecastDateTimeEST", "ActualDateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

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

            df[["LMP", "Loss", "Congestion"]] = df[["LMP", "Loss", "Congestion"]].astype(numpy.dtypes.Float64DType())
            df[["Name"]] = df[["Name"]].astype(pandas.core.arrays.string_.StringDtype())

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

            df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df[["Node", "Type", "Value"]] = df[["Node", "Type", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

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

            df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df[["Node", "Type", "Value"]] = df[["Node", "Type", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

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

            df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df[["Node", "Type", "Value"]] = df[["Node", "Type", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

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

            df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df[["Node", "Type", "Value"]] = df[["Node", "Type", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

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

            df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
            df[["EPNode", "Value"]] = df[["EPNode", "Value"]].astype(pandas.core.arrays.string_.StringDtype())

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
            ).iloc[:-1]

            df[["RT Ex-Ante LMP", "RT Ex-Ante MEC", "RT Ex-Ante MLC", "RT Ex-Ante MCC"]] = df[["RT Ex-Ante LMP", "RT Ex-Ante MEC", "RT Ex-Ante MLC", "RT Ex-Ante MCC"]].astype(numpy.dtypes.Float64DType())
            df[["CP Node"]] = df[["CP Node"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Time (EST)"]] = df[["Time (EST)"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

            return df
        
        @staticmethod
        def parse_nsi1(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["timestamp"]] = df[["timestamp"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")
            df[["AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE"]] = df[["AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE"]].astype(pandas.core.arrays.integer.Int64Dtype())

            return df
        
        @staticmethod
        def parse_nsi5(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["timestamp"]] = df[["timestamp"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")
            df[["AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE"]] = df[["AEC", "AECI", "CSWS", "GLHB", "LGEE", "MHEB", "MISO", "OKGE", "ONT", "PJM", "SOCO", "SPA", "SWPP", "TVA", "WAUE"]].astype(pandas.core.arrays.integer.Int64Dtype())

            return df
            
        @staticmethod
        def parse_nsi1miso(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["timestamp"]] = df[["timestamp"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")
            df[["NSI"]] = df[["NSI"]].astype(pandas.core.arrays.integer.Int64Dtype())

            return df
        
        @staticmethod
        def parse_nsi5miso(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["timestamp"]] = df[["timestamp"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S")
            df[["NSI"]] = df[["NSI"]].astype(pandas.core.arrays.integer.Int64Dtype())

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

            df[["Time"]] = df[["Time"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")
            df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())

            return df
        
        @staticmethod
        def parse_reservebindingconstraints(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["Price"]] = df[["Price"]].astype(numpy.dtypes.Float64DType())
            df[["Period"]] = df[["Period"]].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S")
            df[["Name", "Description"]] = df[["Name", "Description"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_totalload(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text

            table_1 = "ClearedMW"
            df1 = pd.read_csv(
                filepath_or_buffer=io.StringIO(text),
                skiprows=3,
                nrows=24,
            )
            df1[["Load_Hour"]] = df1[["Load_Hour"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df1[["Load_Value"]] = df1[["Load_Value"]].astype(numpy.dtypes.Float64DType())

            table_2 = "MediumTermLoadForecast"
            df2 = pd.read_csv(
                filepath_or_buffer=io.StringIO(text),
                skiprows=29,
                nrows=24,
            )
            df2[["Hour_End"]] = df2[["Hour_End"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df2[["Load_Forecast"]] = df2[["Load_Forecast"]].astype(numpy.dtypes.Float64DType())

            table_3 = "FiveMinTotalLoad"
            df3 = pd.read_csv(
                filepath_or_buffer=io.StringIO(text),
                skiprows=55,
            )
            df3[["Load_Time"]] = df3[["Load_Time"]].apply(pd.to_datetime, format="%H:%M")
            df3[["Load_Value"]] = df3[["Load_Value"]].astype(numpy.dtypes.Float64DType())

            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                    table_1,
                    table_2,
                    table_3,
                ],
                MULTI_DF_DFS_COLUMN: [
                    df1,
                    df2,
                    df3,
                ],
            })

            return df
        
        @staticmethod
        def parse_RSG(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["TOTAL_ECON_MAX"]] = df[["TOTAL_ECON_MAX"]].astype(numpy.dtypes.Float64DType())
            df[["MKT_INT_END_EST"]] = df[["MKT_INT_END_EST"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S %p")
            df[["COMMIT_REASON", "NUM_RESOURCES"]] = df[["COMMIT_REASON", "NUM_RESOURCES"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_WindActual(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            dictionary = json.loads(text)

            df = pd.DataFrame(
                data=dictionary["instance"],
            )

            df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())
            df[["HourEndingEST"]] = df[["HourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["DateTimeEST"]] = df[["DateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

            return df  

        @staticmethod
        def parse_SolarActual(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            dictionary = json.loads(text)

            df = pd.DataFrame(
                data=dictionary["instance"],
            )

            df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())
            df[["HourEndingEST"]] = df[["HourEndingEST"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["DateTimeEST"]] = df[["DateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

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

            df[["Name"]] = df[["Name"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Value"]] = df[["Value"]].astype(numpy.dtypes.Float64DType())

            return df  
        
        @staticmethod
        def parse_regionaldirectionaltransfer(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[2:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["NORTH_SOUTH_LIMIT", "SOUTH_NORTH_LIMIT", "RAW_MW", " UDSFLOW_MW"]] = df[["NORTH_SOUTH_LIMIT", "SOUTH_NORTH_LIMIT", "RAW_MW", " UDSFLOW_MW"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["INTERVALEST"]] = df[["INTERVALEST"]].apply(pd.to_datetime, format="%Y-%m-%d %H:%M:%S %p")

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
            text = res.text

            second_table_start_idx = text.index("Pnode,Zone,MCP Type")

            table_1 = "Table 1"
            df1 = pd.read_csv(
                filepath_or_buffer=io.StringIO(text[:second_table_start_idx]),
                skiprows=4,
                nrows=24,
            )
            hours = [" HE 1"] + [f"HE {i}" for i in range(2, 25)]
            df1[hours] = df1[hours].astype(numpy.dtypes.Float64DType())
            df1[df1.columns[:3]] = df1[df1.columns[:3]].astype(pandas.core.arrays.string_.StringDtype())

            table_2 = "Table 2"
            df2 = pd.read_csv(
                filepath_or_buffer=io.StringIO(text[second_table_start_idx:]),
            )
            df2[hours] = df2[hours].astype(numpy.dtypes.Float64DType())
            df2[["Pnode", "Zone", "MCP Type"]] = df2[["Pnode", "Zone", "MCP Type"]].astype(pandas.core.arrays.string_.StringDtype())

            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                    table_1,
                    table_2,
                ],
                MULTI_DF_DFS_COLUMN: [
                    df1,
                    df2,
                ],
            })

            return df
        
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
            files_by_type = defaultdict(list)

            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                for filename in z.namelist():
                    prefix = filename.split('_')[0]
                    
                    files_by_type[prefix].append({
                        "name": filename, 
                        "data": z.read(filename).decode("utf-8"),
                    })

            df_names = []
            dfs = []

            for csv_file in files_by_type["BindingConstraint"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
                df[["Flow", "Limit", "MarginalCost", "Violation"]] = df[["Flow", "Limit", "MarginalCost", "Violation"]].astype(numpy.dtypes.Float64DType())
                df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]] = df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]].astype(pandas.core.arrays.string_.StringDtype())

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)

            for csv_file in files_by_type["MarketResults"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["MW", "ClearingPrice"]] = df[["MW", "ClearingPrice"]].astype(numpy.dtypes.Float64DType())
                df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "Round", "HedgeType", "Type", "Class"]] = df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "Round", "HedgeType", "Type", "Class"]].astype(pandas.core.arrays.string_.StringDtype())
                df[["StartDate", "EndDate"]] = df[["StartDate", "EndDate"]].apply(pd.to_datetime, format="%m/%d/%Y")

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)
            
            for csv_file in files_by_type["SourceSinkShadowPrices"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
                df[["ShadowPrice"]] = df[["ShadowPrice"]].astype(numpy.dtypes.Float64DType())
                df[["SourceSink", "Class"]] = df[["SourceSink", "Class"]].astype(pandas.core.arrays.string_.StringDtype())

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)
                
            df = pd.DataFrame(data={
                MULTI_DF_NAMES_COLUMN: df_names, 
                MULTI_DF_DFS_COLUMN: dfs,
            })
            
            return df

        @staticmethod
        def parse_ftr_annual_results_round_2(
            res: requests.Response,
        ) -> pd.DataFrame:
            files_by_type = defaultdict(list)

            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                for filename in z.namelist():
                    filepath = filename.split('/')
                    prefix = filepath[1].split('_')[0]
                    
                    files_by_type[prefix].append({
                        "name": filename, 
                        "data": z.read(filename).decode("utf-8"),
                    })

            df_names = []
            dfs = []

            for csv_file in files_by_type["BindingConstraint"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
                df[["Flow", "Limit", "MarginalCost", "Violation"]] = df[["Flow", "Limit", "MarginalCost", "Violation"]].astype(numpy.dtypes.Float64DType())
                df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]] = df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]].astype(pandas.core.arrays.string_.StringDtype())

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)

            for csv_file in files_by_type["MarketResults"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["MW", "ClearingPrice"]] = df[["MW", "ClearingPrice"]].astype(numpy.dtypes.Float64DType())
                df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "Round", "HedgeType", "Type", "Class"]] = df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "Round", "HedgeType", "Type", "Class"]].astype(pandas.core.arrays.string_.StringDtype())
                df[["StartDate", "EndDate"]] = df[["StartDate", "EndDate"]].apply(pd.to_datetime, format="%m/%d/%Y")

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)
            
            for csv_file in files_by_type["SourceSinkShadowPrices"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
                df[["ShadowPrice"]] = df[["ShadowPrice"]].astype(numpy.dtypes.Float64DType())
                df[["SourceSink", "Class"]] = df[["SourceSink", "Class"]].astype(pandas.core.arrays.string_.StringDtype())

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)
                
            df = pd.DataFrame(data={
                MULTI_DF_NAMES_COLUMN: df_names, 
                MULTI_DF_DFS_COLUMN: dfs,
            })
            
            return df

        @staticmethod
        def parse_ftr_annual_results_round_3(
            res: requests.Response,
        ) -> pd.DataFrame:
            files_by_type = defaultdict(list)

            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                for filename in z.namelist():
                    filepath = filename.split('/')
                    prefix = filepath[1].split('_')[0]
                    
                    files_by_type[prefix].append({
                        "name": filename, 
                        "data": z.read(filename).decode("utf-8"),
                    })

            df_names = []
            dfs = []

            for csv_file in files_by_type["BindingConstraint"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
                df[["Flow", "Limit", "MarginalCost", "Violation"]] = df[["Flow", "Limit", "MarginalCost", "Violation"]].astype(numpy.dtypes.Float64DType())
                df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]] = df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]].astype(pandas.core.arrays.string_.StringDtype())

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)

            for csv_file in files_by_type["MarketResults"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["MW", "ClearingPrice"]] = df[["MW", "ClearingPrice"]].astype(numpy.dtypes.Float64DType())
                df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "Round", "HedgeType", "Type", "Class"]] = df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "Round", "HedgeType", "Type", "Class"]].astype(pandas.core.arrays.string_.StringDtype())
                df[["StartDate", "EndDate"]] = df[["StartDate", "EndDate"]].apply(pd.to_datetime, format="%m/%d/%Y")

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)
            
            for csv_file in files_by_type["SourceSinkShadowPrices"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
                df[["ShadowPrice"]] = df[["ShadowPrice"]].astype(numpy.dtypes.Float64DType())
                df[["SourceSink", "Class"]] = df[["SourceSink", "Class"]].astype(pandas.core.arrays.string_.StringDtype())

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)
                
            df = pd.DataFrame(data={
                MULTI_DF_NAMES_COLUMN: df_names, 
                MULTI_DF_DFS_COLUMN: dfs,
            })
            
            return df

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
            files_by_type = defaultdict(list)

            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                for filename in z.namelist():
                    filepath = filename.split('/')
                    prefix = filepath[1].split('_')[0]
                    
                    files_by_type[prefix].append({
                        "name": filename, 
                        "data": z.read(filename).decode("utf-8"),
                    })

            df_names = []
            dfs = []

            for csv_file in files_by_type["BindingConstraint"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
                df[["Flow", "Limit", "MarginalCost", "Violation"]] = df[["Flow", "Limit", "MarginalCost", "Violation"]].astype(numpy.dtypes.Float64DType())
                df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]] = df[["DeviceName", "DeviceType", "ControlArea", "Direction", "Contingency", "Class", "Description"]].astype(pandas.core.arrays.string_.StringDtype())

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)

            for csv_file in files_by_type["MarketResults"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["MW", "ClearingPrice"]] = df[["MW", "ClearingPrice"]].astype(numpy.dtypes.Float64DType())
                df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "Round", "HedgeType", "Type", "Class"]] = df[["MarketParticipant", "Source", "Sink", "Category", "FTRID", "Round", "HedgeType", "Type", "Class"]].astype(pandas.core.arrays.string_.StringDtype())
                df[["StartDate", "EndDate"]] = df[["StartDate", "EndDate"]].apply(pd.to_datetime, format="%m/%d/%Y")

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)
            
            for csv_file in files_by_type["SourceSinkShadowPrices"]:
                df = pd.read_csv(
                    filepath_or_buffer=io.StringIO(csv_file["data"]),
                )

                df[["Round"]] = df[["Round"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
                df[["ShadowPrice"]] = df[["ShadowPrice"]].astype(numpy.dtypes.Float64DType())
                df[["SourceSink", "Class"]] = df[["SourceSink", "Class"]].astype(pandas.core.arrays.string_.StringDtype())

                df_names.append(csv_file["name"].split('/')[-1].split('.')[0])
                dfs.append(df)
                
            df = pd.DataFrame(data={
                MULTI_DF_NAMES_COLUMN: df_names, 
                MULTI_DF_DFS_COLUMN: dfs,
            })
            
            return df

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
            text = res.text
            csv1, csv2 = text.split("\n\n\n")

            csv1_lines = csv1.splitlines()
            
            df1 = pd.read_csv(
                filepath_or_buffer=io.StringIO("\n".join(csv1_lines[4:])),
            )

            df1.rename(columns={
                    "Unnamed: 0": "Label",
                    " HE 1": "HE 1",
                }, 
                inplace=True,
            )
            df1.drop(columns=["Unnamed: 1"], inplace=True)

            df1[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df1[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df1[["Label", "MCP Type"]] = df1[["Label", "MCP Type"]].astype(pandas.core.arrays.string_.StringDtype())

            csv2_lines = csv2.splitlines()

            df2 = pd.read_csv(
                filepath_or_buffer=io.StringIO("\n".join(csv2_lines)),
            )

            df2.rename(columns={
                    " HE 1": "HE 1",
                }, 
                inplace=True,
            )

            df2[["Zone"]] = df2[["Zone"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
            df2[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df2[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df2[["Pnode", "MCP Type"]] = df2[["Pnode", "MCP Type"]].astype(pandas.core.arrays.string_.StringDtype())
            
            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                       "Table 1",
                       "Table 2",
                ], 
                MULTI_DF_DFS_COLUMN: [
                        df1, 
                        df2,
                ],
            })
            
            return df
        
        @staticmethod
        def parse_asm_rtmcp_final(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            _, _, csv1, csv2 = text.split("\r\n\r\n")

            csv1_lines = csv1.splitlines()
            
            df1 = pd.read_csv(
                filepath_or_buffer=io.StringIO("\n".join(csv1_lines)),
            )

            df1.rename(columns={"Unnamed: 0": "Label"}, inplace=True)
            df1.drop(columns=["Unnamed: 1"], inplace=True)

            df1[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df1[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df1[["Label", "MCP Type"]] = df1[["Label", "MCP Type"]].astype(pandas.core.arrays.string_.StringDtype())

            csv2_lines = csv2.splitlines()

            df2 = pd.read_csv(
                filepath_or_buffer=io.StringIO("\n".join(csv2_lines)),
            )

            df2.rename(columns={
                    " HE 1": "HE 1",
                    " Zone": "Zone",
                    " MCP Type": "MCP Type",
                }, 
                inplace=True,
            )

            df2[["Zone"]] = df2[["Zone"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
            df2[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df2[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df2[["Pnode", "MCP Type"]] = df2[["Pnode", "MCP Type"]].astype(pandas.core.arrays.string_.StringDtype())
            
            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                       "Table 1",
                       "Table 2",
                ], 
                MULTI_DF_DFS_COLUMN: [
                        df1, 
                        df2,
                ],
            })
            
            return df
        
        @staticmethod
        def parse_asm_rtmcp_prelim(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            _, _, csv1, csv2 = text.split("\r\n\r\n")

            csv1_lines = csv1.splitlines()
            
            df1 = pd.read_csv(
                filepath_or_buffer=io.StringIO("\n".join(csv1_lines)),
            )

            df1.rename(columns={"Unnamed: 0": "Label"}, inplace=True)
            df1.drop(columns=["Unnamed: 1"], inplace=True)

            df1[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df1[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df1[["Label", "MCP Type"]] = df1[["Label", "MCP Type"]].astype(pandas.core.arrays.string_.StringDtype())

            csv2_lines = csv2.splitlines()

            df2 = pd.read_csv(
                filepath_or_buffer=io.StringIO("\n".join(csv2_lines)),
            )

            df2.rename(columns={
                    " HE 1": "HE 1",
                    " Zone": "Zone",
                    " MCP Type": "MCP Type",
                }, 
                inplace=True,
            )

            df2[["Zone"]] = df2[["Zone"]].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
            df2[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df2[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype(numpy.dtypes.Float64DType())
            df2[["Pnode", "MCP Type"]] = df2[["Pnode", "MCP Type"]].astype(pandas.core.arrays.string_.StringDtype())
            
            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                       "Table 1",
                       "Table 2",
                ], 
                MULTI_DF_DFS_COLUMN: [
                        df1, 
                        df2,
                ],
            })
            
            return df
        
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
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=5,
            ).iloc[:-1]
             
            df.columns = pd.Index([
                "Hour Ending",
            ] + [
                f"Reserve Zone {zone_num} - {direction}" 
                for zone_num in range(1, 9) 
                for direction in ["DA MCP Ramp Up Ex-Ante 1 Hour", "DA MCP Ramp Down Ex-Ante 1 Hour"]
            ])
            
            df[["Reserve Zone 1 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Ante 1 Hour"]] = df[["Reserve Zone 1 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Ante 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Ante 1 Hour"]].astype(numpy.dtypes.Float64DType())
            df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

            return df
        
        @staticmethod
        def parse_da_exante_str_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=7,
            ).iloc[:-1]
             
            df = df.rename(columns={idx: f"Reserve Zone {idx}" for idx in range(1, 9)})

            df[["Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8"]] = df[["Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8"]].astype(numpy.dtypes.Float64DType())
            df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

            return df
        
        @staticmethod
        def parse_da_expost_ramp_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=5,
            ).iloc[:-1]
             
            df.columns = pd.Index([
                "Hour Ending",
            ] + [
                f"Reserve Zone {zone_num} - {direction}" 
                for zone_num in range(1, 9) 
                for direction in ["DA MCP Ramp Up Ex-Post 1 Hour", "DA MCP Ramp Down Ex-Post 1 Hour"]
            ])

            df[["Reserve Zone 1 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Post 1 Hour"]] = df[["Reserve Zone 1 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 1 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 2 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 3 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 4 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 5 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 6 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 7 - DA MCP Ramp Down Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Up Ex-Post 1 Hour", "Reserve Zone 8 - DA MCP Ramp Down Ex-Post 1 Hour"]].astype(numpy.dtypes.Float64DType())
            df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

            return df
        
        @staticmethod
        def parse_da_expost_str_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=5,
            ).iloc[:-1]
             
            df = df.rename(columns={idx: f"Reserve Zone {idx}" for idx in range(1, 9)})

            df[["Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8"]] = df[["Reserve Zone 1", "Reserve Zone 2", "Reserve Zone 3", "Reserve Zone 4", "Reserve Zone 5", "Reserve Zone 6", "Reserve Zone 7", "Reserve Zone 8"]].astype(numpy.dtypes.Float64DType())
            df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

            return df
        
        @staticmethod
        def parse_rt_expost_ramp_5min_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=6,
            ).iloc[:-1]
             
            df.columns = pd.Index([
                "Time (EST)", 
                "Preliminary / Final"
            ] + [
                f"Reserve Zone {zone_num} - {direction}" 
                for zone_num in range(1, 9) 
                for direction in ["RT MCP Ramp Up Ex-Post 5 Min", "RT MCP Ramp Down Ex-Post 5 Min"]
            ])

            df[["Reserve Zone 1 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post 5 Min"]] = df[["Reserve Zone 1 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post 5 Min", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post 5 Min"]].astype(numpy.dtypes.Float64DType())
            df[["Time (EST)"]] = df[["Time (EST)"]].apply(pd.to_datetime, format="%m/%d/%Y  %I:%M:%S %p")
            df[["Preliminary / Final"]] = df[["Preliminary / Final"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_rt_expost_ramp_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=5,
            ).iloc[:-1]
             
            df.columns = pd.Index([
                "Market Date", 
                "Hour Ending", 
                "Preliminary / Final"
            ] + [
                f"Reserve Zone {zone_num} - {direction}" 
                for zone_num in range(1, 9) 
                for direction in ["RT MCP Ramp Up Ex-Post Hourly", "RT MCP Ramp Down Ex-Post Hourly"]
            ])

            df[["Reserve Zone 1 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post Hourly"]] = df[["Reserve Zone 1 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 1 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 2 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 3 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 4 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 5 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 6 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 7 - RT MCP Ramp Down Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Up Ex-Post Hourly", "Reserve Zone 8 - RT MCP Ramp Down Ex-Post Hourly"]].astype(numpy.dtypes.Float64DType())
            df[["Market Date"]] = df[["Market Date"]].apply(pd.to_datetime, format="%Y-%m-%d")
            df[["Preliminary / Final"]] = df[["Preliminary / Final"]].astype(pandas.core.arrays.string_.StringDtype())
            df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())

            return df
        
        @staticmethod
        def parse_rt_expost_str_5min_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
            ).iloc[:-1]
             
            df = df.rename(columns={idx: f"RESERVE ZONE {idx}" for idx in range(1, 9)})
            df = df.drop(columns=["Unnamed: 0"])

            df[["RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8"]] = df[["RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8"]].astype(numpy.dtypes.Float64DType())
            df[["Time(EST)"]] = df[["Time(EST)"]].apply(pd.to_datetime, format="%m/%d/%Y  %I:%M:%S %p")
            df[["Preliminary/ Final"]] = df[["Preliminary/ Final"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_rt_expost_str_mcp(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=5,
            ).iloc[:-1]
             
            df = df.rename(columns={idx: f"RESERVE ZONE {idx}" for idx in range(1, 9)})

            df[["Hour Ending", "RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8"]] = df[["Hour Ending", "RESERVE ZONE 1", "RESERVE ZONE 2", "RESERVE ZONE 3", "RESERVE ZONE 4", "RESERVE ZONE 5", "RESERVE ZONE 6", "RESERVE ZONE 7", "RESERVE ZONE 8"]].astype(numpy.dtypes.Float64DType())
            df[["MARKET DATE"]] = df[["MARKET DATE"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["Preliminary/ Final"]] = df[["Preliminary/ Final"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_Allocation_on_MISO_Flowgates(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[:-2])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                thousands=",",
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
                thousands=",",
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
            with pdfplumber.open(io.BytesIO(res.content)) as pdf:
                pg = pdf.pages[0]

                bounding_box = (0, pg.height / 8, pg.width, (pg.height * 3) / 4)
                pg = pg.crop(bounding_box, relative=True)

                tables = pg.extract_tables(table_settings={
                    "vertical_strategy": "explicit",
                    "horizontal_strategy": "text",
                    "snap_tolerance": 4,
                    "explicit_vertical_lines": [18.9, 299.71666666666664, 355.80000000000007, 411.80000000000007, 467.80000000000007, 523.8000000000001, 579.8000000000001, 635.8000000000001, 691.8000000000001, 747.8000000000001, 803.8000000000001, 859.8000000000001, 915.8000000000001, 973.7833333333333],
                    "intersection_x_tolerance": 10,
                })
            
            if not tables:
                raise ValueError("Unexpected: no tables file found in PDF.")

            try:
                divider = tables[0].index(["" for i in range(13)])
            except ValueError:
                raise ValueError("Unexpected: no table delimiter found in PDF.")
            
            tables = [tables[0][:divider], tables[0][divider + 1:]]

            df_names = []
            dfs = []

            for table in tables:
                df = pd.DataFrame(
                    data=table[1:], 
                    columns=table[0],
                )
                
                year = df.columns[-1].split()[-1]

                df[["Cost Paid by Load (Hourly Avg per Month)"]] = df[["Cost Paid by Load (Hourly Avg per Month)"]].astype(pandas.core.arrays.string_.StringDtype())
                df[[f"Jan {year}", f"Feb {year}", f"Mar {year}", f"Apr {year}", f"May {year}", f"Jun {year}", f"Jul {year}", f"Aug {year}", f"Sep {year}", f"Oct {year}", f"Nov {year}", f"Dec {year}"]] = df[[f"Jan {year}", f"Feb {year}", f"Mar {year}", f"Apr {year}", f"May {year}", f"Jun {year}", f"Jul {year}", f"Aug {year}", f"Sep {year}", f"Oct {year}", f"Nov {year}", f"Dec {year}"]].replace(r'[\$,()]', '', regex=True).replace(r'^\s*$', np.nan, regex=True).astype(numpy.dtypes.Float64DType())

                dfs.append(df)
                df_names.append(f"Cost Paid by Load - {year}")


            df = pd.DataFrame(data={
                MULTI_DF_NAMES_COLUMN: df_names, 
                MULTI_DF_DFS_COLUMN: dfs,
            })
            
            return df

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
                low_memory=False,
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

        @staticmethod
        def parse_RT_LMPs(
            res: requests.Response,
        ) -> pd.DataFrame:
            with zipfile.ZipFile(file=io.BytesIO(res.content)) as z:
                text = z.read(z.namelist()[0]).decode("utf-8")

            csv_data = "\n".join(text.splitlines()[1:])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                thousands=",",
            )

            df[["MARKET_DAY"]] = df[["MARKET_DAY"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(numpy.dtypes.Float64DType())
            df[["NODE", "TYPE", "VALUE"]] = df[["NODE", "TYPE", "VALUE"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_sr_gfm(
            res: requests.Response,
        ) -> pd.DataFrame:
            MarketHourColumn = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                usecols="A",
            )[:-1]

            MarketHourColumn["Market Hour Ending"] = MarketHourColumn["Market Hour Ending"].astype(pandas.core.arrays.string_.StringDtype())

            df1 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                usecols="B:J",
                sheet_name="RT Generation Fuel Mix",
            )[:-1]
            shared_column_names = list(df1.columns)[:-2]

            df1[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]] = df1[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]].astype(numpy.dtypes.Float64DType())
            
            df2 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                usecols="L:T",
                sheet_name="RT Generation Fuel Mix",
                names=shared_column_names + ["Storage", "Total MW"],
            )[:-1]

            df2[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]] = df2[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]].astype(numpy.dtypes.Float64DType())

            df3 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                usecols="V:AC",
                sheet_name="RT Generation Fuel Mix",
                names=shared_column_names + ["Total MW"],
            )[:-1]

            df3[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW"]] = df3[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW"]].astype(numpy.dtypes.Float64DType())

            df4 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                usecols="AG:AO",
                sheet_name="RT Generation Fuel Mix",
                names=shared_column_names + ["Storage", "MISO"],
            )[:-1]

            df4[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO"]] = df4[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO"]].astype(numpy.dtypes.Float64DType())

            df5 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                sheet_name="DA Cleared Generation Fuel Mix",
                names=shared_column_names + ["Storage", "Total MW"],
            )[:-1]

            df5[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]] = df5[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]].astype(numpy.dtypes.Float64DType())

            df6 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                sheet_name="DA Cleared Generation Fuel Mix",
                names=shared_column_names + ["Storage", "Total MW"],
            )[:-1]

            df6[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]] = df6[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "Total MW"]].astype(numpy.dtypes.Float64DType())

            df7 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                sheet_name="DA Cleared Generation Fuel Mix",
                names=shared_column_names + ["Total MW"],
            )[:-1]

            df7[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW"]] = df7[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Total MW"]].astype(numpy.dtypes.Float64DType())

            df8 = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                sheet_name="DA Cleared Generation Fuel Mix",
                names=shared_column_names + ["Storage", "MISO"],
            )[:-1]

            df8[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO"]] = df8[["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other", "Storage", "MISO"]].astype(numpy.dtypes.Float64DType())


            df_list = [df1, df2, df3, df4, df5, df6, df7, df8]

            for df in df_list:
                df.insert(
                    loc=0,
                    column="Market Hour Ending",
                    value=MarketHourColumn["Market Hour Ending"],
                )

            df = pd.DataFrame({
                MULTI_DF_NAMES_COLUMN: [
                       "RT Generation Fuel Mix Central",
                       "RT Generation Fuel Mix North",
                       "RT Generation Fuel Mix South",
                       "RT Generation Fuel Mix Totals",
                       "DA Cleared Generation Fuel Mix Central",
                       "DA Cleared Generation Fuel Mix North",
                       "DA Cleared Generation Fuel Mix South",
                       "DA Cleared Generation Fuel Mix Totals",
                ], 
                MULTI_DF_DFS_COLUMN: [
                        df1, 
                        df2,
                        df3,
                        df4,
                        df5,
                        df6,
                        df7,
                        df8,
                ],
            })

            return df

        @staticmethod
        def parse_dfal_HIST(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=5,
            )[:-2]

            df = df[df["MarketDay"] != "MarketDay"]
            df = df.reset_index(drop=True)
            df[["HourEnding"]] = df[["HourEnding"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["MarketDay"]] = df[["MarketDay"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["MTLF (MWh)", "ActualLoad (MWh)"]] = df[["MTLF (MWh)", "ActualLoad (MWh)"]].astype(numpy.dtypes.Float64DType())
            df[["LoadResource Zone"]] = df[["LoadResource Zone"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_historical_gen_fuel_mix(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                usecols="B:G",
            )

            df[["HourEnding"]] = df[["HourEnding"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Market Date"]] = df[["Market Date"]].apply(pd.to_datetime, format="%Y-%m-%d")
            df[["DA Cleared UDS Generation", "[RT Generation State Estimator"]] = df[["DA Cleared UDS Generation", "[RT Generation State Estimator"]].astype(numpy.dtypes.Float64DType())
            df[["Region", "Fuel Type"]] = df[["Region", "Fuel Type"]].astype(pandas.core.arrays.string_.StringDtype())
            
            return df
        
        @staticmethod
        def parse_hwd_HIST(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[7:-1])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["Hour Ending"]] = df[["Hour Ending"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Market Day	"]] = df[["Market Day	"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["MWh"]] = df[["MWh"]].astype(numpy.dtypes.Float64DType())

            return df
        
        @staticmethod
        def parse_sr_hist_is(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[1:-2])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
                sep="|",
            )

            df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["MKTDAY"]] = df[["MKTDAY"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["INTERFACE"]] = df[["INTERFACE"]].astype(pandas.core.arrays.string_.StringDtype())

            return df

        @staticmethod
        def parse_rfal_HIST(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=4,
                usecols="B:G",
            )[:-4]

            df[["HourEnding"]] = df[["HourEnding"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Market Day"]] = df[["Market Day"]].apply(pd.to_datetime, format="%m/%d/%Y")
            df[["MTLF (MWh)", "Actual Load (MWh)"]] = df[["MTLF (MWh)", "Actual Load (MWh)"]].astype(numpy.dtypes.Float64DType())
            df[["Region", "Footnote"]] = df[["Region", "Footnote"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_sr_lt(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=3,
            )

            df[["Minimum (GW)", "Average (GW)", "Maximum (GW)"]] = df[["Minimum (GW)", "Average (GW)", "Maximum (GW)"]].astype(numpy.dtypes.Float64DType())
            df[["Week Starting"]] = df[["Week Starting"]].apply(pd.to_datetime)
            
            return df
        
        @staticmethod
        def parse_sr_la_rg(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[3:-1])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df = df.dropna()
            df = df.reset_index(drop=True)
            df[["10/24/2024 Thursday Peak Hour: HE  19 MTLF (GW)", "10/24/2024 Thursday Peak Hour: HE  19 Capacity on Outage (GW)", "10/25/2024 Friday   Peak Hour: HE  16 MTLF (GW)", "10/25/2024 Friday   Peak Hour: HE  16 Capacity on Outage (GW)", "10/26/2024 Saturday Peak Hour: HE  19 MTLF (GW)", "10/26/2024 Saturday Peak Hour: HE  19 Capacity on Outage (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 MTLF (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 Capacity on Outage (GW)", "10/28/2024 Monday   Peak Hour: HE  19 MTLF (GW)", "10/28/2024 Monday   Peak Hour: HE  19Capacity on Outage (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 MTLF (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 Capacity on Outage (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 MTLF (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 Capacity on Outage (GW)"]] = df[["10/24/2024 Thursday Peak Hour: HE  19 MTLF (GW)", "10/24/2024 Thursday Peak Hour: HE  19 Capacity on Outage (GW)", "10/25/2024 Friday   Peak Hour: HE  16 MTLF (GW)", "10/25/2024 Friday   Peak Hour: HE  16 Capacity on Outage (GW)", "10/26/2024 Saturday Peak Hour: HE  19 MTLF (GW)", "10/26/2024 Saturday Peak Hour: HE  19 Capacity on Outage (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 MTLF (GW)", "10/27/2024 Sunday   Peak Hour: HE  19 Capacity on Outage (GW)", "10/28/2024 Monday   Peak Hour: HE  19 MTLF (GW)", "10/28/2024 Monday   Peak Hour: HE  19Capacity on Outage (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 MTLF (GW)", "10/29/2024 Tuesday  Peak Hour: HE  19 Capacity on Outage (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 MTLF (GW)", "10/30/2024 WednesdayPeak Hour: HE  24 Capacity on Outage (GW)"]].astype(numpy.dtypes.Float64DType())
            df[["Hourend_EST", "Region"]] = df[["Hourend_EST", "Region"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_mom(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Parsing of this report is not yet implemented. **WARNING** PROCEED WITH CAUTION")

        @staticmethod
        def parse_sr_nd_is(
            res: requests.Response,
        ) -> pd.DataFrame:
            df = pd.read_excel(
                io=io.BytesIO(res.content),
                skiprows=10,
                usecols="B:R"
            )[:-11]
            
            df.rename(
                columns={
                    "Unnamed: 1": "Hour",
                }, 
                inplace=True,
            )

            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df["Hour"] = df["Hour"].replace('[^\\d]+', '', regex=True).astype(pandas.core.arrays.integer.Int64Dtype())
            df[["GLHB", "IESO", "MHEB", "PJM", "SOCO", "SWPP", "TVA", "AECI", "LGEE", "Other", "Total"]] = df[["GLHB", "IESO", "MHEB", "PJM", "SOCO", "SWPP", "TVA", "AECI", "LGEE", "Other", "Total"]].astype(pandas.core.arrays.integer.Int64Dtype())

            return df

        @staticmethod
        def parse_PeakHourOverview(
            res: requests.Response,
        ) -> pd.DataFrame:
            raise NotImplementedError("Parsing of this report is not yet implemented.")
        
        @staticmethod
        def parse_sr_tcdc_group2(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
            csv_data = "\n".join(text.splitlines()[4:-2])

            df = pd.read_csv(
                filepath_or_buffer=io.StringIO(csv_data),
            )

            df[["EffectiveTime", "TerminationTime"]] = df[["EffectiveTime", "TerminationTime"]].apply(pd.to_datetime, format="%m/%d/%Y %H:%M:%S")
            df[["BP1", "PC1", "BP2", "PC2"]] = df[["BP1", "PC1", "BP2", "PC2"]].astype(numpy.dtypes.Float64DType())
            df[["ContingencyName", "ContingencyDescription", "BranchName", "CurveName", "Reason"]] = df[["ContingencyName", "ContingencyDescription", "BranchName", "CurveName", "Reason"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_MISOdaily(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text
                        
            element_tree = ET.fromstring(text)
            product = element_tree.find("Product")
            account_header = product.find("AccountHeader") # type: ignore
            posting_headers = account_header.findall("PostingHeader") # type: ignore

            data_elements: list[ET.Element] = []
            for posting_header in posting_headers:
                if posting_header.find("HourlyIndicatedValue") is not None:
                    data_elements.append(posting_header)
            
            data_element_columns = [tag for (tag, text) in data_elements[0].find("HourlyIndicatedValue").items()] # type: ignore
            partial_dfs = []
            for element in data_elements:
                outer_mappings = {tag: text for (tag, text) in element.items()}
                
                inner_data = {tag: [] for tag in data_element_columns} # type: ignore

                inner_elements = element.findall("HourlyIndicatedValue")
                for inner_element in inner_elements:
                    for tag, text in inner_element.items():
                        inner_data[tag].append(text)

                partial_df = pd.DataFrame(inner_data)
                for key, value in outer_mappings.items():
                    if key in partial_df.columns:
                        raise ValueError(f"Key {key} already exists in the DataFrame.")
                    
                    partial_df[key] = value
                
                partial_dfs.append(partial_df)

            df = pd.concat(partial_dfs, ignore_index=True)

            df[["PostedValue", "Hour", "UTCOffset"]] = df[["PostedValue", "Hour", "UTCOffset"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Data_Date"]] = df[["Data_Date"]].apply(pd.to_datetime, format="%j%Y")
            df[["Data_Code", "Data_Type", "PostingType"]] = df[["Data_Code", "Data_Type", "PostingType"]].astype(pandas.core.arrays.string_.StringDtype())

            return df
        
        @staticmethod
        def parse_MISOsamedaydemand(
            res: requests.Response,
        ) -> pd.DataFrame:
            text = res.text

            element_tree = ET.fromstring(text)
            product = element_tree.find("Product")
            account_header = product.find("AccountHeader") # type: ignore
            posting_headers = account_header.findall("PostingHeader") # type: ignore

            data_elements: list[ET.Element] = []
            for posting_header in posting_headers:
                if posting_header.find("HourlyIndicatedValue") is not None:
                    data_elements.append(posting_header)
            
            data_element_columns = [tag for (tag, text) in data_elements[0].find("HourlyIndicatedValue").items()] # type: ignore
            partial_dfs = []
            for element in data_elements:
                outer_mappings = {tag: text for (tag, text) in element.items()}
                
                inner_data = {tag: [] for tag in data_element_columns} # type: ignore

                inner_elements = element.findall("HourlyIndicatedValue")
                for inner_element in inner_elements:
                    for tag, text in inner_element.items():
                        inner_data[tag].append(text)

                partial_df = pd.DataFrame(inner_data)
                for key, value in outer_mappings.items():
                    if key in partial_df.columns:
                        raise ValueError(f"Key {key} already exists in the DataFrame.")
                    
                    partial_df[key] = value
                
                partial_dfs.append(partial_df)

            df = pd.concat(partial_dfs, ignore_index=True)

            df[["PostedValue", "Hour", "UTCOffset"]] = df[["PostedValue", "Hour", "UTCOffset"]].astype(pandas.core.arrays.integer.Int64Dtype())
            df[["Data_Date"]] = df[["Data_Date"]].apply(pd.to_datetime, format="%j%Y")
            df[["Data_Code", "Data_Type", "PostingType"]] = df[["Data_Code", "Data_Type", "PostingType"]].astype(pandas.core.arrays.string_.StringDtype())

            return df


    report_mappings: dict[str, Report] = {
        "rt_bc_HIST": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_bc_HIST",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_bc_HIST,
            example_url="https://docs.misoenergy.org/marketreports/2024_rt_bc_HIST.csv",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "RT_UDS_Approved_Case_Percentage": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="RT_UDS_Approved_Case_Percentage",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_RT_UDS_Approved_Case_Percentage,
            example_url="https://docs.misoenergy.org/marketreports/20241023_RT_UDS_Approved_Case_Percentage.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=23),
        ),

        "Resource_Uplift_by_Commitment_Reason": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="Resource_Uplift_by_Commitment_Reason",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_Resource_Uplift_by_Commitment_Reason,
            example_url="https://docs.misoenergy.org/marketreports/20241009_Resource_Uplift_by_Commitment_Reason.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=9),
        ),

        "rt_rpe": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_rpe",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_rpe,
            example_url="https://docs.misoenergy.org/marketreports/20241101_rt_rpe.xls",
            example_datetime=datetime.datetime(year=2024, month=11, day=1),
        ),

        "Historical_RT_RSG_Commitment": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="Historical_RT_RSG_Commitment",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_Historical_RT_RSG_Commitment,
            example_url="https://docs.misoenergy.org/marketreports/2024_Historical_RT_RSG_Commitment.csv",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "da_pr": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_pr",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_da_pr,
            example_url="https://docs.misoenergy.org/marketreports/20241030_da_pr.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "da_pbc": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_pbc",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_pbc,
            example_url="https://docs.misoenergy.org/marketreports/20220107_da_pbc.csv",
            example_datetime=datetime.datetime(year=2022, month=1, day=7),
        ),

        "da_bc": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_bc",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_da_bc,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_bc.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "da_bcsf": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_bcsf",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_da_bcsf,
            example_url="https://docs.misoenergy.org/marketreports/20241029_da_bcsf.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "rt_pr": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_pr",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_pr,
            example_url="https://docs.misoenergy.org/marketreports/20241026_rt_pr.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=26),
        ),

        "rt_irsf": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_irsf",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_irsf,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_irsf.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_mf": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_mf",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_rt_mf,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_mf.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_ex": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_ex",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_ex,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_ex.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_pbc": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_pbc",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_pbc,
            example_url="https://docs.misoenergy.org/marketreports/20241001_rt_pbc.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=1),
        ),

        "rt_bc": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_bc",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_bc,
            example_url="https://docs.misoenergy.org/marketreports/20241030_rt_bc.xls",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "rt_or": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_or",
                supported_extensions=["xls"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xls",
            ),
            type_to_parse="xls",
            parser=ReportParsers.parse_rt_or,
            example_url="https://docs.misoenergy.org/marketreports/20240910_rt_or.xls",
            example_datetime=datetime.datetime(year=2024, month=9, day=10),
        ),

        "rt_fuel_on_margin": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_fuel_on_margin",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_rt_fuel_on_margin,
            example_url="https://docs.misoenergy.org/marketreports/2023_rt_fuel_on_margin.zip",
            example_datetime=datetime.datetime(year=2023, month=1, day=1),
        ),

        "Total_Uplift_by_Resource": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="Total_Uplift_by_Resource",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_Total_Uplift_by_Resource,
            example_url="https://docs.misoenergy.org/marketreports/20241001_Total_Uplift_by_Resource.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=1),
        ),

        "ms_vlr_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_vlr_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_vlr_srw,
            example_url="https://docs.misoenergy.org/marketreports/20240901_ms_vlr_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=9, day=1),
        ),

        "ms_rsg_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_rsg_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_rsg_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241104_ms_rsg_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=11, day=4),
        ),

        "ms_rnu_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_rnu_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_rnu_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241029_ms_rnu_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "ms_ri_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_ri_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_ri_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241029_ms_ri_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=29),
        ),

        "MARKET_SETTLEMENT_DATA_SRW": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="MARKET_SETTLEMENT_DATA_SRW",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_no_date,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_MARKET_SETTLEMENT_DATA_SRW,
            example_url="https://docs.misoenergy.org/marketreports/MARKET_SETTLEMENT_DATA_SRW.zip",
        ),

        "ms_vlr_HIST_SRW": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_vlr_HIST_SRW",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_vlr_HIST_SRW,
            example_url="https://docs.misoenergy.org/marketreports/2024_ms_vlr_HIST_SRW.xlsx",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "ms_ecf_srw": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_ecf_srw",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_ms_ecf_srw,
            example_url="https://docs.misoenergy.org/marketreports/20241107_ms_ecf_srw.xlsx",
            example_datetime=datetime.datetime(year=2024, month=11, day=7),
        ),


        "ccf_co": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ccf_co",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_ccf_co,
            example_url="https://docs.misoenergy.org/marketreports/20241020_ccf_co.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=20),
        ),

        "ms_vlr_HIST": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ms_vlr_HIST",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,\
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_ms_vlr_HIST,
            example_url="https://docs.misoenergy.org/marketreports/2022_ms_vlr_HIST.csv",
            example_datetime=datetime.datetime(year=2022, month=1, day=1),
        ),

        "Daily_Uplift_by_Local_Resource_Zone": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="Daily_Uplift_by_Local_Resource_Zone",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_Daily_Uplift_by_Local_Resource_Zone,
            example_url="https://docs.misoenergy.org/marketreports/20241020_Daily_Uplift_by_Local_Resource_Zone.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=20),
        ),

        "fuelmix": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getfuelmix",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_fuelmix,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getfuelmix&returnType=csv",
        ),

        "ace": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getace",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_ace,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getace&returnType=csv",
        ),

        "AncillaryServicesMCP": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getAncillaryServicesMCP",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_AncillaryServicesMCP,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getAncillaryServicesMCP&returnType=csv",
        ),

        "cts": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getcts",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_cts,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcts&returnType=csv",
        ),

        "combinedwindsolar": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getcombinedwindsolar",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_combinedwindsolar,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcombinedwindsolar&returnType=csv",
        ),

        "WindForecast": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWindForecast",
                supported_extensions=["xml", "json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_WindForecast,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindForecast&returnType=json",
        ),

        "Wind": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWind",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_Wind,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWind&returnType=csv",
        ),

        "SolarForecast": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolarForecast",
                supported_extensions=["xml", "json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_SolarForecast,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarForecast&returnType=json",
        ),

        "Solar": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolar",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_Solar,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolar&returnType=csv",
        ),

        "exantelmp": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getexantelmp",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
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
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_exante_lmp,
            example_url="https://docs.misoenergy.org/marketreports/20241026_da_exante_lmp.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=26),
        ),

        "da_expost_lmp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="da_expost_lmp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_da_expost_lmp,
            example_url="https://docs.misoenergy.org/marketreports/20241026_da_expost_lmp.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=26),
        ),

        "rt_lmp_final": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_lmp_final",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_lmp_final,
            example_url="https://docs.misoenergy.org/marketreports/20241021_rt_lmp_final.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=21),
        ),

        "rt_lmp_prelim": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="rt_lmp_prelim",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_rt_lmp_prelim,
            example_url="https://docs.misoenergy.org/marketreports/20241103_rt_lmp_prelim.csv",
            example_datetime=datetime.datetime(year=2024, month=11, day=3),
        ),

        "DA_Load_EPNodes": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="DA_Load_EPNodes",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_last,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_DA_Load_EPNodes,
            example_url="https://docs.misoenergy.org/marketreports/DA_Load_EPNodes_20241021.zip",
            example_datetime=datetime.datetime(year=2024, month=10, day=21),
        ),

        "DA_LMPs": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="DA_LMPs",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_current_month_name_to_two_months_later_name_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_DA_LMPs,
            example_url="https://docs.misoenergy.org/marketreports/2024-Jul-Sep_DA_LMPs.zip",
            example_datetime=datetime.datetime(year=2024, month=7, day=1),
        ),

        "5min_exante_lmp": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="5min_exante_lmp",
                supported_extensions=["xlsx"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="xlsx",
            ),
            type_to_parse="xlsx",
            parser=ReportParsers.parse_5min_exante_lmp,
            example_url="https://docs.misoenergy.org/marketreports/20241025_5min_exante_lmp.xlsx",
            example_datetime=datetime.datetime(year=2024, month=10, day=25),
        ),

        "nsi1": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi1",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi1,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1&returnType=csv",
        ),

        "nsi5": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi5",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi5,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5&returnType=csv",
        ),

        "nsi1miso": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi1miso",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi1miso,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1miso&returnType=csv",
        ),

        "nsi5miso": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getnsi5miso",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_nsi5miso,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5miso&returnType=csv",
        ),

        "importtotal5": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getimporttotal5",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_importtotal5,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getimporttotal5&returnType=json",
        ),

        "reservebindingconstraints": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getreservebindingconstraints",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_reservebindingconstraints,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getreservebindingconstraints&returnType=csv",
        ),

        "RSG": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getRSG",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_RSG,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getRSG&returnType=csv",
        ),

        "totalload": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="gettotalload",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_totalload,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=gettotalload&returnType=csv",
        ),

        "WindActual": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getWindActual",
                supported_extensions=["xml", "json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_WindActual,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindActual&returnType=json",
        ),

        "SolarActual": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getSolarActual",
                supported_extensions=["xml", "json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_SolarActual,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarActual&returnType=json",
        ),

        "NAI": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getNAI",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_NAI,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getNAI&returnType=csv",
        ),

        "regionaldirectionaltransfer": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getregionaldirectionaltransfer",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_regionaldirectionaltransfer,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getregionaldirectionaltransfer&returnType=csv",
        ),

        "generationoutagesplusminusfivedays": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getgenerationoutagesplusminusfivedays",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_generationoutagesplusminusfivedays,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getgenerationoutagesplusminusfivedays&returnType=csv",
        ),

        "apiversion": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getapiversion",
                supported_extensions=["json"],
                default_extension="json",
            ),
            type_to_parse="json",
            parser=ReportParsers.parse_apiversion,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getapiversion&returnType=json",
        ),

        "lmpconsolidatedtable": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getlmpconsolidatedtable",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_lmpconsolidatedtable,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getlmpconsolidatedtable&returnType=csv",
        ),

        "realtimebindingconstraints": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getrealtimebindingconstraints",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_realtimebindingconstraints,
            example_url="https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getrealtimebindingconstraints&returnType=csv",
        ),

        "realtimebindingsrpbconstraints": Report(
            url_builder=MISORTWDDataBrokerURLBuilder(
                target="getrealtimebindingsrpbconstraints",
                supported_extensions=["csv", "xml", "json"],
                default_extension="csv",
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
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_RT_Load_EPNodes,
            example_url="https://docs.misoenergy.org/marketreports/RT_Load_EPNodes_20241018.zip",
            example_datetime=datetime.datetime(year=2024, month=10, day=18),
        ),

        "5MIN_LMP": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="5MIN_LMP",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_5MIN_LMP,
            example_url="https://docs.misoenergy.org/marketreports/20241021_5MIN_LMP.zip",
            example_datetime=datetime.datetime(year=2024, month=10, day=21),
        ),

        "bids_cb": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="bids_cb",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_bids_cb,
            example_url="https://docs.misoenergy.org/marketreports/20240801_bids_cb.zip",
            example_datetime=datetime.datetime(year=2024, month=8, day=1),
        ),
        
        "asm_exante_damcp": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="asm_exante_damcp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_asm_exante_damcp,
            example_url="https://docs.misoenergy.org/marketreports/20241030_asm_exante_damcp.csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),

        "ftr_allocation_restoration": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_restoration",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_allocation_restoration,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_restoration.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_allocation_stage_1A": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_stage_1A",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_allocation_stage_1A,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1A.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_allocation_stage_1B": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_stage_1B",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_allocation_stage_1B,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1B.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_allocation_summary": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_allocation_summary",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_allocation_summary,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_summary.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_annual_results_round_1": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_results_round_1",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_annual_results_round_1,
            example_url="https://docs.misoenergy.org/marketreports/20240401_ftr_annual_results_round_1.zip",
            example_datetime=datetime.datetime(year=2024, month=4, day=1),
        ),

        "ftr_annual_results_round_2": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_results_round_2",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_annual_results_round_2,
            example_url="https://docs.misoenergy.org/marketreports/20240501_ftr_annual_results_round_2.zip",
            example_datetime=datetime.datetime(year=2024, month=5, day=1),
        ),

        "ftr_annual_results_round_3": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_results_round_3",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_annual_results_round_3,
            example_url="https://docs.misoenergy.org/marketreports/20240101_ftr_annual_results_round_3.zip",
            example_datetime=datetime.datetime(year=2024, month=1, day=1),
        ),

        "ftr_annual_bids_offers": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_annual_bids_offers",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYY_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_annual_bids_offers,
            example_url="https://docs.misoenergy.org/marketreports/2023_ftr_annual_bids_offers.zip",
            example_datetime=datetime.datetime(year=2023, month=1, day=1),
        ),

        "ftr_mpma_results": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_mpma_results",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_mpma_results,
            example_url="https://docs.misoenergy.org/marketreports/20241101_ftr_mpma_results.zip",
            example_datetime=datetime.datetime(year=2024, month=11, day=1),
        ),

        "ftr_mpma_bids_offers": Report(
            url_builder=MISOMarketReportsURLBuilder(
                target="ftr_mpma_bids_offers",
                supported_extensions=["zip"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="zip",
            ),
            type_to_parse="zip",
            parser=ReportParsers.parse_ftr_mpma_bids_offers,
            example_url="https://docs.misoenergy.org/marketreports/20240801_ftr_mpma_bids_offers.zip",
            example_datetime=datetime.datetime(year=2024, month=8, day=1),
        ),

        "asm_expost_damcp": Report(
             url_builder=MISOMarketReportsURLBuilder(
                target="asm_expost_damcp",
                supported_extensions=["csv"],
                url_generator=MISOMarketReportsURLBuilder.url_generator_YYYYmmdd_first,
                default_extension="csv",
            ),
            type_to_parse="csv",
            parser=ReportParsers.parse_asm_expost_damcp,
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
            parser=ReportParsers.parse_asm_rtmcp_final,
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
            parser=ReportParsers.parse_asm_rtmcp_prelim,
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
            parser=ReportParsers.parse_5min_exante_mcp,
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
            parser=ReportParsers.parse_5min_expost_mcp,
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
            parser=ReportParsers.parse_da_exante_ramp_mcp,
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
            parser=ReportParsers.parse_da_exante_str_mcp,
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
            parser=ReportParsers.parse_da_expost_ramp_mcp,
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
            parser=ReportParsers.parse_da_expost_str_mcp,
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
            parser=ReportParsers.parse_rt_expost_ramp_5min_mcp,
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
            parser=ReportParsers.parse_rt_expost_ramp_mcp,
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
            parser=ReportParsers.parse_rt_expost_str_5min_mcp,
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
            parser=ReportParsers.parse_rt_expost_str_mcp,
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
            parser=ReportParsers.parse_Allocation_on_MISO_Flowgates,
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
            parser=ReportParsers.parse_M2M_FFE,
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
            parser=ReportParsers.parse_M2M_Flowgates_as_of,
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
            parser=ReportParsers.parse_da_M2M_Settlement_srw,
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
            parser=ReportParsers.parse_M2M_Settlement_srw,
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
            parser=ReportParsers.parse_MM_Annual_Report,
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
            parser=ReportParsers.parse_asm_da_co,
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
            parser=ReportParsers.parse_asm_rt_co,
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
            parser=ReportParsers.parse_Dead_Node_Report,
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
            parser=ReportParsers.parse_rt_co,
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
            parser=ReportParsers.parse_da_co,
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
            parser=ReportParsers.parse_cpnode_reszone,
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
            parser=ReportParsers.parse_sr_ctsl,
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
            parser=ReportParsers.parse_df_al,
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
            parser=ReportParsers.parse_rf_al,
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
            parser=ReportParsers.parse_da_bc_HIST,
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
            parser=ReportParsers.parse_da_ex_rg,
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
            parser=ReportParsers.parse_da_ex,
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
            parser=ReportParsers.parse_da_rpe,
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
            parser=ReportParsers.parse_RT_LMPs,
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
            parser=ReportParsers.parse_sr_gfm,
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
            parser=ReportParsers.parse_dfal_HIST,
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
            parser=ReportParsers.parse_historical_gen_fuel_mix,
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
            parser=ReportParsers.parse_hwd_HIST,
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
            parser=ReportParsers.parse_sr_hist_is,
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
            parser=ReportParsers.parse_rfal_HIST,
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
            parser=ReportParsers.parse_sr_lt,
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
            parser=ReportParsers.parse_sr_la_rg,
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
            parser=ReportParsers.parse_mom,
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
            parser=ReportParsers.parse_sr_nd_is,
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
            parser=ReportParsers.parse_PeakHourOverview,
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
            parser=ReportParsers.parse_sr_tcdc_group2,
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
            parser=ReportParsers.parse_MISOdaily,
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
            parser=ReportParsers.parse_MISOsamedaydemand,
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
            parser=ReportParsers.parse_currentinterval,
            example_url="https://api.misoenergy.org/MISORTWDBIReporter/Reporter.asmx?messageType=currentinterval&returnType=csv",
            example_datetime=datetime.datetime(year=2024, month=10, day=30),
        ),
    }

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

        return MISOReports._get_response_helper(url)
    
    @staticmethod
    def _get_response_helper(
        url: str,
        timeout: int | None = None,
    ) -> requests.Response:
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
        
        return df

import uuid
from abc import ABC, abstractmethod
from typing import Callable
import datetime


class URLBuilder(ABC):
    target_placeholder = str(uuid.uuid4())
    extension_placeholder = str(uuid.uuid4())

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
        self.target = target
        self.supported_extensions = supported_extensions

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
        self.target = target
        self.supported_extensions = supported_extensions

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
        self.target = target
        self.supported_extensions = supported_extensions

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
    
    def url_generator_datetime_first(
        ddatetime: datetime.datetime,
        target: str,
        datetime_format: str,
    ) -> str:
        format_string = f"https://docs.misoenergy.org/marketreports/{datetime_format}_{target}.{URLBuilder.extension_placeholder}"
        res = ddatetime.strftime(format_string)
        return res
    
    def url_generator_YYYYmmdd_first(
        ddatetime: datetime.datetime,
        target: str,
    ) -> str:
        return MISOMarketReportsURLBuilder.url_generator_datetime_first(ddatetime, target, "%Y%m%d")
    
    def url_generator_YYYYmm_first(
        ddatetime: datetime.datetime,
        target: str,
    ) -> str:
        return MISOMarketReportsURLBuilder.url_generator_datetime_first(ddatetime, target, "%Y%m")
    
    def url_generator_YYYY_current_month_name_to_two_months_later_name_first(
        ddatetime: datetime.datetime,
        target: str,
    ) -> str:
        new_month = (ddatetime.month + 2) % 12 
        two_months_later_datetime = ddatetime.replace(month=new_month)
        datetime_part = f"{ddatetime.strftime('%Y')}-{ddatetime.strftime('%b')}-{two_months_later_datetime.strftime('%b')}" 
        res = f"https://docs.misoenergy.org/marketreports/{datetime_part}_{target}.{URLBuilder.extension_placeholder}"
        return res
    
    def url_generator_YYYYmmdd_last(
        ddatetime: datetime.datetime,
        target: str,
    ) -> str:
        res = f"https://docs.misoenergy.org/marketreports/{target}_{ddatetime.strftime('%Y%m%d')}.{URLBuilder.extension_placeholder}"
        return res



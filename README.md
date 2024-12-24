# MISOReports
A comprehensive Python library for downloading Midcontinent Independent System Operator (MISO) public reports into pandas dataframes. 

As of 2024-12-22, MISOReports supports reports from 
[MISORTWDDataBroker](https://api.misoenergy.org/MISORTWDDataBroker/), [MISORTWDBIReporter](https://api.misoenergy.org/MISORTWDBIReporter/),
and [MISO Market Reports](https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/), totalling to well over 120 different reports.

With MISOReports, you can skip all of the intermediate URL generation/parsing/typing steps and get any supported report's data
as a dataframe with just a few lines of code. You can also choose to retrieve the raw data directly and use that instead. 

For documentation and information on currently supported reports, please check out [DOCUMENTATION.md](DOCUMENTATION.md).

## Features
MISOReports supports these features and more:
- Downloading reports by datetime for reports that offer a datetime option
- Downloading live reports for reports without a date option
- Downloading raw report content in any of their supported formats (csv, xml, json, xls, xlsx, etc.)
- Generating target URLs for the report of your choice

## Installation
To install and use MISOReports, in the command line, run:
```
pip install MISOReports
```

## Examples

### Example 1:
Download a single-table report with datetime option from [MISO Market Reports](https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/).

#### Code:
```python
import datetime
from MISOReports.MISOReports import MISOReports

# Downloads the data offered at
# https://docs.misoenergy.org/marketreports/20241030_da_expost_ramp_mcp.xlsx.
df = MISOReports.get_df(
    report_name="da_expost_ramp_mcp",
    ddatetime=datetime.datetime(year=2024, month=10, day=30),
)

print(df)
```

#### Output:
```
    Hour Ending  Reserve Zone 1 - DA MCP Ramp Up Ex-Post 1 Hour  ...  Reserve Zone 8 - DA MCP Ramp Up Ex-Post 1 Hour  Reserve Zone 8 - DA MCP Ramp Down Ex-Post 1 Hour
0             1                                            0.00  ...                                            0.00                                               0.0
1             2                                            0.00  ...                                            0.00                                               0.0
2             3                                            0.00  ...                                            0.00                                               0.0
3             4                                            0.00  ...                                            0.00                                               0.0
4             5                                            0.00  ...                                            0.00                                               0.0
5             6                                            0.17  ...                                            0.17                                               0.0
6             7                                            1.48  ...                                            1.48                                               0.0
7             8                                            0.00  ...                                            0.00                                               0.0
8             9                                            0.00  ...                                            0.00                                               0.0
9            10                                            0.00  ...                                            0.00                                               0.0
10           11                                            0.00  ...                                            0.00                                               0.0
11           12                                            1.08  ...                                            1.08                                               0.0
12           13                                            1.81  ...                                            1.81                                               0.0
13           14                                            2.56  ...                                            2.56                                               0.0
14           15                                            3.13  ...                                            3.13                                               0.0
15           16                                            5.00  ...                                            5.00                                               0.0
16           17                                            5.00  ...                                            5.00                                               0.0
17           18                                           12.85  ...                                           12.85                                               0.0
18           19                                            5.17  ...                                            5.17                                               0.0
19           20                                            0.00  ...                                            0.00                                               0.0
20           21                                            0.00  ...                                            0.00                                               0.0
21           22                                            0.00  ...                                            0.00                                               0.0
22           23                                            0.00  ...                                            0.00                                               0.0
23           24                                            0.00  ...                                            0.00                                               0.0

[24 rows x 17 columns]
```

### Example 2:
Download a multi-table report from [MISORTWDDataBroker](https://api.misoenergy.org/MISORTWDDataBroker/).

#### Code:
```python
from MISOReports.MISOReports import MISOReports

# Downloads the data offered at
# https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=gettotalload&returnType=csv.
df = MISOReports.get_df(
    report_name="totalload",
)

# For multi-table reports, use a for-loop
# to iterate across the tables.
for i, table_name in enumerate(df["table_names"]):
    print(table_name)
    print(df["dataframes"].iloc[i].head(3))
    print()
    print()
```

#### Output:
```
ClearedMW
   Load_Hour  Load_Value
0          1     65871.0
1          2     65521.0
2          3     64474.0


MediumTermLoadForecast
   Hour_End  Load_Forecast
0         1        68614.0
1         2        66566.0
2         3        66620.0


FiveMinTotalLoad
            Load_Time  Load_Value
0 1900-01-01 00:00:00     68899.0
1 1900-01-01 00:05:00     68690.0
2 1900-01-01 00:10:00     68327.0
```

### Example 3:
Download a multi-table report from [MISORTWDDataBroker](https://api.misoenergy.org/MISORTWDDataBroker/).

#### Code:
```python
from MISOReports.MISOReports import MISOReports

# Downloads the data offered at
# https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getlmpconsolidatedtable&returnType=csv.
df = MISOReports.get_df(
    report_name="lmpconsolidatedtable",
)

# For multi-table reports, use a for-loop
# to iterate across the tables.
for i, table_name in enumerate(df["table_names"]):
    print(table_name)
    print(df["dataframes"].iloc[i].head(3))
    print()
    print()
```

#### Output:
```
Metadata
                  Type              Timing
0           FiveMinLMP 1900-01-01 16:45:00
1  HourlyIntegratedLmp 1900-01-01 16:00:00
2    DayAheadExAnteLmp 1900-01-01 17:00:00


Data
            Name  LMP - FiveMinLMP  MLC - FiveMinLMP  MCC - FiveMinLMP  REGMCP - FiveMinLMP  ...  MLC - DayAheadExAnteLmp  MCC - DayAheadExAnteLmp  LMP - DayAheadExPostLmp  MLC - DayAheadExPostLmp  MCC - DayAheadExPostLmp
1  EES.PERVL2_CT             17.49             -1.69            -12.64                 15.0  ...                    -1.15                     -6.1                     21.0                    -1.15                     -6.1
2      EES.RICE1             17.91             -1.25            -12.66                 15.0  ...                    -0.06                    -6.21                    21.98                    -0.06                    -6.21
3   EES.RVRBEND1             18.42             -0.98            -12.42                 15.0  ...                    -0.38                    -5.83                    22.04                    -0.38                    -5.83

[3 rows x 20 columns]
```

### Example 4:
Download a single-table report along with its text content from [MISO Market Reports](https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/).

#### Code:
```python
from MISOReports.MISOReports import MISOReports

# Downloads the data offered at
# https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getNAI&returnType=csv.
data = MISOReports.get_data(
    report_name="NAI",
    file_extension="csv",
)

print("Text Content:")
print(data.response.text)
print()

print("Dataframe:")
print(data.df)
```

#### Output:
```
Text Content:
RefId,22-Dec-2024 - Interval 16:40 EST

Name,Value
MISO,2212.89


Dataframe:
   Name    Value
0  MISO  2212.89
```

### Example 5:
Download a single-table report with datetime option from [MISO Market Reports](https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/).

#### Code:
```python
import datetime
from MISOReports.MISOReports import MISOReports

# Downloads the data offered at
# https://docs.misoenergy.org/marketreports/MISOdaily3042024.xml.
# Note: the above link's 304 represents
# the number of days past the start of the year, 
# 2024, which aligns with the ddatetime given below.
data = MISOReports.get_data(
    report_name="MISOdaily",
    ddatetime=datetime.datetime(year=2024, month=10, day=30),
)

print(data.df)
```

#### Output:
```
     PostedValue  Hour Data_Code  Data_Date Data_Type  UTCOffset PostingType
0          64975     1           2024-10-30        DF          5       Daily
1          63868     2           2024-10-30        DF          5       Daily
2          62750     3           2024-10-30        DF          5       Daily
3          62581     4           2024-10-30        DF          5       Daily
4          63869     5           2024-10-30        DF          5       Daily
..           ...   ...       ...        ...       ...        ...         ...
619         1935    20       TVA 2024-10-28      FLOW          5       Daily
620         2304    21       TVA 2024-10-28      FLOW          5       Daily
621         2379    22       TVA 2024-10-28      FLOW          5       Daily
622         2343    23       TVA 2024-10-28      FLOW          5       Daily
623         2364    24       TVA 2024-10-28      FLOW          5       Daily

[624 rows x 7 columns]
```

## Contributing
Please take a look at our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
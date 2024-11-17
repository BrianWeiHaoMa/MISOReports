# MISOReports
A library for downloading Midcontinent Independent System Operator (MISO) public reports. As of 2024-11-17, MISOReports supports
reports from [MISORTWDDataBroker](https://api.misoenergy.org/MISORTWDDataBroker/), [MISORTWDBIReporter](https://api.misoenergy.org/MISORTWDBIReporter/),
and [MISO Market Reports](https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/), totalling to well over 100 reports.

With MISOReports, you can skip all of the intermediate URL generation/parsing/typing steps and get any supported report's data
in a dataframe with just a few lines of code. You can also choose to retrieve the get request data directly and use that instead. 

## Features
MISOReports supports but is not limited to the below features:
- Downloading reports by date for reports that offer a date option
- Downloading live reports for reports without a date option
- Downloading raw report content in any of their supported formats (csv, xml, json, xls, xlsx, etc.)
- Well annotated and documented functions and classes (passing mypy --strict test)

## Installation
To install, use
```
pip install MISOReports
```

## Examples

### Example 1:
Download a single-table report from [MISORTWDDataBroker](https://api.misoenergy.org/MISORTWDDataBroker/).

#### Input:
```python
from MISOReports.MISOReports import MISOReports

# Single table reports will be stored
# directly as the dataframe result.

# Downloads the data offered at
# https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getlmpconsolidatedtable&returnType=csv.
df = MISOReports.get_df(
    report_name="lmpconsolidatedtable",
)

print(df)
```

#### Output:
```
               Name    LMP   MLC   MCC  REGMCP  REGMILEAGEMCP  SPINMCP  SUPPMCP  STRMCP  RCUPMCP  RCDOWNMCP  LMP.1  MLC.1  MCC.1  LMP.2  MLC.2  MCC.2  LMP.3  MLC.3  MCC.3
0        EES.AXIALL  20.58 -0.56  0.00   13.55           0.75     2.72     0.01     0.0      0.0        0.0  20.37  -0.74   0.00  20.65  -0.35   0.52  20.65  -0.35   0.52
1    EES.CALCAS1_CT  20.72 -0.42  0.00   13.55           0.75     2.72     0.01     0.0      0.0        0.0  20.51  -0.60   0.00  20.75  -0.25   0.52  20.75  -0.25   0.52
2    EES.CALCAS2_CT  20.72 -0.42  0.00   13.55           0.75     2.72     0.01     0.0      0.0        0.0  20.51  -0.60   0.00  20.75  -0.25   0.52  20.75  -0.25   0.52
3        EES.CARV_A  21.00 -0.14  0.00   13.55           0.75     2.72     0.01     0.0      0.0        0.0  20.77  -0.34   0.00  21.13   0.16   0.49  21.13   0.16   0.49
4       EES.CARV_BC  21.00 -0.14  0.00   13.55           0.75     2.72     0.01     0.0      0.0        0.0  20.77  -0.34   0.00  21.13   0.16   0.49  21.13   0.16   0.49
..              ...    ...   ...   ...     ...            ...      ...      ...     ...      ...        ...    ...    ...    ...    ...    ...    ...    ...    ...    ...
322   EAI.WH_BLUFF2  20.64 -0.50  0.00   13.55           0.75     2.72     0.01     0.0      0.0        0.0  20.53  -0.58   0.00  19.90  -0.69   0.11  19.90  -0.69   0.11
323             EDE  20.53 -0.59 -0.02    0.00           0.00     0.00     0.00     0.0      0.0        0.0  20.62  -0.44  -0.06  21.24  -0.93   1.69  21.24  -0.93   1.69
324   EES.ACAD2_CT1  20.50 -0.64  0.00   13.55           0.75     2.72     0.01     0.0      0.0        0.0  20.26  -0.85   0.00  20.58  -0.41   0.51  20.58  -0.41   0.51
325   EES.ACAD2_CT2  20.50 -0.64  0.00   13.55           0.75     2.72     0.01     0.0      0.0        0.0  20.26  -0.85   0.00  20.58  -0.41   0.51  20.58  -0.41   0.51
326    EES.ACAD2_ST  20.50 -0.64  0.00   13.55           0.75     2.72     0.01     0.0      0.0        0.0  20.26  -0.85   0.00  20.58  -0.41   0.51  20.58  -0.41   0.51

[327 rows x 20 columns]
```

### Example 2:
Download a multi-table report from [MISORTWDDataBroker](https://api.misoenergy.org/MISORTWDDataBroker/).

#### Input:
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
    print(df["dataframes"].iloc[i])
    print()
    print()
```

#### Output:
```
ClearedMW
    Load_Hour  Load_Value
0           1     57306.0
1           2     56564.0
2           3     55085.0
3           4     55189.0
4           5     54450.0
5           6     55161.0
6           7     56981.0
7           8     59703.0
8           9     59882.0
9          10     60419.0
10         11     62572.0
11         12     62215.0
12         13     62212.0
13         14     62423.0
14         15     62019.0
15         16     62861.0
16         17     67282.0
17         18     71489.0
18         19     71420.0
19         20     70631.0
20         21     68146.0
21         22     66190.0
22         23     63428.0
23         24     60859.0


MediumTermLoadForecast
    Hour_End  Load_Forecast
0          1        61570.0
1          2        59957.0
2          3        59707.0
3          4        59008.0
4          5        58701.0
5          6        58634.0
6          7        59941.0
7          8        61064.0
8          9        62505.0
9         10        63714.0
10        11        64406.0
11        12        64917.0
12        13        65523.0
13        14        66128.0
14        15        66466.0
15        16        66811.0
16        17        67815.0
17        18        70013.0
18        19        71686.0
19        20        71145.0
20        21        69849.0
21        22        67944.0
22        23        65504.0
23        24        62802.0


FiveMinTotalLoad
              Load_Time  Load_Value
0   1900-01-01 00:00:00     62534.0
1   1900-01-01 00:05:00     62437.0
2   1900-01-01 00:10:00     62234.0
3   1900-01-01 00:15:00     62102.0
4   1900-01-01 00:20:00     61948.0
..                  ...         ...
153 1900-01-01 12:45:00     65481.0
154 1900-01-01 12:50:00     65576.0
155 1900-01-01 12:55:00     65430.0
156 1900-01-01 13:00:00     65722.0
157 1900-01-01 13:05:00     65874.0

[158 rows x 2 columns]
```

### Example 3:
Download a single-table report with datetime option from [MISO Market Reports](https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/).

#### Input:
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

### Example 4:
Download the raw, unparsed data of a report from [MISO Market Reports](https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/).

#### Input:
```python
from MISOReports.MISOReports import MISOReports

# Downloads the data offered at
# https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getNAI&returnType=csv.
res = MISOReports.get_response(
    report_name="NAI",
    file_extension="csv",
)

print(res.text)
```

#### Output:
```
RefId,17-Nov-2024 - Interval 15:50 EST

Name,Value
MISO,-2494.86
```

### Example 5:
Download a single-table report with datetime option from [MISO Market Reports](https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/).

#### Input:
```python
import datetime
from MISOReports.MISOReports import MISOReports

# Downloads the data offered at
# https://docs.misoenergy.org/marketreports/MISOdaily3042024.xml.
# Note: the above link's 304 represents
# the number of days past the start of the year, 
# 2024, which aligns with the ddatetime given below.
df = MISOReports.get_df(
    report_name="MISOdaily",
    ddatetime=datetime.datetime(year=2024, month=10, day=30),
)

print(df)
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

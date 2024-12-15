# Documentation
This is the documentation for MISOReports.

## Table of Contents
- [Data Types](#data-types)
- [Supported Reports](#supported-reports)
    - [MISORTWDDataBroker Reports](#misortwddatabroker-reports)
    - [MISORTWDBIReporter Reports](#misortwdbireporter-reports)
    - [MISO Market Reports](#miso-market-reports)
        - [Bids](#bids)
        - [Day-Ahead](#day-ahead)
        - [EIA](#eia)
        - [FTR](#ftr)
        - [Historical LMP](#historical-lmp)
        - [Historical MCP](#historical-mcp)
        - [Market Settlements](#market-settlements)
        - [Market to Market](#market-to-market)
        - [Offers](#offers)
        - [Real-Time](#real-time)
        - [Resource Adequacy](#resource-adequacy)
        - [Summary](#summary)
- [Useful Tricks](#useful-tricks)

## Data Types
All dataframe columns are categorized into one of the following data types:
* **string** ex. "Toronto".
* **datetime64\[ns\]** ex. "2024-02-02 08:24:36 PM" or "2024-02-02 16:24:36" or "2024-01-03" or "13:05:00" etc..
* **Float64** ex. 34.13.
* **Int64** ex. 34.

## Supported Reports
Here are the supported reports along with corresponding example URLs. If the report offers multiple formats,
the supported extensions are listed on the right. In the rare case that a report was looked at, but left unimplemented,
it will be indented and an explanation will be provided on the right.

### MISORTWDDataBroker Reports
These can be found at [MISORTWDDataBroker](https://api.misoenergy.org/MISORTWDDataBroker/)

```
apiversion                         https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getapiversion&returnType=json                   JSON
fuelmix                            https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getfuelmix&returnType=csv                    CSV  XML  JSON
ace                                https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getace&returnType=csv                        CSV  XML  JSON
AncillaryServicesMCP               https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getAncillaryServicesMCP&returnType=csv       CSV  XML  JSON
cts                                https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcts&returnType=csv                        CSV  XML  JSON
combinedwindsolar                  https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcombinedwindsolar&returnType=csv          CSV  XML  JSON
WindForecast                       https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindForecast&returnType=xml               XML  JSON
Wind                               https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWind&returnType=csv                       CSV  XML  JSON
SolarForecast                      https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarForecast&returnType=xml              XML  JSON
Solar                              https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolar&returnType=csv                      CSV  XML  JSON
exantelmp                          https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getexantelmp&returnType=csv                  CSV  XML  JSON
lmpconsolidatedtable               https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getlmpconsolidatedtable&returnType=csv       CSV  XML  JSON
nsi1                               https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1&returnType=csv                       CSV  XML  JSON
nsi5                               https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5&returnType=csv                       CSV  XML  JSON
nsi1miso                           https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1miso&returnType=csv                   CSV  XML  JSON
nsi5miso                           https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5miso&returnType=csv                   CSV  XML  JSON
importtotal5                       https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getimporttotal5&returnType=json              CSV  XML  JSON
realtimebindingconstraints         https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getrealtimebindingconstraints&returnType=csv CSV  XML  JSON
realtimebindingsrpbconstraints     https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getrealtimebindingsrpbconstraints&returnType=csv CSV  XML  JSON
reservebindingconstraints          https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getreservebindingconstraints&returnType=csv  CSV  XML  JSON
RSG                                https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getRSG&returnType=csv                        CSV  XML  JSON
totalload                          https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=gettotalload&returnType=csv                  CSV  XML  JSON
WindActual                         https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindActual&returnType=xml                 XML  JSON
SolarActual                        https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarActual&returnType=xml                XML  JSON
NAI                                https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getNAI&returnType=csv                        CSV  XML  JSON
regionaldirectionaltransfer        https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getregionaldirectionaltransfer&returnType=csv CSV  XML  JSON
generationoutagesplusminusfivedays https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getgenerationoutagesplusminusfivedays&returnType=csv CSV  XML  JSON
```

### MISORTWDBIReporter Reports
These can be found at [MISORTWDBIReporter](https://api.misoenergy.org/MISORTWDBIReporter/).
```
currentinterval https://api.misoenergy.org/MISORTWDBIReporter/Reporter.asmx?messageType=currentinterval&returnType=csv CSV
```

### MISO Market Reports
These can be found at [MISO Market Reports](https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/)
under each report's corresponding section.

#### Bids
```
bids_cb https://docs.misoenergy.org/marketreports/20240801_bids_cb.zip
```

#### Day-Ahead
```
da_bcsf      https://docs.misoenergy.org/marketreports/20241029_da_bcsf.xls
da_bc        https://docs.misoenergy.org/marketreports/20241029_da_bc.xls
da_pbc       https://docs.misoenergy.org/marketreports/20220107_da_pbc.csv
da_pr        https://docs.misoenergy.org/marketreports/20241030_da_pr.xls
da_rpe       https://docs.misoenergy.org/marketreports/20241029_da_rpe.xls
da_ex        https://docs.misoenergy.org/marketreports/20220321_da_ex.xls
da_ex_rg     https://docs.misoenergy.org/marketreports/20241030_da_ex_rg.xlsx
da_bc_HIST   https://docs.misoenergy.org/marketreports/2024_da_bc_HIST.csv
```

#### EIA
```
MISOdaily           https://docs.misoenergy.org/marketreports/MISOdaily3312024.xml
MISOsamedaydemand   https://docs.misoenergy.org/marketreports/MISOsamedaydemand.xml

```

#### FTR
```
ftr_allocation_restoration     https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_restoration.zip
ftr_allocation_stage_1A        https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1A.zip
ftr_allocation_stage_1B        https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1B.zip
ftr_allocation_summary         https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_summary.zip
ftr_annual_results_round_1     https://docs.misoenergy.org/marketreports/20240401_ftr_annual_results_round_1.zip
ftr_annual_results_round_2     https://docs.misoenergy.org/marketreports/20240501_ftr_annual_results_round_2.zip
ftr_annual_results_round_3     https://docs.misoenergy.org/marketreports/20240101_ftr_annual_results_round_3.zip
ftr_annual_bids_offers         https://docs.misoenergy.org/marketreports/2023_ftr_annual_bids_offers.zip
ftr_mpma_results               https://docs.misoenergy.org/marketreports/20241101_ftr_mpma_results.zip
ftr_mpma_bids_offers           https://docs.misoenergy.org/marketreports/20240801_ftr_mpma_bids_offers.zip
```

#### Historical LMP
```
DA_Load_EPNodes            https://docs.misoenergy.org/marketreports/DA_Load_EPNodes_20241021.zip
da_exante_lmp              https://docs.misoenergy.org/marketreports/20241026_da_exante_lmp.csv
da_expost_lmp              https://docs.misoenergy.org/marketreports/20241026_da_expost_lmp.csv
2024-Jul-Sep_DA_LMPs       https://docs.misoenergy.org/marketreports/2024-Jul-Sep_DA_LMPs.zip
2024_Jul-Sep_RT_LMPs       https://docs.misoenergy.org/marketreports/2024_Jul-Sep_RT_LMPs.zip
5min_exante_lmp            https://docs.misoenergy.org/marketreports/20241025_5min_exante_lmp.xlsx
RT_Load_EPNodes            https://docs.misoenergy.org/marketreports/RT_Load_EPNodes_20241018.zip
rt_lmp_final               https://docs.misoenergy.org/marketreports/20241021_rt_lmp_final.csv
rt_lmp_prelim              https://docs.misoenergy.org/marketreports/20241024_rt_lmp_prelim.csv
5MIN_LMP                   https://docs.misoenergy.org/marketreports/20241021_5MIN_LMP.zip
```

#### Historical MCP
```
asm_exante_damcp            https://docs.misoenergy.org/marketreports/20241030_asm_exante_damcp.csv
asm_expost_damcp            https://docs.misoenergy.org/marketreports/20241030_asm_expost_damcp.csv
5min_exante_mcp             https://docs.misoenergy.org/marketreports/20241030_5min_exante_mcp.xlsx
asm_rtmcp_final             https://docs.misoenergy.org/marketreports/20241026_asm_rtmcp_final.csv
asm_rtmcp_prelim            https://docs.misoenergy.org/marketreports/20241029_asm_rtmcp_prelim.csv
5min_expost_mcp             https://docs.misoenergy.org/marketreports/20241028_5min_expost_mcp.xlsx
da_exante_ramp_mcp          https://docs.misoenergy.org/marketreports/20241030_da_exante_ramp_mcp.xlsx
da_exante_str_mcp           https://docs.misoenergy.org/marketreports/20241029_da_exante_str_mcp.xlsx
da_expost_ramp_mcp          https://docs.misoenergy.org/marketreports/20241030_da_expost_ramp_mcp.xlsx
da_expost_str_mcp           https://docs.misoenergy.org/marketreports/20241030_da_expost_str_mcp.xlsx
rt_expost_ramp_5min_mcp     https://docs.misoenergy.org/marketreports/202410_rt_expost_ramp_5min_mcp.xlsx
rt_expost_ramp_mcp          https://docs.misoenergy.org/marketreports/202410_rt_expost_ramp_mcp.xlsx
rt_expost_str_5min_mcp      https://docs.misoenergy.org/marketreports/202409_rt_expost_str_5min_mcp.xlsx
rt_expost_str_mcp           https://docs.misoenergy.org/marketreports/202410_rt_expost_str_mcp.xlsx
```

#### Market Settlements
```
Daily_Uplift_by_Local_Resource_Zone https://docs.misoenergy.org/marketreports/20241020_Daily_Uplift_by_Local_Resource_Zone.xlsx
ms_vlr_HIST                         https://docs.misoenergy.org/marketreports/2022_ms_vlr_HIST.csv
ccf_co                              https://docs.misoenergy.org/marketreports/20241020_ccf_co.csv
ms_ecf_srw                          https://docs.misoenergy.org/marketreports/20241029_ms_ecf_srw.xlsx
ms_vlr_HIST_SRW                     https://docs.misoenergy.org/marketreports/2024_ms_vlr_HIST_SRW.xlsx
MARKET_SETTLEMENT_DATA_SRW          https://docs.misoenergy.org/marketreports/MARKET_SETTLEMENT_DATA_SRW.zip
ms_ri_srw                           https://docs.misoenergy.org/marketreports/20241029_ms_ri_srw.xlsx
ms_rnu_srw                          https://docs.misoenergy.org/marketreports/20241029_ms_rnu_srw.xlsx
ms_rsg_srw                          https://docs.misoenergy.org/marketreports/20241029_ms_rsg_srw.xlsx
ms_vlr_srw                          https://docs.misoenergy.org/marketreports/20240901_ms_vlr_srw.xlsx
Total_Uplift_by_Resource            https://docs.misoenergy.org/marketreports/20241001_Total_Uplift_by_Resource.xlsx
```

#### Market to Market
```
Allocation_on_MISO_Flowgates https://docs.misoenergy.org/marketreports/Allocation_on_MISO_Flowgates_2024_10_29.csv
M2M_FFE                      https://docs.misoenergy.org/marketreports/M2M_FFE_2024_10_29.CSV
M2M_Flowgates_as_of          https://docs.misoenergy.org/marketreports/M2M_Flowgates_as_of_20241030.CSV
    da_M2M_Settlement_srw        https://docs.misoenergy.org/marketreports/da_M2M_Settlement_srw_2024.csv (this one does not have a single non-empty report as of 2024-11-19)
M2M_Settlement_srw           https://docs.misoenergy.org/marketreports/M2M_Settlement_srw_2024.csv
```

#### Offers
```
asm_da_co          https://docs.misoenergy.org/marketreports/20240801_asm_da_co.zip
asm_rt_co          https://docs.misoenergy.org/marketreports/20240801_asm_rt_co.zip
da_co              https://docs.misoenergy.org/marketreports/20240801_da_co.zip
Dead_Node_Report   https://docs.misoenergy.org/marketreports/Dead_Node_Report_20241030.xls
rt_co              https://docs.misoenergy.org/marketreports/20240801_rt_co.zip
```

#### Real-Time
```
rt_fuel_on_margin                    https://docs.misoenergy.org/marketreports/2023_rt_fuel_on_margin.zip
rt_or                                https://docs.misoenergy.org/marketreports/20240910_rt_or.xls
rt_bc                                https://docs.misoenergy.org/marketreports/20241030_rt_bc.xls
rt_pbc                               https://docs.misoenergy.org/marketreports/20241001_rt_pbc.csv
rt_ex                                https://docs.misoenergy.org/marketreports/20241030_rt_ex.xls
rt_mf                                https://docs.misoenergy.org/marketreports/20241030_rt_mf.xlsx
rt_irsf                              https://docs.misoenergy.org/marketreports/20241030_rt_irsf.csv
rt_pr                                https://docs.misoenergy.org/marketreports/20241026_rt_pr.xls
Historical_RT_RSG_Commitment         https://docs.misoenergy.org/marketreports/2024_Historical_RT_RSG_Commitment.csv
rt_rpe                               https://docs.misoenergy.org/marketreports/20241101_rt_rpe.xls
Resource_Uplift_by_Commitment_Reason https://docs.misoenergy.org/marketreports/20241009_Resource_Uplift_by_Commitment_Reason.xlsx
RT_UDS_Approved_Case_Percentage      https://docs.misoenergy.org/marketreports/20241023_RT_UDS_Approved_Case_Percentage.csv
rt_bc_HIST                           https://docs.misoenergy.org/marketreports/2024_rt_bc_HIST.csv
```

#### Resource Adequacy
```
MM_Annual_Report https://docs.misoenergy.org/marketreports/20241030_MM_Annual_Report.zip
```

#### Summary
```
cpnode_reszone            https://docs.misoenergy.org/marketreports/20241002_cpnode_reszone.xlsx
sr_ctsl                   https://docs.misoenergy.org/marketreports/20241020_sr_ctsl.pdf
df_al                     https://docs.misoenergy.org/marketreports/20241030_df_al.xls
rf_al                     https://docs.misoenergy.org/marketreports/20241030_rf_al.xls
sr_gfm                    https://docs.misoenergy.org/marketreports/20241030_sr_gfm.xlsx
dfal_HIST                 https://docs.misoenergy.org/marketreports/20241030_dfal_HIST.xls
historical_gen_fuel_mix   https://docs.misoenergy.org/marketreports/historical_gen_fuel_mix_2023.xlsx
hwd_HIST                  https://docs.misoenergy.org/marketreports/20241030_hwd_HIST.csv
sr_hist_is                https://docs.misoenergy.org/marketreports/2024_sr_hist_is.csv
rfal_HIST                 https://docs.misoenergy.org/marketreports/20241030_rfal_HIST.xls
sr_lt                     https://docs.misoenergy.org/marketreports/20241028_sr_lt.xls
sr_la_rg                  https://docs.misoenergy.org/marketreports/20241024_sr_la_rg.csv
mom                       https://docs.misoenergy.org/marketreports/20241020_mom.xlsx
sr_nd_is                  https://docs.misoenergy.org/marketreports/20241020_sr_nd_is.xls
PeakHourOverview          https://docs.misoenergy.org/marketreports/PeakHourOverview_03052022.csv
sr_tcdc_group2            https://docs.misoenergy.org/marketreports/2024_sr_tcdc_group2.csv
```

## Useful Tricks
Here are some coding patterns that might be of help to you.

### Datetime Extraction for MISORTWDDataBroker Reports
Many of the reports offered by MISORTWDDataBroker come with datetime data at the top of the
raw data which can be easily parsed by using the function below.

```python
from MISOReports.MISOReports import MISOReports
import re
import datetime

# You can use this function for parsing datetime data in many MISORTWDDataBroker reports.
def parse_datetime_from_text(text: str):
    match = re.search(r'(\d{2}-\w{3}-\d{4}) - Interval (\d{2}:\d{2})', text)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        date_time_str = f"{date_str} {time_str}"
        date_time_obj = datetime.datetime.strptime(date_time_str, "%d-%b-%Y %H:%M")
        return date_time_obj
    else:
        raise ValueError("Unexpected format.")

# Report link: https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getNAI&returnType=csv.
report_name = "NAI"

# Download the raw data to get the datetime.
res = MISOReports.get_response(
    report_name=report_name,
    file_extension="csv",
)

print("Raw data:")
print(res.text)

# Download the dataframe.
df = MISOReports.get_df(
    report_name=report_name,
)

df["datetime"] = parse_datetime_from_text(res.text)

print("Final dataframe:")
print(df)
```

Executing the above gives:
```
Raw data:
RefId,21-Nov-2024 - Interval 20:50 EST

Name,Value
MISO,-32.77

Final dataframe:
   Name  Value            datetime
0  MISO -32.77 2024-11-21 20:50:00
```

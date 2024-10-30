# TODO LIST

## Support for reports
This section contains the links to reports that we plan on supporting. The entries that have been indented are already supported.
We may add more in the future, but the ones listed currently are the ones that will be the most worth it.

### Support for MISORTWDDataBroker reports 
The possible extensions (ones that are offered in the link) are listed on the right side. 

```
https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getapiversion&returnType=json JSON 
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getfuelmix&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getace&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getAncillaryServicesMCP&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcts&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getcombinedwindsolar&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindForecast&returnType=xml XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWind&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarForecast&returnType=xml XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolar&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getexantelmp&returnType=csv CSV	XML	JSON
https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getlmpconsolidatedtable&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1&returnType=csv CSV XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi1miso&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getnsi5miso&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getimporttotal5&returnType=json CSV	XML	JSON
https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getrealtimebindingconstraints&returnType=csv CSV	XML	JSON
https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getrealtimebindingsrpbconstraints&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getreservebindingconstraints&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getRSG&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=gettotalload&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindActual&returnType=xml XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarActual&returnType=xml XML	JSO
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getNAI&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getregionaldirectionaltransfer&returnType=csv CSV	XML	JSON
    https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getgenerationoutagesplusminusfivedays&returnType=csv CSV	XML	JSON
```

### Support for MISORTWDBIReporter reports 
```
https://api.misoenergy.org/MISORTWDBIReporter/Reporter.asmx?messageType=currentinterval&returnType=csv Current Interval	 Rolling Current Day 	Previous Day
```

### Support for market reports
Historical LMP
```
    https://docs.misoenergy.org/marketreports/DA_Load_EPNodes_20241021.zip
    https://docs.misoenergy.org/marketreports/20241026_da_exante_lmp.csv
    https://docs.misoenergy.org/marketreports/20241026_da_expost_lmp.csv
    https://docs.misoenergy.org/marketreports/2024-Jul-Sep_DA_LMPs.zip
https://docs.misoenergy.org/marketreports/2024_Jul-Sep_RT_LMPs.zip
    https://docs.misoenergy.org/marketreports/20241025_5min_exante_lmp.xlsx
https://docs.misoenergy.org/marketreports/RT_Load_EPNodes_20241018.zip
    https://docs.misoenergy.org/marketreports/20241021_rt_lmp_final.csv
    https://docs.misoenergy.org/marketreports/20241024_rt_lmp_prelim.csv
https://docs.misoenergy.org/marketreports/20241021_5MIN_LMP.zip
```

Bids
```
https://docs.misoenergy.org/marketreports/20240801_bids_cb.zip
```

Day-Ahead
```
https://docs.misoenergy.org/marketreports/20241029_da_bcsf.xls
https://docs.misoenergy.org/marketreports/20241029_da_bc.xls
https://docs.misoenergy.org/marketreports/20241029_da_pbc.csv
https://docs.misoenergy.org/marketreports/20241030_da_pr.xls
https://docs.misoenergy.org/marketreports/20241029_da_rpe.xls
https://docs.misoenergy.org/marketreports/20220321_da_ex.xls
https://docs.misoenergy.org/marketreports/20241030_da_ex_rg.xlsx
https://docs.misoenergy.org/marketreports/2024_da_bc_HIST.csv
```

EIA
```
https://docs.misoenergy.org/marketreports/MISOdaily3042024.xml
https://docs.misoenergy.org/marketreports/MISOsamedaydemand.xml
```

FTR
```
https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_restoration.zip
https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1A.zip
https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_stage_1B.zip
https://docs.misoenergy.org/marketreports/20240401_ftr_allocation_summary.zip
https://docs.misoenergy.org/marketreports/20240401_ftr_annual_results_round_1.zip
https://docs.misoenergy.org/marketreports/20240501_ftr_annual_results_round_2.zip
https://docs.misoenergy.org/marketreports/20240101_ftr_annual_results_round_3.zip
https://docs.misoenergy.org/marketreports/2023_ftr_annual_bids_offers.zip
https://docs.misoenergy.org/marketreports/20241101_ftr_mpma_results.zip
https://docs.misoenergy.org/marketreports/20240801_ftr_mpma_bids_offers.zip
```

Historical MCP
```
https://docs.misoenergy.org/marketreports/20241030_asm_exante_damcp.csv
https://docs.misoenergy.org/marketreports/20241030_asm_expost_damcp.csv
https://docs.misoenergy.org/marketreports/20241030_5min_exante_mcp.xlsx
https://docs.misoenergy.org/marketreports/20241026_asm_rtmcp_final.csv
https://docs.misoenergy.org/marketreports/20241029_asm_rtmcp_prelim.csv
https://docs.misoenergy.org/marketreports/20241028_5min_expost_mcp.xlsx
https://docs.misoenergy.org/marketreports/20241030_da_exante_ramp_mcp.xlsx
https://docs.misoenergy.org/marketreports/20241029_da_exante_str_mcp.xlsx
https://docs.misoenergy.org/marketreports/20241030_da_expost_ramp_mcp.xlsx
https://docs.misoenergy.org/marketreports/20241030_da_expost_str_mcp.xlsx
https://docs.misoenergy.org/marketreports/202410_rt_expost_ramp_5min_mcp.xlsx
https://docs.misoenergy.org/marketreports/202410_rt_expost_ramp_mcp.xlsx
https://docs.misoenergy.org/marketreports/202409_rt_expost_str_5min_mcp.xlsx
https://docs.misoenergy.org/marketreports/202410_rt_expost_str_mcp.xlsx
```

Market Settlements
```
https://docs.misoenergy.org/marketreports/20241020_Daily_Uplift_by_Local_Resource_Zone.xlsx
https://docs.misoenergy.org/marketreports/2022_ms_vlr_HIST.csv
https://docs.misoenergy.org/marketreports/20241022_ccf_co.csv
https://docs.misoenergy.org/marketreports/20241029_ms_ecf_srw.xlsx
https://docs.misoenergy.org/marketreports/2024_ms_vlr_HIST_SRW.xlsx
https://docs.misoenergy.org/marketreports/MARKET_SETTLEMENT_DATA_SRW.zip
https://docs.misoenergy.org/marketreports/20241029_ms_ri_srw.xlsx
https://docs.misoenergy.org/marketreports/20241029_ms_rnu_srw.xlsx
https://docs.misoenergy.org/marketreports/20241029_ms_rsg_srw.xlsx
https://docs.misoenergy.org/marketreports/20240901_ms_vlr_srw.xlsx
https://docs.misoenergy.org/marketreports/20241001_Total_Uplift_by_Resource.xlsx
```

Market to Market
```
https://docs.misoenergy.org/marketreports/Allocation_on_MISO_Flowgates_2024_10_29.csv
https://docs.misoenergy.org/marketreports/M2M_FFE_2024_10_29.CSV
https://docs.misoenergy.org/marketreports/M2M_Flowgates_as_of_20241030.CSV
https://docs.misoenergy.org/marketreports/da_M2M_Settlement_srw_2024.csv
https://docs.misoenergy.org/marketreports/M2M_Settlement_srw_2024.csv
```

Offers
```
https://docs.misoenergy.org/marketreports/20240801_asm_da_co.zip
https://docs.misoenergy.org/marketreports/20240801_asm_rt_co.zip
https://docs.misoenergy.org/marketreports/20240801_da_co.zip
https://docs.misoenergy.org/marketreports/Dead_Node_Report_20241030.xls
https://docs.misoenergy.org/marketreports/20240801_rt_co.zip
```

Real-Time
```
https://docs.misoenergy.org/marketreports/2023_rt_fuel_on_margin.zip
https://docs.misoenergy.org/marketreports/20241030_rt_or.xls
https://docs.misoenergy.org/marketreports/20241030_rt_bc.xls
https://docs.misoenergy.org/marketreports/20241030_rt_pbc.csv
https://docs.misoenergy.org/marketreports/20241030_rt_ex.xls
https://docs.misoenergy.org/marketreports/20241030_rt_mf.xlsx
https://docs.misoenergy.org/marketreports/20241030_rt_irsf.csv
https://docs.misoenergy.org/marketreports/20241026_rt_pr.xls
https://docs.misoenergy.org/marketreports/2024_Historical_RT_RSG_Commitment.csv
https://docs.misoenergy.org/marketreports/20241030_rt_rpe.xls
https://docs.misoenergy.org/marketreports/20241009_Resource_Uplift_by_Commitment_Reason.xlsx
https://docs.misoenergy.org/marketreports/20241023_RT_UDS_Approved_Case_Percentage.csv
https://docs.misoenergy.org/marketreports/2024_rt_bc_HIST.csv
```

Resource Adequacy
```
https://docs.misoenergy.org/marketreports/20241030_MM_Annual_Report.zip
```

Summary
```
https://docs.misoenergy.org/marketreports/20241002_cpnode_reszone.xlsx
https://docs.misoenergy.org/marketreports/20241020_sr_ctsl.pdf
https://docs.misoenergy.org/marketreports/20241030_df_al.xls
https://docs.misoenergy.org/marketreports/20241030_rf_al.xls
https://docs.misoenergy.org/marketreports/20241030_sr_gfm.xlsx
https://docs.misoenergy.org/marketreports/20241030_dfal_HIST.xls
https://docs.misoenergy.org/marketreports/historical_gen_fuel_mix_2023.xlsx
https://docs.misoenergy.org/marketreports/20241030_hwd_HIST.csv
https://docs.misoenergy.org/marketreports/2024_sr_hist_is.csv
https://docs.misoenergy.org/marketreports/20241030_rfal_HIST.xls
https://docs.misoenergy.org/marketreports/20241028_sr_lt.xls
https://docs.misoenergy.org/marketreports/20241024_sr_la_rg.csv
https://docs.misoenergy.org/marketreports/20241020_mom.xlsx
https://docs.misoenergy.org/marketreports/20241020_sr_nd_is.xls
https://docs.misoenergy.org/marketreports/PeakHourOverview_03052022.csv
https://docs.misoenergy.org/marketreports/2024_sr_tcdc_group2.csv
```

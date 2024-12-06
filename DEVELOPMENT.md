# Development
Here you can find the general guidelines for the development of MISOReports.

## Github Workflow
Before commiting or pushing to github, remember to run these in the terminal and make sure everything passes:

For running all tests:
```
pytest 
```

If you want to skip the completion and long tests:
```
pytest -m "not completion and not long"
```

For checking type annotations:
```
mypy --strict .\MISOReports\MISOReports.py 
```

## Coding Style
* We are using the vscode extension, autoDocstring's, one-line-sphinx documentation template.
* Try to keep the style the same as the code that was previously there in all respects (naming schemes, character length per line, etc.) 
* Try too keep the line length to PEP8 standards. Exceptions where it makes sense is fine.

## Reports to Pandas Dataframe Mapping Logic
Remember to make a parsing function in parsers.py and make a new Report entry in MISOReports.report_mappings.
As well, make sure to add the report's test in single_df_test_list or multiple_dfs_test_list in test_MISOReports.py.
Continue to use the same naming scheme as the previous code.

When in doubt, check the entries for previously completed reports.

Map every single column type to one of the below data pandas types:
* **string** ex. "Toronto".
* **datetime64\[ns\]** ex. "2024-02-02 08:24:36 PM" or "2024-02-02 16:24:36" or "2024-01-03" or "13:05:00" etc..
* **Float64** ex. 34.13.
* **Int64** ex. 34.

When looking at the report, use this checklist:
* Ignore null/empty values when deciding with the below guidelines.
* If there is any string (ex. names, codes, etc.) in the column, the column type should be **string**.
* Otherwise if the column is clearly meant to portray datetime/date/time, the column type should be **datetime64[ns]**.
* Otherwise if any number in the column has a decimal, the column type should be **Float64**.
* Otherwise if the numbers in the column are all integers, the column type should be **Int64**.
* Otherwise make note of the new case here.

## Report Parser Reference
csv
```python
def parse_rt_lmp_prelim(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    csv_data = "\n".join(text.splitlines()[4:])

    df = pd.read_csv(
        filepath_or_buffer=io.StringIO(csv_data),
    )

    df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]] = df[["HE 1", "HE 2", "HE 3", "HE 4", "HE 5", "HE 6", "HE 7", "HE 8", "HE 9", "HE 10", "HE 11", "HE 12", "HE 13", "HE 14", "HE 15", "HE 16", "HE 17", "HE 18", "HE 19", "HE 20", "HE 21", "HE 22", "HE 23", "HE 24"]].astype("Float64")
    df[["Node", "Type", "Value"]] = df[["Node", "Type", "Value"]].astype("string")

    return df
```

json
```python
def parse_SolarForecast(
    res: requests.Response,
) -> pd.DataFrame:
    text = res.text
    dictionary = json.loads(text)

    df = pd.DataFrame(
        data=dictionary["Forecast"],
    )

    df[["DateTimeEST"]] = df[["DateTimeEST"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")
    df[["HourEndingEST"]] = df[["HourEndingEST"]].astype("Int64")
    df[["Value"]] = df[["Value"]].astype("Float64")

    return df
```

zip with a csv file in the extracted folder
```python
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
    df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]] = df[["HE1", "HE2", "HE3", "HE4", "HE5", "HE6", "HE7", "HE8", "HE9", "HE10", "HE11", "HE12", "HE13", "HE14", "HE15", "HE16", "HE17", "HE18", "HE19", "HE20", "HE21", "HE22", "HE23", "HE24"]].astype("Float64")
    df[["NODE", "TYPE", "VALUE"]] = df[["NODE", "TYPE", "VALUE"]].astype("string")

    return df
```

excel
```python
def parse_5min_exante_lmp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    ).iloc[:-1]

    df[["RT Ex-Ante LMP", "RT Ex-Ante MEC", "RT Ex-Ante MLC", "RT Ex-Ante MCC"]] = df[["RT Ex-Ante LMP", "RT Ex-Ante MEC", "RT Ex-Ante MLC", "RT Ex-Ante MCC"]].astype("Float64")
    df[["CP Node"]] = df[["CP Node"]].astype("string")
    df[["Time (EST)"]] = df[["Time (EST)"]].apply(pd.to_datetime, format="%Y-%m-%d %I:%M:%S %p")

    return df
```

## Using Checker.py
To see the options available:
```
python -m MISOReports.checker -h
```

### Example: 
```
python -m MISOReports.checker -r ccf_co ms_vlr_HIST rt_pr ms_vlr_srw ms_rsg_srw -p -o
```
This prints the get_df() results for the reports with names ccf_co, ms_vlr_HIST, rt_pr, ms_vlr_srw, and ms_rsg_srw,
and saves an output file to the current working directory.

```
python -m MISOReports.checker -a -p -o ./my_files/
```
This prints the get_df() results for the ALL reports
and saves an output file to the directory ./my_files/.

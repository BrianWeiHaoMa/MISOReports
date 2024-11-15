# Development guidelines

## Github workflow
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

## Coding style
* We are using the vscode extension, autoDocstring's, one-line-sphinx documentation template.
* Try to keep the style the same as the code that was previously there in all respects (naming schemes, character length per line, etc.) 
* Try too keep the line length to PEP8 standards. Exceptions where it makes sense is fine.
* When adding support for a new report, if it is on the TODO list, mark it off as done. If not, make a new entry for it.

## Reports to pandas dataframe mapping logic
Remember to make a parsing function in ReportParsers and make a new Report entry in report_mappings.
As well, make sure to add the report's test in report_columns_type_mappings in test_MISOReports.py.
Continue to use the same naming scheme as the previous code.

When in doubt, check the entries for previously completed reports (you can find them on the TODOS.md file).

Map every single column type to one of the below data types:
* **pandas.core.arrays.string_.StringDtype()** ex. "Toronto".
* **numpy.dtypes.DateTime64DType()** ex. "2024-02-02 08:24:36 PM" or "2024-02-02 16:24:36" or "2024-01-03" or "13:05:00" etc..
* **numpy.dtypes.Float64DType()** ex. 34.13.
* **pandas.core.arrays.integer.Int64Dtype()** ex. 34.

When looking at the report, use this checklist:
* Ignore null/empty values when deciding with the below guidelines.
* If there is any string (ex. names, codes, etc.) in the column, the column type should be **pandas.core.arrays.string_.StringDtype()**.
* Otherwise if the column is clearly meant to portray datetime/date/time, the column type should be **numpy.dtypes.DateTime64DType()**.
* Otherwise if any number in the column has a decimal, the column type should be **numpy.dtypes.Float64DType()**.
* Otherwise if the numbers in the column are all integers, the column type should be **pandas.core.arrays.integer.Int64Dtype()**.
* Otherwise make note of the new case here.

## Report parser reference
csv
```python
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
```
json
```python
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
```
zip with a csv file in the extracted folder
```python
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
```
excel
```python
@staticmethod
def parse_5min_exante_lmp(
    res: requests.Response,
) -> pd.DataFrame:
    df = pd.read_excel(
        io=io.BytesIO(res.content),
        skiprows=3,
    )

    return df
```

## Templates
run.py
```python
import datetime
from MISOReports.MISOReports import MISOReports
import pandas as pd

report_name = "rt_or"
file_extension = "xls"

ddatetime = datetime.datetime(year=2024, month=9, day=10)

url = MISOReports.get_url(
    report_name=report_name,
    file_extension=file_extension,
    ddatetime=ddatetime,
)

df = MISOReports.get_df(
    report_name=report_name, 
    ddatetime=ddatetime,
)

print(f"URL example: {url}")

print("Top of df")
print(df.head(10))
print()
print("Bottom of df")
print(df.tail(10))

columns = list(df.columns)

types = [str(type(df.iloc[0, i])) for i in range(df.shape[1])]

types_df = pd.DataFrame(
    {
        "columns": columns,
        "types": types,
    }
)

print(types_df.to_string())
```

## Using checker.py
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

# Development guidelines

## Github workflow
Before commiting or pushing to github, remember run these in the terminal and make sure everything passes:
```
python -m pytest .\MISOReports\test_MISOReports.py
```
```
mypy --strict .\MISOReports\MISOReports.py 
```

## Coding style
* We are using the vscode extension, autoDocstring's, one-line-sphinx documentation template.
* Try to keep the style the same as the code that was previously there in all respects (naming schemes, character length per line, etc.) 
* Try too keep the line length to PEP8 standards. Exceptions where it makes sense is fine.
* When adding support for a new report, if it is on the TODO list, mark it off as done. If not, make a new entry for it.

## Reports to pandas dataframe mapping logic
Remember to make a parsing function in ReportParsers and make a new Report entry in report_mappings. Use the same naming scheme as the previous code.

When in doubt, check previously completed reports (you can find them on the TODOS.md file).

* If any number in the column has a decimal, convert column to Float64.
* If the numbers in the column are all integers, convert column to Int64.
* If the number is a datetime, convert column to datetime64.

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
    ).astype(
        dtype={
            "HourEndingEST": pd.Int64Dtype(),
            "Value": pd.Float64Dtype(),
        }
    )

    df["DateTimeEST"] = pd.to_datetime(df["DateTimeEST"], format="%Y-%m-%d %I:%M:%S %p")

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
        parse_dates=[
            "MARKET_DAY", 
        ],
        date_format={
            "MARKET_DAY": "%m/%d/%Y",
        },
    )

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

import os
import datetime
import sys
from argparse import ArgumentParser

import pandas as pd
import numpy as np

from MISOReports.MISOReports import (
    MISOReports,
)
from MISOReports.parsers import (
    MULTI_DF_NAMES_COLUMN,
    MULTI_DF_DFS_COLUMN,
)


def string_format_suggestions(
    df: pd.DataFrame,
    report_name: str,
) -> str:
    categories = {
        "float": [], 
        "date": [], 
        "int": [], 
        "string": [], 
        "other": [],
    }
    
    dtypes = df.dtypes
    for k in dtypes.index:
        new = str(type(dtypes[k]))

        if "Float" in new:
            categories["float"].append(k)
        elif "Date" in new:
            categories["date"].append(k)
        elif "String" in new:
            categories["string"].append(k)
        elif "Int" in new:
            categories["int"].append(k)
        else:
            categories["other"].append(k)

    data_types = {
        "float": "numpy.dtypes.Float64DType",
        "int": "pandas.core.arrays.integer.Int64Dtype",
        "string": "pandas.core.arrays.string_.StringDtype",
    }

    test_config = {}
    unknown_col_str = ""

    res = "Suggested Configs:\n"

    for cat in ("float", "int", "string", "date", "other",):
        column_names = tuple(categories[cat])
        list_string = "[" + ", ".join([f'"{col}"' for col in column_names]) + "]"

        if len(column_names):            
            if cat in ("float", "int", "string",):
                res += f"\tdf[{list_string}] = df[{list_string}].astype({data_types[cat]}())\n"
                
                test_config[column_names] = data_types[cat]
            elif cat == "date":
                res += f"\tdf[{list_string}] = df[{list_string}].apply(pd.to_datetime, format=\"TODO PUT FORMAT HERE\")\n"
                
                test_config[column_names] = "numpy.dtypes.DateTime64DType"
            else:
                unknown_col_str = f"TODO figure out these cols: {list_string}\n"
                
                res += unknown_col_str

    config_dict_str = f"Test Config:\n\"{report_name}\": " + "{\n"

    for cols, dtype in test_config.items():
        cols_formatted = ", ".join(f'"{col}"' for col in cols)
        config_dict_str += f"\t({cols_formatted},): {dtype},\n"

    config_dict_str += "},\n"

    if unknown_col_str:
        config_dict_str += "\n" + unknown_col_str

    res += "\n" + config_dict_str

    res += """
Usable types:
pandas.core.arrays.string_.StringDtype
numpy.dtypes.DateTime64DType
numpy.dtypes.Float64DType
pandas.core.arrays.integer.Int64Dtype
"""

    return res


def string_format_df_types(
    df: pd.DataFrame,
    auto_size: bool = False,
) -> pd.DataFrame:
    columns = list(df.columns)
    
    dtypes = df.dtypes
    types = []
    for k in dtypes.index:
        new = str(type(dtypes[k]))

        types.append(new)

    types_df = pd.DataFrame(
        columns=columns,
        data=[types],
    )

    if auto_size:
        res = str(types_df)
    else:
        res = types_df.to_string()

    return res


def string_format_split_df(
    df: pd.DataFrame,
    top: int = 3,
    bottom: int = 3,
    auto_size: bool = False,
) -> pd.DataFrame:
    if auto_size:
        top_str = str(df.head(top))
        bottom_str = str(df.tail(bottom))
    else:
        top_str = df.head(top).to_string()
        bottom_str = df.tail(bottom).to_string()

    columns_str = ", ".join([f'"{col}"' for col in df.columns])

    res = f"""
columns: {columns_str}

shape: {df.shape}

Dataframe top({top}):
{top_str}

Dataframe bottom({bottom}):
{bottom_str}

Dataframe types:
{string_format_df_types(df=df, auto_size=auto_size)}
"""
    return res


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-a", "--all", action="store_true", default=False, help="Run the check for all reports.")
    parser.add_argument("-r", "--report_names", nargs='*', default=None, help="A list of reports to run the check for.")
    parser.add_argument("-o", "--output", type=str, nargs="?", const="", default=None, help="The output directory for the result file.")
    parser.add_argument("-p", "--print", action="store_true", default=False,  help="Print the output in the terminal.")
    parser.add_argument("-t", "--top", type=int, default=3, help="The number of rows to show from the top of the df.")
    parser.add_argument("-b", "--bottom", type=int, default=3, help="The number of rows to show from bottom of the df.")          
    parser.add_argument("-s", "--auto_size", action="store_true", default=False, help="Automatically size the output on the df.")
    args = parser.parse_args(sys.argv[1:])

    i_all = args.all
    i_report_names = args.report_names
    i_output = args.output
    i_print = args.print
    i_top = args.top
    i_bottom = args.bottom
    i_auto_size = args.auto_size

    report_names = []
    if i_all:
        report_names = list(MISOReports.report_mappings.keys())
    elif i_report_names is not None:
        report_names = i_report_names

        for report_name in report_names:
            if report_name not in MISOReports.report_mappings.keys():
                parser.error(f"Report name '{report_name}' is not valid.")
    else:
        parser.error("Please provide either --all or --report_names.")

    res_string = ""
    for report_name in report_names:
        report = MISOReports.report_mappings[report_name]
        url = report.example_url

        try:
            df = MISOReports.get_df(
                report_name=report_name,
                url=url,
            ) 
        except NotImplementedError as e:
            msg = f"\nReport '{report_name}' is not implemented: {e}\n\n\n"
            
            print(msg)
            res_string += msg

            continue
        
        if df.columns[0] == MULTI_DF_NAMES_COLUMN:
            for table_name, df in zip(df[MULTI_DF_NAMES_COLUMN], df[MULTI_DF_DFS_COLUMN]):            
                new_string = f"""
        Report: {table_name}
    URL: {url}
    {string_format_split_df(df=df, top=i_top, bottom=i_bottom, auto_size=i_auto_size)}
    {string_format_suggestions(df=df, report_name=report_name)}


"""
                res_string += new_string

                if i_print:
                    print(new_string)

        else:
            new_string = f"""
    Report: {report_name}
URL: {url}
{string_format_split_df(df=df, top=i_top, bottom=i_bottom, auto_size=i_auto_size)}
{string_format_suggestions(df=df, report_name=report_name)}


"""
            res_string += new_string

            if i_print:
                print(new_string)
    
    if i_output is not None:
        if i_output == "":
            i_output = "./"

        current_datetime = datetime.datetime.now()
        output_path = os.path.join(
            i_output, 
            f"checker_output_{current_datetime.strftime('%Y%m%d_%H%M%S')}.txt",
        )

        with open(output_path, "w") as f:
            f.write(res_string)

        print(f"Output written to: {output_path}")



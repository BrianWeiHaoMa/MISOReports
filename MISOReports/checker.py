import os
import datetime
import sys
from argparse import ArgumentParser

import pandas as pd
import numpy as np

from MISOReports.MISOReports import MISOReports


def string_format_df_types(
    df: pd.DataFrame,
    auto_size: bool = False,
) -> pd.DataFrame:
    columns = list(df.columns)
    
    dtypes = df.dtypes
    types = []
    for k in dtypes.index:
        types.append(str(type(dtypes[k])))

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
    parser.add_argument("-p", "--print", action="store_true", default=True,  help="Print the output in the terminal.")
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
        
        new_string = f"""
    Report: {report_name}
URL: {url}
{string_format_split_df(df=df, top=i_top, bottom=i_bottom, auto_size=i_auto_size)}

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



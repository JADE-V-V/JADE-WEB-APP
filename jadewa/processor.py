"""Module to process the data and get the plot"""

import json
import logging
import os
import re
from copy import deepcopy
from importlib.resources import as_file, files, path
from io import StringIO
from urllib.error import HTTPError

import numpy as np
import pandas as pd
import requests
from plotly.graph_objects import Figure

import jadewa.resources as res
from jadewa.errors import JsonSettingsError
from jadewa.plotter import get_figure
from jadewa.status import Status
from jadewa.utils import (
    PROTECTED_STRINGS,
    sorting_func,
    string_ints_converter,
)

UNIT_PATTERN = re.compile(r"\[.*\]")


class Processor:
    def __init__(self, status: Status) -> None:
        self.status = status
        # Load the available tallies plot parameters
        resources = files(res)
        self.params = {}
        for file in os.listdir(resources):
            if file.endswith(".json"):
                name = file[:-5]
                with as_file(resources.joinpath(file)) as file:
                    with open(file, "r", encoding="utf-8") as infile:
                        benchmark_params = json.load(infile)
                        self.params[name] = benchmark_params
        # if the tallies are generic, at runtime, new tally configuration must
        # be created
        # check for XX-... general tallies
        # the XX pattern will tell what to ignore and what is the actual tally
        available_benchmarks = self.get_available_benchmarks()
        for benchmark in available_benchmarks:
            try:
                generic = self.params[benchmark]["general"]["generic_tallies"]
            except KeyError:
                generic = False

            if generic:
                # first of all check all possible tallies available across
                # all libraries and codes
                csv_names = []
                for lib, values in self.status.status[benchmark].items():
                    for code, available_csv in values.items():
                        csv_names.extend(available_csv[1])
                csv_names = list(set(csv_names))
                csv_names.sort(key=sorting_func)

                generic_tally_names = list(self.params[benchmark].keys())
                for csv in csv_names:
                    # split only on the first underscore to separate the benchmark
                    # name from the rest
                    pieces = csv.split("_", 1)

                    # now separate the case name from the tally name
                    pieces[-1] = pieces[-1].split(" ", 1)
                    # generic tallies should only be used for benchmarks with cases, so
                    # pieces[0] = benchmark, pieces[1][0] = case name,
                    # pieces[1][1] = tally name
                    pieces = [pieces[0], pieces[-1][0], pieces[-1][1]]
                    # A new ad hoc config tally must be created from the generic
                    for gtally_name in generic_tally_names:
                        # Add the correct general tally
                        if gtally_name != "general":
                            result = self.params[benchmark][gtally_name]["result"]
                            match = False
                            # result can either be a list or a string
                            if isinstance(result, list):
                                # Check if any item in the result list matches the current csv
                                match = pieces[-1][:-4] in result
                            else:
                                match = result == pieces[-1][:-4]
                            if match:
                                gtally_splits = gtally_name.count("{}")
                                # if there are protected substrings, replace them temporarily
                                for orig, temp in PROTECTED_STRINGS.items():
                                    pieces[1] = pieces[1].replace(orig, temp)
                                    gtally_name = gtally_name.replace(orig, temp)
                                split_name = pieces[1].rsplit("-", gtally_splits - 1)
                                total_splits = gtally_name.count("-")
                                # Restore original protected substrings
                                for orig, temp in PROTECTED_STRINGS.items():
                                    gtally_name = gtally_name.replace(temp, orig)
                                    for i, split in enumerate(split_name):
                                        split_name[i] = split_name[i].replace(
                                            temp, orig
                                        )
                                # Substitute empty spaces in gtally_name ("{}")
                                # with the corresponding specific case pieces
                                completed_gtally_name = gtally_name.format(*split_name)
                                if completed_gtally_name not in self.params[benchmark]:
                                    self.params[benchmark][completed_gtally_name] = (
                                        deepcopy(self.params[benchmark][gtally_name])
                                    )
                                # Add the "csv" key only for benchmarks with general tallies,
                                # others retrieve csv names from self.params[benchmark][tally]["result"]
                                if (
                                    "csv"
                                    not in self.params[benchmark][completed_gtally_name]
                                ):
                                    self.params[benchmark][completed_gtally_name][
                                        "csv"
                                    ] = []
                                self.params[benchmark][completed_gtally_name][
                                    "csv"
                                ].append(csv)
                                # Add "tally_options_divisions" for general tallies with
                                # "-" in sub-cases; used when "{}" count in gtally_name
                                # doesn't match "-" count in pieces[1].
                                self.params[benchmark][gtally_name.format(*split_name)][
                                    "tally_options_divisions"
                                ] = gtally_splits + total_splits - 1

                for key in generic_tally_names:
                    if key != "general":
                        self.params[benchmark].pop(key)

    def _get_csv(
        self,
        path: str | os.PathLike,
        csv: str,
    ) -> pd.DataFrame:
        # logic to determine the correct path (local or github)
        if "https" in path:
            path = path + r"/{}"
            formatted_path = (
                path.format(csv)
                .replace(" ", "%20")
                .replace("[", "%5B")
                .replace("]", "%5D")
            )
        else:
            path = path + os.sep + "{}"
            formatted_path = path.format(csv)

        try:
            df = pd.read_csv(formatted_path)
        except Exception:
            df = None
        return df

    def _get_graph_data(
        self,
        benchmark: str,
        reflib: str,
        tally: str,
        refcode: str = "mcnp",
        ratio: bool = False,
        x_vals_to_string: bool = None,
        sum_by: str = None,
        subset: tuple[str, str | list] = None,
    ) -> pd.DataFrame:
        """Get data for a specific graph

        Parameters
        ----------
        benchmark : str
            benchmark name
        reflib : str
            library to be used as reference (e.g. FENDL 2.1)
        tally : str
            tally to be plotted (code).
        refcode : str, optional
            code to be used as reference, by default 'mcnp'
        ratio : bool, optional
            if True, the data will be normalized to the ref-lib and ref-code, by default False
        x_vals_to_string: str, optional
            Columns to convert. The x values will be converted to string, by default False.
            In this process, floats and int representation of integers will be
            converted to the same value.
        sum_by: str, optional
            if provided, the df is groubed by the specified column, sum and
            index is then reserted, by default None.
        subset: tuple[str, str | list], optional
            if provided, the df is filtered by the specified column-value couple, by default None.

        Returns
        -------
        pd.DataFrame
            data for plotting
        """
        # verify that the benchmark-tally combination is supported
        try:
            y_label = self.params[benchmark][tally]["plot_args"]["y"]
        except KeyError as exc:
            raise NotImplementedError(
                f"{benchmark}-{tally} combination not supported"
            ) from exc

        # get all dfs for the different codes-libraries combos
        dfs = []
        for lib, values in self.status.status[benchmark].items():
            for code, (path, csvs) in values.items():
                # locate and read the csv file
                try:
                    csv = self.params[benchmark][tally]["csv"]
                except KeyError:
                    result = self.params[benchmark][tally]["result"]
                    # If result is a list, find all matching csvs
                    if isinstance(result, list):
                        csv = [csv for csv in csvs if csv[:-4] in result]
                    else:
                        csv = [csv for csv in csvs if result == csv[:-4]]
                # If result is a list, more than one csv needs to be considered for the plot
                # Load and concatenate all matching CSVs
                dfs_to_concat = []
                ref_df_concat = []
                for csv_name in csv:
                    df = self._get_csv(
                        path,
                        csv_name,
                    )
                    if df is None:
                        if reflib == lib and refcode == code:
                            raise NotImplementedError(
                                f"Reference data for {reflib}-{refcode} not found. Please, select another library as a reference."
                            )
                        else:
                            continue

                    # Always drop the "total" row if present (check only first col)
                    df = (
                        df.set_index(df.columns[0])
                        .drop("total", errors="ignore")
                        .reset_index()
                    )

                    # Get only a subset of the data if requested
                    if subset:
                        col = subset[0]
                        index = subset[1]
                        # transform the values contained in column col to strings
                        df[col] = list(map(str, df[col]))
                        # keep the subset of the dataframe for which the col column matches the values in index
                        df = df[df[col].isin(np.array(index).flatten())]
                    # Add the label to the df
                    label = f"{lib}-{code}"
                    df["label"] = label

                    # Memorize the reference df to compute ratios
                    if reflib == lib and refcode == code:
                        ref_df = df
                        ref_df_concat.append(ref_df)

                    # if requested, convert x values to string
                    if x_vals_to_string:
                        df = string_ints_converter(df, x_vals_to_string)

                    dfs_to_concat.append(df)

                # Concatenate all dataframes for this tally/lib/code
                if not dfs_to_concat:
                    continue
                df = pd.concat(dfs_to_concat, ignore_index=True)
                if reflib == lib and refcode == code:
                    ref_df = pd.concat(ref_df_concat, ignore_index=True)
                # if the library is exp, it needs to be the first one for
                # better plots
                if lib == "exp":
                    temp = [df]
                    temp.extend(dfs)
                    dfs = temp
                else:
                    dfs.append(df)
        # normalize data to reflib/refcode if requested
        if ratio:
            newdfs = []
            for df in dfs:
                if len(df) == len(ref_df):
                    newdf = df.copy()
                    newdf["Value"] = (
                        newdf["Value"].to_numpy() / ref_df["Value"].to_numpy()
                    )
                    newdf["Error"] = np.sqrt(
                        newdf["Error"].to_numpy() ** 2 + ref_df["Error"].to_numpy() ** 2
                    )  # relative error propagation for ratio
                    newdfs.append(newdf)
        else:
            newdfs = dfs

        newdf = pd.concat(newdfs)

        # Rename columns
        for old, new in self.params[benchmark][tally]["substitutions"].items():
            # if ratio was requested, change y unit
            if ratio and new == y_label:
                if reflib == "exp":
                    new = UNIT_PATTERN.sub("[C/E]", new)
                elif "C/E" in new:
                    new = new.replace("C/E", f"Ratio vs {reflib}-{refcode}")
                else:
                    new = UNIT_PATTERN.sub(f"[ratio vs {reflib}-{refcode}]", new)
            newdf[new] = newdf[old]
            del newdf[old]

        return newdf

    def _get_x_vals_to_string(self, benchmark: str, tally: str) -> str:
        # Check if the x-axis needs to be converted to string
        try:
            # first check if the x ticks are imposed, if not no conversion
            tickmode = self.params[benchmark][tally]["x_axis_format"]["tickmode"]
            if tickmode == "array":
                # then we need to check if the x values columns had originally
                # another name in the csv
                nice_x = self.params[benchmark][tally]["plot_args"]["x"]
                try:
                    subs = self.params[benchmark][tally]["substitutions"]
                    found = False
                    for key, value in subs.items():
                        if nice_x == value:
                            x_vals_to_string = key
                            found = True
                    if not found:
                        x_vals_to_string = nice_x

                except KeyError:
                    x_vals_to_string = nice_x
            else:
                x_vals_to_string = None
        except KeyError:
            x_vals_to_string = None

        return x_vals_to_string

    def _get_optional_config(self, key: str, benchmark: str, tally: str) -> str | bool:
        """helper to get optional configuration from the json file thay may not
        be present"""
        try:
            return self.params[benchmark][tally][key]
        except KeyError:
            return None

    def get_plot(
        self,
        benchmark: str,
        reflib: str,
        refcode: str,
        tally: str,
        ratio: bool = False,
    ) -> Figure:
        """Get a plotly figure for a specific benchmark-tally combination

        Parameters
        ----------
        benchmark : str
            benchmark name
        reflib : str
            library to be used as reference
        refcode : str
            code to be used as reference
        tally : str
            tally to be plotted.
        ratio : bool, optional
            if yes, the data will be normalized to the ref-lib and ref-code, by default False

        Returns
        -------
        Figure
            plotly Figure
        """
        """
        # Recover the tally code
        for key, value in self.params[benchmark].items():
            if key != "general":
                if value["tally_name"] == tally:
                    tally = key
        """

        # check for optional inputs
        x_axis_format = self._get_optional_config("x_axis_format", benchmark, tally)
        y_axis_format = self._get_optional_config("y_axis_format", benchmark, tally)
        only_ratio = self._get_optional_config("only_ratio", benchmark, tally)
        if only_ratio:
            ratio = True  # if only_ratio is set, ratio is forced to True

        # Check if the x-axis needs to be converted to string
        x_vals_to_string = self._get_x_vals_to_string(benchmark, tally)

        data = self._get_graph_data(
            benchmark,
            reflib,
            tally,
            ratio=ratio,
            refcode=refcode,
            x_vals_to_string=x_vals_to_string,
            sum_by=self._get_optional_config("sum_by", benchmark, tally),
            subset=self._get_optional_config("subset", benchmark, tally),
        )
        # Mandatory keys
        try:
            key_args = self.params[benchmark][tally]["plot_args"]
            plot_type = self.params[benchmark][tally]["plot_type"]
        except KeyError as exc:
            raise JsonSettingsError(
                f"Missing mandatory options in {benchmark} {tally}"
            ) from exc

        # be sure to deactivate log if ratio is on
        if ratio:
            key_args["log_y"] = False
            if reflib == "exp":
                key_args["y"] = UNIT_PATTERN.sub("[C/E]", key_args["y"])
            elif "C/E" in key_args["y"]:
                key_args["y"] = key_args["y"].replace(
                    "C/E", f"Ratio vs {reflib}-{refcode}"
                )
            else:
                key_args["y"] = UNIT_PATTERN.sub(
                    f"[ratio vs {reflib}-{refcode}]", key_args["y"]
                )

        # # combine columns before plot (if requested)
        # try:
        #     combine_columns = self.params[benchmark][tally]["combine_columns"]
        #     for key, columns in combine_columns.items():
        #         data[key] = data[columns[0]].astype(str)
        #         for column in columns[1:]:
        #             data[key] = data[key].astype(str) + "-" + data[column].astype(str)
        # except KeyError:
        #     pass

        fig = get_figure(
            plot_type,
            data,
            key_args,
            x_axis_format=x_axis_format,
            y_axis_format=y_axis_format,
        )
        return fig

    def get_available_benchmarks(self) -> list[str]:
        """Get a list of all benchmarks available. To be available, the raw data
        need to be present and a json configuration file should be also present.

        Returns
        -------
        list[str]
            List of all benchmarks available
        """
        raw_data = self.status.get_benchmarks()
        available_config = list(self.params.keys())
        intersection = set(raw_data).intersection(set(available_config))
        return list(intersection)

    def get_available_tallies(
        self, benchmark: str, library: str, code: str
    ) -> list[str]:
        """Cross check which tallies have been run for a given benchmark with
        the ones supported by the plotter.

        Parameters
        ----------
        benchmark : str
            Benchmark name
        library : str
            Library name
        code : str
            Code name

        Returns
        -------
        list[str]
            Path to the results and a list of all files available
        """
        available_csv = self.status.status[benchmark][library][code]
        csv_names = available_csv[1]

        supported = []
        for key, value in self.params[benchmark].items():
            if "result" in value:
                result = value["result"]
                # result can either be a list or a string
                if isinstance(result, list):
                    supported.extend(result)
                else:
                    supported.append(result)
        tally_names = []
        available = []
        for csv in csv_names:
            available.append(csv[:-4])
            csv = csv[:-4].split(" ", 1)
            available.append(csv[-1])
        tallies = list(set(available).intersection(set(supported)))
        tallies.sort(key=sorting_func)
        for tally in tallies:
            for key, value in self.params[benchmark].items():
                if "result" in value:
                    result = value["result"]
                    # result can either be a list or a string
                    if (
                        (isinstance(result, list) and tally in result)
                        or (result == tally)
                    ) and key not in tally_names:
                        tally_names.append(key)

        # Sort options by number of "-" to ensure proper construction of the ctg_dict
        # first, temporarily replace protected substrings
        for i in range(len(tally_names)):
            for orig, temp in PROTECTED_STRINGS.items():
                tally_names[i] = tally_names[i].replace(orig, temp)
        tally_names = sorted(tally_names, key=lambda x: x.count("-"))
        # restore original protected substrings
        for i in range(len(tally_names)):
            for orig, temp in PROTECTED_STRINGS.items():
                tally_names[i] = tally_names[i].replace(temp, orig)

        return tally_names

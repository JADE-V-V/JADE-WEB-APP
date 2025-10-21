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
    GITHUB_HEADERS,
    get_pretty_mat_iso_names,
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
                if benchmark == "SphereSDDR":
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

                    # if SDDR the second piece is a material/isotope and needs
                    # to be translated to something more useful
                    if benchmark == "SphereSDDR":
                        pieces[0] = get_pretty_mat_iso_names([pieces[1]])[0].replace(
                            "-", ""
                        )
                    # A new ad hoc config tally must be created from the generic
                    for gtally_name in generic_tally_names:
                        # Add the correct general tally
                        if (
                            gtally_name != "general"
                            and self.params[benchmark][gtally_name]["result"]
                            == pieces[-1][:-4]
                        ):
                            self.params[benchmark][
                                gtally_name.format(*pieces[1].split("-"))
                            ] = self.params[benchmark][gtally_name]
                            self.params[benchmark][
                                gtally_name.format(*pieces[1].split("-"))
                            ]["csv"] = csv
                for key in generic_tally_names:
                    if key != "general":
                        self.params[benchmark].pop(key)

    def _get_csv(
        self,
        path: str | os.PathLike,
        code: str,
        csv: str,
        isotope_material: bool,
        allow_not_found: bool = False,
    ) -> pd.DataFrame:
        # logic to determine the correct path (local or github)
        if "https" in path:
            path = path + r"/{}"
        else:
            path = path + os.sep + "{}"

        if isotope_material:
            if "https" in path:
                formatted_path = path.format(code + isotope_material).replace(
                    " ", "%20"
                )
            else:
                formatted_path = path.format(code + isotope_material)
        else:
            if "https" in path:
                formatted_path = path.format(csv).replace(" ", "%20")
            else:
                formatted_path = path.format(csv)
        if allow_not_found:
            try:
                if "https" in path:
                    response = requests.get(formatted_path, headers=GITHUB_HEADERS)
                    response.raise_for_status()  # Raise an error for HTTP issues
                    csv_content = StringIO(
                        response.text
                    )  # Convert text to a file-like object
                else:
                    # if the file is local, just read it
                    csv_content = formatted_path
                df = pd.read_csv(csv_content)
            except FileNotFoundError:
                # if everything went well, it means that the isotope
                # or material is not available for this library
                logging.debug("%s not found", formatted_path)
                return None
            except HTTPError:
                # if everything went well, it means that the isotope
                # or material is not available for this library
                logging.debug("%s not found", formatted_path)
                return None
        else:
            df = pd.read_csv(formatted_path)

        return df

    def _get_graph_data(
        self,
        benchmark: str,
        reflib: str,
        tally: str,
        isotope_material: str = None,
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
            library to be used as reference (e.g. FENDL 2.1c)
        tally : str
            tally to be plotted (code).
        isotope_material : str, optional
            isotope or material to be plotted (e.g. 1001), by default None
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
        if benchmark in ["Sphere", "SphereSDDR"]:
            allow = True
        else:
            allow = False
        for lib, values in self.status.status[benchmark].items():
            for code, (path, csvs) in values.items():
                # locate and read the csv file
                try:
                    csv = [self.params[benchmark][tally]["csv"]]
                except KeyError:
                    csv = [
                        csv
                        for csv in csvs
                        if self.params[benchmark][tally]["result"] in csv
                    ]
                df = self._get_csv(
                    path,
                    code,
                    csv[0],
                    isotope_material,
                    allow_not_found=allow,
                )
                if df is None:
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

                # if sum_by is provided, group by the column and sum
                if sum_by:
                    df["abs err"] = df["Value"] * df["Error"]
                    df = df.groupby(sum_by).sum(numeric_only=True).reset_index()
                    df["Error"] = df["abs err"] / df["Value"]

                # Add the label to the df
                label = f"{lib}-{code}"
                df["label"] = label

                # Memorize the reference df to compute ratios
                if reflib == lib and refcode == code:
                    ref_df = df

                # if requested, convert x values to string
                if x_vals_to_string:
                    df = string_ints_converter(df, x_vals_to_string)

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
                newdf = df.copy()
                if len(newdf["Value"]) == len(ref_df["Value"]):
                    newdf["Value"] = (
                        newdf["Value"].to_numpy() / ref_df["Value"].to_numpy()
                    )
                else:
                    # Find the matching key column
                    key_col = None
                    for col in ["Cells", "Energy", "Time"]:
                        if col in newdf.columns and col in ref_df.columns:
                            key_col = col
                            break
                    if key_col is None:
                        raise ValueError(
                            "No matching key column found in both dataframes."
                        )

                    # Merge on the key column, keeping only rows present in both
                    merged = pd.merge(
                        newdf,
                        ref_df[[key_col, "Value"]],
                        on=key_col,
                        suffixes=("", "_ref"),
                    )

                    # Divide the values and keep only matched rows
                    merged["Value"] = merged["Value"] / merged["Value_ref"]

                    # Drop the reference value column
                    merged = merged.drop(columns=["Value_ref"])

                    # Update newdf to be only the merged, matched rows
                    newdf = merged
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

        if isotope_material:
            newdf = newdf[newdf["Tally Description"] == tally]

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
        isotope_material: str = None,
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
        isotope_material : str, optional
            isotope or material to be plotted, by default None
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

        if benchmark == "Sphere":
            iso_mat = isotope_material
        else:
            iso_mat = None

        # Check if the x-axis needs to be converted to string
        x_vals_to_string = self._get_x_vals_to_string(benchmark, tally)

        data = self._get_graph_data(
            benchmark,
            reflib,
            tally,
            isotope_material=iso_mat,
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

        supported = [
            value["result"]
            for key, value in self.params[benchmark].items()
            if "result" in value
        ]
        # general is not part of the supported tallies, needs to be removed

        # Sphere benchmark raw data has a different structure
        if benchmark == "Sphere":
            # get the first available csv file
            if "https" in available_csv[0]:
                path_csv = available_csv[0] + r"/" + csv_names[0] + r"?raw=true"
            else:
                path_csv = os.path.join(available_csv[0], csv_names[0])
            df = pd.read_csv(path_csv)
            return list(
                set(df["Tally Description"].to_list()).intersection(set(supported))
            )

        tally_names = []
        available = []
        for csv in csv_names:
            available.append(csv[:-4])
            csv = csv[:-4].split(" ", 1)
            available.append(csv[-1])
        tallies = list(set(available).intersection(set(supported)))

        if benchmark == "SphereSDDR":
            tallies.sort(key=sorting_func)
        for tally in tallies:
            for key, value in self.params[benchmark].items():
                if "result" in value and value["result"] == tally:
                    tally_names.append(key)
        return tally_names

    def get_available_isotopes_materials(
        self, benchmark: str, library: str, code: str
    ) -> list[str]:
        """Get a list of all isotopes or materials available for a given benchmark, library and code

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
            List of all isotopes or materials available
        """
        available_csv = self.status.status[benchmark][library][code][1]
        available = []
        for csv in available_csv:
            available.append(csv[:-4])

        return available

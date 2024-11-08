"""Module to process the data and get the plot"""

import json
import logging
import os
import re
from copy import deepcopy
from importlib.resources import as_file, files
from urllib.error import HTTPError

import numpy as np
import pandas as pd
from plotly.graph_objects import Figure

import jadewa.resources as res
from jadewa.errors import JsonSettingsError
from jadewa.plotter import get_figure
from jadewa.status import Status
from jadewa.utils import (
    LIB_NAMES,
    get_pretty_mat_iso_names,
    sorting_func_sphere_sddr,
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
                    csv_names.sort(key=sorting_func_sphere_sddr)

                generic_tallies = list(self.params[benchmark].keys())
                for csv in csv_names:
                    if benchmark == "FNS-TOF":
                        pieces = csv.split("-")
                        pieces.append(pieces[1].split(" ")[1])
                        pieces[1] = pieces[1].split(" ")[0]
                    else:
                        pieces = csv.split("_")
                    tally_key = csv[:-4]
                    # if SDDR the first piece is a material/isotope and needs
                    # to be translated to something more useful
                    if benchmark == "SphereSDDR":
                        pieces[0] = get_pretty_mat_iso_names(pieces[:1])[0].replace(
                            "-", ""
                        )

                    # A new ad hoc config tallyt must be created from the generic
                    for gtally in generic_tallies:
                        # Add the correct general tally
                        if gtally == pieces[-1][:-4]:
                            new_config = deepcopy(self.params[benchmark][gtally])
                            new_config["tally_name"] = new_config["tally_name"].format(
                                *pieces[:-1]
                            )
                            self.params[benchmark][tally_key] = new_config
                # in case of SphereSDDR, it is better to sort the tallies

    def _get_csv(
        self,
        path: str | os.PathLike,
        code: str,
        tally: str,
        isotope_material: bool,
        allow_not_found: bool = False,
    ) -> pd.DataFrame:
        # logic to determine the correct path (local or github)
        if "https" in path:
            path = path + r"/{}.csv?raw=true"
        else:
            path = path + os.sep + "{}.csv"

        if isotope_material:
            if "https" in path:
                formatted_path = path.format(code + isotope_material).replace(
                    " ", "%20"
                )
            else:
                formatted_path = path.format(code + isotope_material)
        else:
            if "https" in path:
                formatted_path = path.format(tally).replace(" ", "%20")
            else:
                formatted_path = path.format(tally)

        if allow_not_found:
            try:
                df = pd.read_csv(formatted_path)
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
        compute_lethargy: bool = False,
        compute_per_unit_bin: str = None,
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
            suffix of the library to be used as reference (e.g. 21c)
        tally : str
            tally to be plotted (code).
        isotope_material : str, optional
            isotope or material to be plotted (e.g. 1001), by default None
        refcode : str, optional
            code to be used as reference, by default 'mcnp'
        ratio : bool, optional
            if True, the data will be normalized to the ref-lib and ref-code, by default False
        compute_lethargy: bool, optional
            if True, the data will be converted to lethargy, by default False.
            This is true for every library except "exp" which is
            expected to be in the right format if needed.
        compute_per_unit_bin: str, optional
            column name of the x-axis data used to convert the y-axis data
            to per unit bin (e.g. Energy), by default None
            This is true for every library except "exp" which is
            expected to be in the right format if needed.
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
            for code, (path, _) in values.items():
                # locate and read the csv file
                df = self._get_csv(
                    path, code, tally, isotope_material, allow_not_found=allow
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
                    df[col] = list(map(str, df[col]))
                    df = df[df[col].isin(np.array(index).flatten())]

                # if sum_by is provided, group by the column and sum
                if sum_by:
                    df["abs err"] = df["Value"] * df["Error"]
                    df = df.groupby(sum_by).sum(numeric_only=True).reset_index()
                    df["Error"] = df["abs err"] / df["Value"]

                # Add the label to the df
                label = f"{LIB_NAMES[lib]}-{code}"
                df["label"] = label

                # Memorize the reference df to compute ratios
                if reflib == lib and refcode == code:
                    ref_df = df

                # Compute lethargy or if needed
                if lib != "exp" and (
                    compute_lethargy or compute_per_unit_bin is not None
                ):
                    # Get the bins array, separating the cases by normalization type
                    if compute_lethargy:
                        try:
                            # For lethargy, only energy is valid
                            bins = df["Energy"].astype(float).values
                        except KeyError as exc:
                            raise JsonSettingsError(
                                f"Lethargy cannot be computed for {benchmark} {tally}"
                            ) from exc
                    if compute_per_unit_bin is not None:
                        try:
                            bins = df[compute_per_unit_bin].astype(float).values
                        except KeyError as exc:
                            raise JsonSettingsError(
                                f"Per bin unit normalization cannot be computed for {benchmark} {tally}"
                            ) from exc
                    ergs = [1e-10]  # Additional "zero" bin
                    ergs.extend(bins.tolist())
                    ergs = np.array(ergs)

                    # compute lethargy if requested
                    if compute_lethargy:
                        df["Value"] = df["Value"].values / (
                            np.log(ergs[1:] / ergs[:-1])
                        )

                    # or compute per unit bin if requested
                    elif compute_per_unit_bin:
                        df["Value"] = df["Value"].values / (ergs[1:] - ergs[:-1])

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
                newdf["Value"] = newdf["Value"].to_numpy() / ref_df["Value"].to_numpy()
                newdfs.append(newdf)
        else:
            newdfs = dfs

        newdf = pd.concat(newdfs)

        # Rename columns
        for old, new in self.params[benchmark][tally]["substitutions"].items():
            # if ratio was requested, change y unit
            if ratio and new == y_label:
                new = UNIT_PATTERN.sub(f"[ratio vs {LIB_NAMES[reflib]}]", new)
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
            return False

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
        # Recover the tally code
        for key, value in self.params[benchmark].items():
            if key != "general":
                if value["tally_name"] == tally:
                    tally = key

        # check for optional inputs
        compute_lethargy = self._get_optional_config(
            "compute_lethargy", benchmark, tally
        )
        compute_per_unit_bin = self._get_optional_config(
            "compute_per_unit_bin", benchmark, tally
        )
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
            compute_lethargy=compute_lethargy,
            compute_per_unit_bin=compute_per_unit_bin,
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
            key_args["y"] = UNIT_PATTERN.sub(
                f"[ratio vs {LIB_NAMES[reflib]}]", key_args["y"]
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
            Library suffix (e.g. 21c, 30c, 31c)
        code : str
            Code name

        Returns
        -------
        list[str]
            Path to the results and a list of all files available
        """
        available_csv = self.status.status[benchmark][library][code]
        csv_names = available_csv[1]
        supported = list(self.params[benchmark].keys())
        # general is not part of the supported tallies, needs to be removed
        supported = [i for i in supported if i != "general"]

        # Sphere benchmark raw data has a different structure
        if benchmark == "Sphere":
            # get the first availeble csv file
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
        tallies = list(set(available).intersection(set(supported)))
        if benchmark == "SphereSDDR":
            tallies.sort(key=sorting_func_sphere_sddr)

        for tally in tallies:
            for key, value in self.params[benchmark].items():
                if key == tally:
                    tally_names.append(value["tally_name"])

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

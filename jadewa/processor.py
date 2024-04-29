from jadewa.status import Status
from jadewa.plotter import get_figure
from urllib.error import HTTPError

from plotly.graph_objects import Figure
import pandas as pd
import os
from importlib.resources import files, as_file
import jadewa.resources as res
import json
import re
import logging
from jadewa.utils import LIB_NAMES


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

    def _get_graph_data(
        self,
        benchmark: str,
        reflib: str,
        tally: str,
        isotope_material: str = None,
        refcode: str = "mcnp",
        ratio: bool = False,
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
            for code, (path, _) in values.items():
                if "https" in path:
                    path = path + r"/{}.csv?raw=true"
                else:
                    path = path + os.sep + "{}.csv"

                if isotope_material:
                    formatted_path = path.format(code + isotope_material).replace(
                        " ", "%20"
                    )
                    try:
                        df = pd.read_csv(formatted_path)
                    except FileNotFoundError:
                        # if everything went well, it means that the isotope
                        # or material is not available for this library
                        logging.debug("%s not found", formatted_path)
                        continue
                    except HTTPError:
                        # if everything went well, it means that the isotope
                        # or material is not available for this library
                        logging.debug("%s not found", formatted_path)
                        continue
                else:
                    formatted_path = path.format(tally).replace(" ", "%20")
                    df = pd.read_csv(formatted_path)

                label = f"{LIB_NAMES[lib]}-{code}"
                df["label"] = label
                if reflib == lib and refcode == code:
                    ref_df = df
                dfs.append(df)

        # normalize data to reflib/refcode if requested
        if ratio:
            newdfs = []
            for df in dfs:
                newdf = df.copy()
                newdf["Value"] = newdf["Value"] / ref_df["Value"]
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
            if value["tally_name"] == tally:
                tally = key

        # ratio = self.params[benchmark][tally]["ratio"]
        if benchmark == "Sphere":
            data = self._get_graph_data(
                benchmark,
                reflib,
                tally,
                isotope_material=isotope_material,
                ratio=ratio,
                refcode=refcode,
            )
        else:
            data = self._get_graph_data(
                benchmark, reflib, tally, ratio=ratio, refcode=refcode
            )
        key_args = self.params[benchmark][tally]["plot_args"]
        plot_type = self.params[benchmark][tally]["plot_type"]
        # be sure to deactivate log if ratio is on
        if ratio:
            key_args["log_y"] = False
            key_args["y"] = UNIT_PATTERN.sub(
                f"[ratio vs {LIB_NAMES[reflib]}]", key_args["y"]
            )

        # get some optional parameter
        try:
            x_axis_format = self.params[benchmark][tally]["x_axis_format"]
        except KeyError:
            x_axis_format = None
        try:
            y_axis_format = self.params[benchmark][tally]["y_axis_format"]
        except KeyError:
            y_axis_format = None

        fig = get_figure(
            plot_type,
            data,
            key_args,
            x_axis_format=x_axis_format,
            y_axis_format=y_axis_format,
        )
        return fig

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

        available = []
        for csv in csv_names:
            available.append(csv[:-4])
        tallies = list(set(available).intersection(set(supported)))

        tally_names = []
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

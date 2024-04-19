from jadewa.status import Status
from jadewa.plotter import get_figure

from plotly.graph_objects import Figure
import pandas as pd
import os
from importlib.resources import files, as_file
import jadewa.resources as res
import json
from jadewa.utils import LIB_NAMES

RESOURCES = files(res)


class Processor:
    def __init__(self, status: Status) -> None:
        self.status = status
        # Load the available tallies plot parameters
        with as_file(RESOURCES.joinpath("supported_tallies.json")) as file:
            with open(file, "r", encoding="utf-8") as infile:
                self.params = json.load(infile)

    def _get_graph_data(
        self, benchmark: str, reflib: str, tally: str, isotope_material: str = None
    ) -> pd.DataFrame:
        """Get data for a specific graph

        Parameters
        ----------
        benchmark : str
            benchmark name
        reflib : str
            library to be used as reference
        tally : str
            tally to be plotted (pretty name).
        isotope_material : str, optional
            isotope or material to be plotted, by default None

        Returns
        -------
        pd.DataFrame
            data for plotting
        """

        # verify that the benchmark-tally combination is supported
        try:
            self.params[benchmark][tally]
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
                    try:
                        df = pd.read_csv(path.format(isotope_material))
                    except FileNotFoundError:
                        # if everything went well, it means that the isotope
                        # or material is not available for this library
                        continue
                else:
                    df = pd.read_csv(path.format(tally))
                df["label"] = f"{LIB_NAMES[lib]}-{code}"
                dfs.append(df)
        newdf = pd.concat(dfs)

        # Rename columns
        for old, new in self.params[benchmark][tally]["substitutions"].items():
            newdf[new] = newdf[old]
            del newdf[old]

        if isotope_material:
            newdf = newdf[newdf["Tally Description"] == tally]
        return newdf

    def get_plot(
        self, benchmark: str, reflib: str, tally: str, isotope_material: str = None
    ) -> Figure:
        """Get a plotly figure for a specific benchmark-tally combination

        Parameters
        ----------
        benchmark : str
            benchmark name
        reflib : str
            library to be used as reference
        tally : str
            tally to be plotted.
        isotope_material : str, optional
            isotope or material to be plotted, by default None

        Returns
        -------
        Figure
            plotly Figure
        """
        # Recover the tally code
        for key, value in self.params[benchmark].items():
            if value["tally_name"] == tally:
                tally = key

        if benchmark == "Sphere":
            data = self._get_graph_data(
                benchmark, reflib, tally, isotope_material=isotope_material
            )
        else:
            data = self._get_graph_data(benchmark, reflib, tally)
        key_args = self.params[benchmark][tally]["plot_args"]
        plot_type = self.params[benchmark][tally]["plot_type"]
        fig = get_figure(plot_type, data, key_args)
        return fig

    def get_available_tallies(
        self, benchmark: str, library: str, code: str, pretty: bool = False
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
        pretty : bool, optional
            if True, return the pretty names, by default False

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
        if pretty:
            pretty_tallies = []
            for tally in tallies:
                pretty_tallies.append(self.params[benchmark][tally]["tally_name"])
        else:
            pretty_tallies = tallies
        return pretty_tallies

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

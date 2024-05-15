"""
This module provides a Status class that stores information on available results
and their locations.
"""

from __future__ import annotations
import os
import requests
import pandas as pd
from jadewa.utils import LIB_NAMES


class Status:
    def __init__(
        self,
        status: dict[str, dict[str, dict[str, tuple[str, list[str]]]]],
        metadata_paths: pd.DataFrame = None,
    ) -> None:
        """Store information on what results are available and where.

        Parameters
        ----------
        status : dict[str, dict[str, dict[str, tuple[str, list[str]]]]]
            nested dictionary. First level is benchmark name, second level is
            library and third is code. The value is a tuple with the path to
            the results and a list of all files available.
        metadata_df : pd.DataFrame, optional
            DataFrame with the metadata of the results, by default None.

        Attributes
        ----------
        status : dict[str, dict[str, dict[str, tuple[str, list[str]]]]]
            nested dictionary. First level is benchmark name, second level is
            library and third is code. The value is a tuple with the path to
            the results and a list of all files available.
        metadata_df : pd.DataFrame
            DataFrame containing the metadata of the available results. Since
            it is costly to build due to all the single requests to be made
            to the individual json files, it is initialized as None and built
            only if needed.
        """
        self.status = status
        self.metadata_paths = metadata_paths
        self.metadata_df = None

    def get_metadata_df(self) -> None:
        """Get the metadata from a list of paths

        Parameters
        ----------

        Returns
        -------
        pd.DataFrame
            DataFrame containing the metadata
        """
        metadata_rows = []
        for path in self.metadata_paths:
            r = requests.get(path, timeout=5)
            metadata_rows.append(r.json())

        self.metadata_df = pd.DataFrame(metadata_rows)

    @staticmethod
    def _github_walk(owner: str, repo: str, branch: str = "main"):
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        return data["tree"]

    @classmethod
    def from_github(cls, owner: str, repo: str, branch: str = "main") -> Status:
        """Create a Status object parsing all files contained in a GitHub repository

        Parameters
        ----------
        owner : str
            Owner of the repository
        repo : str
            name of the repository
        branch : str, optional
            branch name, by default 'main'

        Returns
        -------
        Status
            Status object
        """
        # structure in the root directory goes library -> benchmark ->
        # code -> results.

        # First get all last level directories
        allfiles = []
        for i in cls._github_walk(owner, repo, branch):
            path = i["path"]
            filename = os.path.basename(path)
            if filename.endswith(".csv") or filename == "metadata.json":
                allfiles.append(path)

        # create the nested dict for the status
        status = {}
        metadata_paths = []
        start_url = f"https://github.com/{owner}/{repo}/blob/{branch}/"
        for path in allfiles:
            pieces = path.split("/")
            library = pieces[-5]
            benchmark = pieces[-4]
            code = pieces[-3]
            file = pieces[-1]
            # store the .csv files
            if file.endswith(".csv"):
                if benchmark not in status:
                    status[benchmark] = {}
                if library not in status[benchmark]:
                    status[benchmark][library] = {}
                if code not in status[benchmark][library]:
                    rel_path = start_url + os.path.dirname(path)
                    status[benchmark][library][code] = (rel_path, [])
                status[benchmark][library][code][1].append(file)
            if file == "metadata.json":
                json_path = (
                    start_url + os.path.dirname(path) + r"/metadata.json?raw=true"
                )
                # r = requests.get(json_path, timeout=5)
                # metadata_rows.append(r.json())
                metadata_paths.append(json_path)

        # df = pd.DataFrame(metadata_rows)

        return cls(status, metadata_paths)

    @classmethod
    def from_root(cls, root: os.PathLike) -> Status:
        """Create a Status object parsing all files contained in a directory
        tree.

        Parameters
        ----------
        root : os.PathLike
            Path to the root directory

        Returns
        -------
        Status
            Status object
        """
        # structure in the root directory goes library -> benchmark ->
        # code -> results.

        # First get all last level directories
        allfiles = []
        for i in os.walk(root):
            if os.path.basename(i[0]) == "Raw_Data":
                allfiles.append(i)

        # build a flat dict
        status = {}
        for path, _, files in allfiles:
            path = os.path.normpath(path)
            pieces = path.split(os.sep)
            library = pieces[-4]
            benchmark = pieces[-3]
            code = pieces[-2]
            # retain only .csv files
            newfiles = []
            for file in files:
                if file.endswith(".csv"):
                    newfiles.append(file)
            status[benchmark, library, code] = (path, newfiles)

        # unflatten the dict
        nested_status = {}
        for key, value in status.items():
            benchmark, library, code = key
            if benchmark not in nested_status:
                nested_status[benchmark] = {}
            if library not in nested_status[benchmark]:
                nested_status[benchmark][library] = {}

            nested_status[benchmark][library][code] = value

        return cls(nested_status)

    def get_benchmarks(self) -> list[str]:
        """Get a list of all benchmarks available

        Returns
        -------
        list[str]
            List of all benchmarks available
        """
        return list(self.status.keys())

    def get_libraries(self, benchmark: str, pretty: bool = False) -> list[str]:
        """Get a list of all libraries available for a given benchmark

        Parameters
        ----------
        benchmark : str
            Benchmark name
        pretty : bool, optional
            if True, return the pretty names, by default False

        Returns
        -------
        list[str]
            List of all libraries available
        """
        # Use the pretty names
        if pretty:
            libs = []
            for lib in self.status[benchmark].keys():
                libs.append(LIB_NAMES[lib])
        else:
            libs = list(self.status[benchmark].keys())

        return libs

    def get_codes(self, benchmark: str, library: str) -> list[str]:
        """Get a list of all codes available for a given library and benchmark

        Parameters
        ----------
        benchmark : str
            Benchmark name
        library : str
            Library name

        Returns
        -------
        list[str]
            List of all codes available
        """
        return list(self.status[benchmark][library].keys())

    def get_results(
        self, benchmark: str, library: str, code: str
    ) -> tuple[str, list[str]]:
        """Get the path to the results and a list of all files available for a
        given benchmark, library and code

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
        tuple[str, list[str]]
            Path to the results and a list of all files available
        """
        return self.status[benchmark][library][code]

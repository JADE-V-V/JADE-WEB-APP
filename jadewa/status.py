from __future__ import annotations
import os


class Status:
    def __init__(
        self, status: dict[str, dict[str, dict[str, tuple[str, list[str]]]]]
    ) -> None:
        """Store information on what results are available and where

        Parameters
        ----------
        status : dict[str, dict[str, dict[str, tuple[str, list[str]]]]]
            nested dictionary. First level is benchmark name, second level is
            library and third is code.

        Attributes
        ----------
        status : dict[str, dict[str, dict[str, tuple[str, list[str]]]]]
            nested dictionary. First level is benchmark name, second level is
            library and third is code.
        """
        self.status = status

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

    def get_libraries(self, benchmark: str) -> list[str]:
        """Get a list of all libraries available for a given benchmark

        Parameters
        ----------
        benchmark : str
            Benchmark name

        Returns
        -------
        list[str]
            List of all libraries available
        """
        return list(self.status[benchmark].keys())

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

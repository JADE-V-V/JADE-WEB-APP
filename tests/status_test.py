"""Test the status module"""

import os
from importlib.resources import files

import pandas as pd
import pytest

import tests.resources.status as res
from jadewa.status import Status


class StatusMockup(Status):
    def __init__(
        self,
    ) -> None:
        metadata_paths = [
            r"https://github.com/JADE-V-V/JADE-RAW-RESULTS/blob/main/ROOT/00c/ITER_1D/mcnp/Raw_Data/metadata.json?raw=true",
            r"https://github.com/JADE-V-V/JADE-RAW-RESULTS/blob/main/ROOT/32c/FNG-W/mcnp/Raw_Data/metadata.json?raw=true",
        ]
        super().__init__({}, metadata_paths)


class TestStatus:
    """test Status class"""

    @pytest.fixture
    def status(self):
        """Fixture for Status class"""
        return Status.from_root(files(res).joinpath("root"))

    def test_from_root(self, status: Status):
        """Test the from_root method"""
        assert isinstance(status, Status)

    def test_get_benchmarks(self, status: Status):
        """Test the get_benchmarks method"""
        assert "ITER_1D" in status.get_benchmarks()

    def test_get_libraries(self, status: Status):
        """Test the get_libraries method"""
        assert set(status.get_libraries("ITER_1D")) == {"ENDFB-VIII.0", "FENDL 3.2b"}

    def test_get_codes(self, status: Status):
        """Test the get_codes method"""
        assert status.get_codes("ITER_1D", "ENDFB-VIII.0") == ["mcnp"]

    def test_get_results(self, status: Status):
        """Test the get_results method"""
        path, files_res = status.get_results("ITER_1D", "ENDFB-VIII.0", "mcnp")
        assert os.path.exists(os.path.join(path, files_res[0]))
        assert len(files_res) == 6

    def test_from_github(self):
        """Test the from_github method"""
        status = Status.from_github(
            "JADE-V-V", "JADE-RAW-RESULTS", branch="jade_v4_raw_results"
        )
        assert isinstance(status, Status)
        csvs = status.get_results("Sphere", "FENDL 3.2c", "mcnp")
        assert len(csvs[1]) > 100
        path = csvs[0] + "/" + csvs[1][0] + "?raw=true"
        formatted_path = path.replace(" ", "%20")
        assert pd.read_csv(formatted_path) is not None
        assert status.metadata_df is None
        status.get_metadata_df()
        assert len(status.metadata_df) > 1

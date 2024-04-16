"""Test the status module
"""

import os
from importlib.resources import files
import pytest
from jadewa.status import Status
import tests.resources.status as res


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
        assert status.get_benchmarks() == ["ITER_1D", "Sphere"]

    def test_get_libraries(self, status: Status):
        """Test the get_libraries method"""
        assert status.get_libraries("ITER_1D") == ["00c", "32c"]

    def test_get_codes(self, status: Status):
        """Test the get_codes method"""
        assert status.get_codes("ITER_1D", "00c") == ["mcnp"]

    def test_get_results(self, status: Status):
        """Test the get_results method"""
        path, files_res = status.get_results("ITER_1D", "00c", "mcnp")
        assert os.path.exists(os.path.join(path, files_res[0]))
        assert len(files_res) == 23

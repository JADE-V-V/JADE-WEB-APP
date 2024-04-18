from importlib.resources import files
import pytest

from jadewa.processor import Processor
from jadewa.status import Status
import tests.resources.status as res


class TestProcessor:
    """Test Processor class"""

    @pytest.fixture
    def status(self):
        """Fixture for Status class"""
        return Status.from_root(files(res).joinpath("root"))

    @pytest.fixture
    def processor_github(self):
        """Fixture for github processor"""
        return Processor(Status.from_github("JADE-V-V", "JADE-RAW-RESULTS"))

    @pytest.fixture
    def processor(self, status: Status):
        """Fixture for local processor"""
        return Processor(status)

    def test_init(self, status: Status):
        """Test the __init__ method"""
        processor = Processor(status)
        assert isinstance(processor, Processor)
        assert processor.params["ITER_1D"]["204"]["plot_args"]["x"] == "Energy [MeV]"

    def test_get_graph_data(self, processor: Processor):
        """Test the get_graph_data method"""
        data = processor._get_graph_data(
            "ITER_1D",
            "21c",
            "204",
        )
        assert set(data["label"]) == {"32c-mcnp", "00c-mcnp"}
        assert len(data.columns) == 4

        try:
            processor._get_graph_data("ITER2D", "21c", "204")
            processor._get_graph_data("ITER_1D", "21c", "999")
            assert False
        except NotImplementedError:
            assert True

    def test_get_graph_data_github(self):
        """Test the get_graph_data method with github data"""
        processor = Processor(Status.from_github("JADE-V-V", "JADE-RAW-RESULTS"))
        data = processor._get_graph_data(
            "Sphere",
            "32c",
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups",
            isotope_material="mcnp1001",
        )
        # assert set(data["label"]) == {"00c-mcnp", "32c-mcnp"}
        assert len(data.columns) == 6
        assert len(set(data["Tally Description"].to_list())) == 1

    def test_get_graph_data_isotope_material(self, processor: Processor):
        """Test the get_graph_data method with isotope_material"""
        data = processor._get_graph_data(
            "Sphere",
            "00c",
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups",
            isotope_material="1001",
        )
        assert set(data["label"]) == {"00c-mcnp", "32c-mcnp"}
        assert len(data.columns) == 6
        assert len(set(data["Tally Description"].to_list())) == 1

    def test_get_plot(self, processor: Processor):
        """Test the get_plot method"""
        fig = processor.get_plot("ITER_1D", "21c", "204")

    def test_get_available_tallies(self, processor: Processor):
        """Test the get_available_tallies method"""
        assert processor.get_available_tallies("ITER_1D", "00c", "mcnp") == ["204"]

    def test_get_available_tallies_github(self, processor_github: Processor):
        """Test the get_available_tallies method"""
        assert (
            processor_github.get_available_tallies("Sphere", "32c", "mcnp") is not None
        )

    def test_get_available_tallies_sphere(self, processor: Processor):
        """Test the get_available_tallies method specific to the Sphere benchmark"""
        tallies = processor.get_available_tallies("Sphere", "00c", "mcnp")
        assert (
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups"
            in tallies
        )

    def test_get_available_isotopes_materials(self, processor: Processor):
        """Test the get_available_isotopes_materials method"""
        isotopes = processor.get_available_isotopes_materials("Sphere", "32c", "mcnp")
        assert isotopes == ["1001", "2003", "2004"]
from importlib.resources import files

import pytest

import tests.resources.status as res
from jadewa.processor import Processor
from jadewa.status import Status


class MockProcessorParams(Processor):
    def __init__(self, params: dict) -> None:
        self.params = params


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
        assert processor.params["ITER_1D"]["204"]["plot_args"]["x"] == "Cell index"

    def test_init_SphereSDDR(self, status: Status):
        """Test the __init__ method for the SphereSDDR benchmark"""
        processor = Processor(status)
        assert isinstance(processor, Processor)
        assert (
            processor.params["SphereSDDR"]["9019_16_2"]["tally_name"]
            == "F19 - 16 - Neutron Flux at the external surface in VitaminJ 175 energy groups"
        )
        assert len(processor.params["SphereSDDR"]) == 5

    def test_init_FNSTOF(self, status: Status):
        """Test the __init__ method for the FNS-TOF benchmark"""
        processor = Processor(status)
        assert isinstance(processor, Processor)
        assert processor.params["FNS-TOF"]["general"]["generic_tallies"] is True
        assert (
            processor.params["FNS-TOF"]["Be-15 25"]["tally_name"]
            == "Be - 15 cm - 24.9°"
        )
        assert len(processor.params["FNS-TOF"]) == 7

    def test_get_graph_data(self, processor: Processor):
        """Test the get_graph_data method"""
        data = processor._get_graph_data(
            "ITER_1D", "21c", "204", subset=("Cells", ["2.0", "3.0"])
        )
        assert set(data["label"]) == {"ENDFB VIII.0-mcnp", "FENDL 3.2b-mcnp"}
        assert len(data.columns) == 4

        data = processor._get_graph_data(
            "Oktavian",
            "exp",
            "Al 21",
            subset=("Energy", "0.10109"),
        )
        assert len(data[data["label"] == "FENDL 3.2b-mcnp"]) == 1

        try:
            # processor._get_graph_data("ITER2D", "21c", "204")
            processor._get_graph_data("ITER_1D", "21c", "999")
            assert False
        except NotImplementedError:
            assert True

    def test_get_graph_data_ratio(self, processor: Processor):
        """Test the get_graph_data method with ratio"""
        data = processor._get_graph_data(
            "ITER_1D",
            "32c",
            "204",
            ratio=True,
        )
        assert set(data["label"]) == {"ENDFB VIII.0-mcnp", "FENDL 3.2b-mcnp"}
        assert len(data.columns) == 4
        assert data.groupby("label").mean().iloc[-1][-1] == 1

    def test_get_graph_data_ratio_lethargy(self, processor: Processor):
        """Test the get_graph_data method with lethargy"""
        data = processor._get_graph_data(
            "Oktavian",
            "exp",
            "Al 21",
            compute_lethargy=True,
        )
        assert len(data[data["label"] == "FENDL 3.2b-mcnp"]) == 134

    def test_get_graph_data_unit_per_bin(self, processor: Processor):
        """Test the get_graph_data method with unit per bin normalization"""
        data = processor._get_graph_data(
            "TUD-Fe",
            "exp",
            "A0 15",
            compute_per_unit_bin="Time",
        )
        assert len(data[data["label"] == "ENDFB VIII.0-mcnp"]) == 136

    def test_get_graph_data_github(self):
        """Test the get_graph_data method with github data"""
        processor = Processor(Status.from_github("JADE-V-V", "JADE-RAW-RESULTS"))
        data = processor._get_graph_data(
            "Sphere",
            "32c",
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups",
            isotope_material="1001",
        )
        # assert set(data["label"]) == {"00c-mcnp", "32c-mcnp"}
        assert len(data.columns) == 6
        assert len(set(data["Tally Description"].to_list())) == 1

        # check that there are no problems in getting a path with a space
        data = processor._get_graph_data(
            "FNG-SDDR",
            "99c",
            "FNG1 4",
            ratio=True,
            refcode="d1s",
        )
        assert len(data.columns) == 4

    def test_get_graph_data_isotope_material(self, processor: Processor):
        """Test the get_graph_data method with isotope_material"""
        data = processor._get_graph_data(
            "Sphere",
            "00c",
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups",
            isotope_material="1001",
        )
        assert set(data["label"]) == {
            "ENDFB VIII.0-mcnp",
            "FENDL 3.2b-mcnp",
            "ENDFB VIII.0-openmc",
        }
        assert len(data.columns) == 6
        assert len(set(data["Tally Description"].to_list())) == 1

    @pytest.mark.parametrize("ratio", [True, False])
    def test_get_plot(self, processor: Processor, ratio: bool):
        """Test the get_plot method"""
        fig = processor.get_plot(
            "Sphere",
            "00c",
            "mcnp",
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups",
            ratio=ratio,
            isotope_material="1001",
        )

    def test_get_plot_subset(self, processor: Processor):
        """Test the get_plot method with a subset of tallies"""
        fig = processor.get_plot(
            "C_Model",
            "00c",
            "mcnp",
            "Neutron current on plasma boundary - (inboard BLK#1 to #6)",
        )

    def test_get_available_benchmarks(self, processor: Processor):
        """Test the get_available_benchmarks method"""
        assert "random" not in processor.get_available_benchmarks()

    def test_get_available_tallies(self, processor: Processor):
        """Test the get_available_tallies method"""
        assert len(processor.get_available_tallies("ITER_1D", "00c", "mcnp")) == 5

    def test_get_available_sddr_tallies(self, processor: Processor):
        """Test the get_available_tallies method"""
        assert (
            processor.get_available_tallies("SphereSDDR", "99c", "d1s")[0]
            == "F19 - 16 - Neutron Flux at the external surface in VitaminJ 175 energy groups"
        )

    def test_get_available_tallies_github(self, processor_github: Processor):
        """Test the get_available_tallies method"""
        assert (
            processor_github.get_available_tallies("Sphere", "32c", "mcnp") is not None
        )

    def test_get_available_tallies_sphere(self, processor: Processor):
        """Test the get_available_tallies method specific to the Sphere benchmark"""
        tallies = processor.get_available_tallies("Sphere", "00c", "openmc")
        assert (
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups"
            in tallies
        )

    def test_get_available_isotopes_materials(self, processor: Processor):
        """Test the get_available_isotopes_materials method"""
        isotopes = processor.get_available_isotopes_materials("Sphere", "32c", "mcnp")
        assert set(isotopes) == set(["mcnp1001", "mcnp2003", "mcnp2004"])

    @pytest.mark.parametrize(
        ["x", "substitutions", "tickmode", "expected"],
        [
            ["A", {"B": "A"}, "array", "B"],
            ["A", {"B": "A"}, None, None],
            ["A", {"B": "C"}, "array", "A"],
        ],
    )
    def test_get_x_vals_to_string(
        self, x: str, substitutions: dict, tickmode: str, expected: str
    ):
        params = {
            "benchmark": {
                "tally": {
                    "x_axis_format": {"tickmode": tickmode},
                    "plot_args": {"x": x},
                    "substitutions": substitutions,
                },
            }
        }
        mock_processor = MockProcessorParams(params)
        assert expected == mock_processor._get_x_vals_to_string("benchmark", "tally")

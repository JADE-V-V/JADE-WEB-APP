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
        return Processor(
            Status.from_github(
                "JADE-V-V", "JADE-RAW-RESULTS", branch="jade_v4_raw_results"
            )
        )

    @pytest.fixture
    def processor(self, status: Status):
        """Fixture for local processor"""
        return Processor(status)

    def test_init(self, status: Status):
        """Test the __init__ method"""
        processor = Processor(status)
        assert isinstance(processor, Processor)
        # Check that ITER_1D params are loaded (even if no matching test data)
        assert "ITER_1D" in processor.params
        assert "Neutron flux" in processor.params["ITER_1D"]
        assert (
            processor.params["ITER_1D"]["Neutron flux"]["plot_args"]["x"]
            == "Radial position [cm]"
        )

    def test_init_SphereSDDR(self, status: Status):
        """Test the __init__ method for the SphereSDDR benchmark"""
        processor = Processor(status)
        assert isinstance(processor, Processor)
        # SphereSDDR uses generic tallies, check that it's configured
        assert "SphereSDDR" in processor.params
        assert "general" in processor.params["SphereSDDR"]
        assert processor.params["SphereSDDR"]["general"]["generic_tallies"] is True

    def test_init_FNSTOF(self, status: Status):
        """Test the __init__ method for the FNS-TOF benchmark"""
        processor = Processor(status)
        assert isinstance(processor, Processor)
        assert processor.params["FNS-TOF"]["general"]["generic_tallies"] is True
        # Check that the tally was properly generated from CSV
        assert "Be - 5 cm - 24.9°" in processor.params["FNS-TOF"]
        print(len(processor.params["FNS-TOF"]))
        assert len(processor.params["FNS-TOF"]) == 2

    def test_get_graph_data(self, processor: Processor):
        """Test the get_graph_data method"""
        # Test with Oktavian which has actual test data
        data = processor._get_graph_data(
            "Oktavian",
            "exp",
            "Ti - Photon leakage spectrum",
        )
        assert "FENDL 3.2b-mcnp" in set(data["label"])
        assert "exp-exp" in set(data["label"])
        assert len(data.columns) == 4

        # Test that non-existent tally raises error
        with pytest.raises((NotImplementedError, KeyError)):
            processor._get_graph_data("Oktavian", "exp", "NonExistentTally")

    def test_get_graph_data_ratio(self, processor: Processor):
        """Test the get_graph_data method with ratio"""
        # Use FENDL 3.2b as reference since we have that data for Oktavian
        data = processor._get_graph_data(
            "Oktavian",
            "FENDL 3.2b",
            "Ti - Photon leakage spectrum",
            refcode="mcnp",
            ratio=True,
        )
        assert "FENDL 3.2b-mcnp" in set(data["label"])
        assert "exp-exp" in set(data["label"])
        assert len(data.columns) == 4
        # Check that reference data (FENDL 3.2b-mcnp) has ratio of 1
        ref_data = data[data["label"] == "FENDL 3.2b-mcnp"]
        # Get the value column (last column after label, which is the Y-axis data)
        value_col_name = data.columns[-1]
        # The ratio values for the reference should be 1
        assert ref_data[value_col_name].mean() == 1

    def test_get_graph_data_TBM(self, processor: Processor):
        """Test the get_graph_data method for the TBM benchmarks"""
        data = processor._get_graph_data(
            "HCPB_TBM_1D",
            "FENDL 3.2b",
            "Neutron flux",
        )
        assert len(data[data["label"] == "FENDL 3.2b-mcnp"]) == 79

        data = processor._get_graph_data(
            "WCLL_TBM_1D",
            "FENDL 3.2b",
            "Neutron flux",
        )
        assert len(data[data["label"] == "FENDL 3.2b-mcnp"]) == 79

    def test_get_graph_data_c_model(self, processor: Processor):
        """Test the get_graph_data method with C-Model which has subset configuration"""
        data = processor._get_graph_data(
            "C-Model",
            "ENDFB-VIII.0",
            "Neutron current on plasma boundary - Collided",
        )
        assert len(data[data["label"] == "ENDFB-VIII.0-mcnp"]) == 36

    def test_get_graph_data_tud_fe(self, processor: Processor):
        """Test the get_graph_data method with TUD-Fe"""
        data = processor._get_graph_data(
            "TUD-Fe",
            "ENDFB-VIII.0",
            "A0 - Neutron fluence (time binned)",
        )
        assert len(data[data["label"] == "ENDFB-VIII.0-mcnp"]) > 0

    def test_get_graph_data_github(self):
        """Test the get_graph_data method with github data"""
        processor = Processor(
            Status.from_github(
                "JADE-V-V", "JADE-RAW-RESULTS", branch="jade_v4_raw_results"
            )
        )
        data = processor._get_graph_data(
            "Sphere",
            "FENDL 3.2c",
            "1001_H-1 - Neutron Flux at the external surface in Vitamin-J 175 energy groups",
        )
        assert len(data.columns) == 4
        assert len(set(data["Neutron flux [n/cm^2/s]"].to_list())) == 1006

        data = processor._get_graph_data(
            "C-Model",
            "ENDFB-VIII.0",
            "Neutron current on plasma boundary - Collided",
            refcode="mcnp",
        )
        assert len(data.columns) == 6

    def test_get_plot(self, processor: Processor):
        """Test the get_plot method"""
        # Test with Oktavian which has actual data
        fig = processor.get_plot(
            "Oktavian",
            "exp",
            "exp",
            "Ti - Photon leakage spectrum",
            ratio=False,
        )
        assert fig is not None

        # Test with ratio
        fig = processor.get_plot(
            "Oktavian",
            "exp",
            "exp",
            "Ti - Photon leakage spectrum",
            ratio=True,
        )
        assert fig is not None

    def test_get_plot_subset(self, processor: Processor):
        """Test the get_plot method with C-Model which has subset configuration"""
        fig = processor.get_plot(
            "C-Model",
            "ENDFB-VIII.0",
            "mcnp",
            "Neutron current on plasma boundary - Collided",
        )
        assert fig is not None

    def test_get_available_benchmarks(self, processor: Processor):
        """Test the get_available_benchmarks method"""
        benchmarks = processor.get_available_benchmarks()
        assert "random" not in benchmarks
        # Check that some expected benchmarks are present
        assert "Oktavian" in benchmarks
        assert "FNS-TOF" in benchmarks

    def test_get_available_tallies(self, processor: Processor):
        """Test the get_available_tallies method"""
        # Use Oktavian which has actual test data
        tallies = processor.get_available_tallies("Oktavian", "exp", "exp")
        assert len(tallies) == 21
        assert "Ti - Photon leakage spectrum" in tallies

    def test_get_available_sddr_tallies(self, processor: Processor):
        """Test the get_available_tallies method for SDDR benchmarks"""
        tallies = processor.get_available_tallies("FNG-SDDR", "exp", "exp")
        assert len(tallies) > 0
        # Check that at least one campaign tally is available
        assert any("campaign" in tally for tally in tallies)

    def test_get_available_tallies_fns_tof(self, processor: Processor):
        """Test the get_available_tallies method for FNS-TOF benchmark"""
        tallies = processor.get_available_tallies("FNS-TOF", "ENDFB-VIII.0", "mcnp")
        assert len(tallies) > 0
        assert "Be - 5 cm - 24.9°" in tallies

    def test_get_available_tallies_github(self, processor_github: Processor):
        """Test the get_available_tallies method"""
        assert (
            processor_github.get_available_tallies("FNG-W", "FENDL 3.2c", "mcnp")
            is not None
        )

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

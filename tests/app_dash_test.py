from jadewa.app_dash import (
    update_lib_dropdown,
    update_isotope_material,
    update_tally_dropdown,
    update_graph,
)
from plotly.graph_objects import Figure


class TestApp:
    """Test applications callbacks"""

    def test_update_lib_dropdown(self, mocker):
        """Test update_lib_dropdown"""
        libraries = ["00c", "31c"]
        mocker.patch(
            "jadewa.app.status.get_libraries",
            return_value=libraries,
        )

        assert update_lib_dropdown("Sphere") == libraries
        assert not update_lib_dropdown(None)

    def test_update_isotope_material(self, mocker):
        """Test update_isotope_material"""
        isotopes = ["U235", "U238"]
        mocker.patch(
            "jadewa.app.processor.get_available_isotopes_materials",
            return_value=isotopes,
        )

        assert update_isotope_material("00c", "Sphere") == isotopes
        assert not update_isotope_material("31c", None)
        assert not update_isotope_material(None, "as")

    def test_update_tally_dropdown(self, mocker):
        """Test update_tally_dropdown"""
        tallies = ["1", "2"]
        mocker.patch(
            "jadewa.app.processor.get_available_tallies",
            return_value=tallies,
        )

        assert update_tally_dropdown("Sphere", "00c") == tallies
        assert not update_tally_dropdown("31c", None)
        assert not update_tally_dropdown(None, "as")

    def test_update_graph(self, mocker):
        """Test update_graph"""
        mocker.patch(
            "jadewa.app.processor.get_plot",
            return_value=Figure(),
        )

        assert update_graph("Sphere", "00c", "1", "U235")
        assert not update_graph("Sphere", "00c", "1", None)
        assert update_graph("ITER1D", "00c", "2", None)
        assert update_graph("ITER1D", "as", None, None) == {}

import pytest
from streamlit.testing.v1 import AppTest

from app_streamlit import _recursive_assign_na_option


class TestStreamlitApp:
    """Test the Streamlit app. Better to reunite all tests in one class to avoid
    multiple executions of the app."""

    def test_all_app(self):
        """
        Test needs to be put together since the initialization of the app can
        take quite some time
        """
        # Selection of the benchmarks is greater than 1
        app = AppTest("app_streamlit.py", default_timeout=45).run()
        assert len(app.selectbox(key="benchmark_0").options) > 1

        # Test the ratio plot.
        assert app.radio.values == ["Ratio"]

        # Test the selection of library options by checking if the selected value
        # matches the expected value and if "FENDL 3.2b" is in the available options.
        app.selectbox(key="benchmark_0").select("Sphere").run()
        assert app.selectbox(key="benchmark_0").value == "Sphere"
        assert "FENDL 3.2b" in app.selectbox(key="lib").options

        # Test an experiment
        app.selectbox(key="benchmark_0").select("Oktavian").run()
        assert set(app.selectbox(key="lib").options) == {
            "Experiment",
            "FENDL 2.1",
            "FENDL 3.1d",
            "FENDL 3.2b",
            "FENDL 3.2c",
            "ENDFB-VIII.0",
            "JEFF-3.3",
        }

        # Test the selection of tally options by checking if the selected values
        # match the expected values.
        app.selectbox(key="benchmark_0").select("Sphere").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        app.selectbox(key="isotope or material_0").select("1001_H-1 ").run()
        assert (
            " Neutron Flux at the external surface in Vitamin-J 175 energy groups"
            in app.selectbox(key="Tally_1001_H-1 ").options
        )

        # Test the selection of tally options by checking if the selected values
        # match the expected values and if a KeyError is raised when selecting the
        # "isotope" option.
        app.selectbox(key="benchmark_0").select("ITER_1D").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        app.selectbox(key="code").select("mcnp").run()
        assert len(app.selectbox(key="tally").options) == 5
        try:
            app.selectbox(key="isotope")
            assert False
        except KeyError:
            assert True

        # Test the plot by checking if the image is not None.
        app.selectbox(key="benchmark_0").select("ITER_1D").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        app.selectbox(key="tally").select("Neutron flux").run()

        # Test the sphere plot.
        app.selectbox(key="benchmark_0").select("Sphere").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        # app.selectbox(key="code").select("openmc").run()
        app.selectbox(key="isotope or material_0").select("1001_H-1 ").run()
        assert app.selectbox(key="Tally_1001_H-1 ").disabled is False
        assert len(app.selectbox(key="Tally_1001_H-1 ").options) > 1
        app.selectbox(key="Tally_1001_H-1 ").select(
            " Neutron Flux at the external surface in Vitamin-J 175 energy groups"
        ).run()

        # Test a benchmark that requires the selection of more than one selectbox.
        app.selectbox(key="benchmark_0").select("ASPIS").run()
        assert app.selectbox(key="benchmark_0").value == "ASPIS"
        app.selectbox(key=" _ASPIS").select("Fe88").run()
        assert app.selectbox(key=" _ASPIS").value == "Fe88"

        # Test the library checkboxes by selecting and deselecting one and
        # checking if it matches the expected bool values.
        app.checkbox(key="JEFF-3.3").check().run()
        assert app.checkbox(key="JEFF-3.3").value is True
        app.checkbox(key="JEFF-3.3").uncheck().run()
        assert app.checkbox(key="JEFF-3.3").value is False

        # Check the correct functioning of the _recursive_assign_na_option function
        dict_test = _recursive_assign_na_option(
            {
                "benchmark": {
                    "benchmark_1.1": {"benchmark_1.2": ["benchmark_1.3"]},
                    "benchmark_2.1": ["benchmark_2.2", "benchmark_2.3"],
                },
            },
            max_depth=4,
        )
        assert dict_test == {
            "benchmark": {
                "benchmark_1.1": {"benchmark_1.2": ["benchmark_1.3"]},
                "benchmark_2.1": {"benchmark_2.2": ["N.A."], "benchmark_2.3": ["N.A."]},
            }
        }

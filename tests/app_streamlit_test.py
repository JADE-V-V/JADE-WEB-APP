from streamlit.testing.v1 import AppTest
import pytest

from app_streamlit import _recursive_assign_na_option


class TestStreamlitApp:
    """Test the Streamlit app. Better to reunite all tests in one class to avoid
    multiple executions of the app."""

    @pytest.mark.skip(reason="Requires GitHub authentication - run manually with credentials")
    def test_all_app(self):
        """
        Test needs to be put toghether since the initialization of the app can
        take quite some time
        """
        # Selection of the benchmarks is greater than 1
        app = AppTest("app_streamlit.py", default_timeout=45).run()
        assert len(app.selectbox(key="benchmark").options) > 1

        # Test the ratio plot.
        assert app.radio.values == ["Ratio"]

        # Test the selection of library options by checking if the selected value
        # matches the expected value and if "FENDL 3.2b" is in the available options.
        app.selectbox(key="benchmark").select("Sphere").run()
        assert app.selectbox(key="benchmark").value == "Sphere"
        assert "FENDL 3.2b" in app.selectbox(key="lib").options

        # Test an experiment
        app.selectbox(key="benchmark").select("Oktavian").run()
        assert app.selectbox(key="lib").options == ["experiment"]

        # Test the selection of tally options by checking if the selected values
        # match the expected values.
        app.selectbox(key="benchmark").select("Sphere").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        app.selectbox(key="isotope").select("H-1").run()
        assert (
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups"
            in app.selectbox(key="tally").options
        )

        # Test the selection of tally options by checking if the selected values
        # match the expected values and if a KeyError is raised when selecting the
        # "isotope" option.
        app.selectbox(key="benchmark").select("ITER_1D").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        assert len(app.selectbox(key="tally").options) == 5
        try:
            app.selectbox(key="isotope")
            assert False
        except KeyError:
            assert True

        # Test the plot by checking if the image is not None.
        app.selectbox(key="benchmark").select("ITER_1D").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        app.selectbox(key="tally").select("Neutron Flux").run()

        # Test the sphere plot.
        app.selectbox(key="benchmark").select("Sphere").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        # app.selectbox(key="code").select("openmc").run()
        app.selectbox(key="isotope").select("H-1").run()
        assert app.selectbox(key="tally").disabled is False
        assert len(app.selectbox(key="tally").options) > 1
        app.selectbox(key="tally").select(
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups"
        ).run()

        # Test a benchmark that requires the selection of more than one selectbox.
        app.selectbox(key="benchmark").select("ASPIS").run()
        assert app.selectbox(key="benchmark").value == "ASPIS"
        app.selectbox(key="benchmark_1").select("Fe88").run()
        assert app.selectbox(key="benchmark_1").value == "Fe88"

        # Test the library checkboxes by selecting and deselecting one and
        # checking if it matches the expected bool values.
        app.checkbox(key="JEFF 3.3").check().run()
        assert app.checkbox(key="JEFF 3.3").value is True
        app.checkbox(key="JEFF 3.3").uncheck().run()
        assert app.checkbox(key="JEFF 3.3").value is False

        # Check the correct functioning of the _recursive_assign_na_option function
        dict_test = _recursive_assign_na_option(
            {"benchmark": {"benchmark_1": {"benchmark_2": ["benchmark_3"]}}}
        )
        assert dict_test == {
            "benchmark": {"benchmark_1": {"benchmark_2": {"benchmark_3": ["N.A."]}}}
        }

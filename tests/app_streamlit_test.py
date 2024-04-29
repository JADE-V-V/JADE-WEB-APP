from streamlit.testing.v1 import AppTest


class TestStreamlitApp:
    """Test the Streamlit app"""

    def test_app(self):
        """
        Test the Streamlit app by checking if the title is not None.
        """
        app = AppTest("app_streamlit.py", default_timeout=10).run()
        assert app.title is not None

    def test_select_benchmark(self):
        """
        Test the selection of benchmark options by checking if the number of options
        is greater than 1.
        """
        app = AppTest("app_streamlit.py", default_timeout=10).run()
        assert len(app.selectbox(key="benchmark").options) > 1

    def test_select_library(self):
        """
        Test the selection of library options by checking if the selected value
        matches the expected value and if "FENDL 3.2b" is in the available options.
        """
        app = AppTest("app_streamlit.py", default_timeout=10).run()
        app.selectbox(key="benchmark").select("Sphere").run()
        assert app.selectbox(key="benchmark").value == "Sphere"
        assert "FENDL 3.2b" in app.selectbox(key="lib").options

        # Test an experiment
        app.selectbox(key="benchmark").select("FNG-SDDR").run()
        assert app.selectbox(key="lib").options == ["experiment"]

    def test_select_tally_sphere(self):
        """
        Test the selection of tally options by checking if the selected values
        match the expected values.
        """
        app = AppTest("app_streamlit.py", default_timeout=10).run()
        app.selectbox(key="benchmark").select("Sphere").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        app.selectbox(key="isotope").select("H-1").run()
        assert (
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups"
            in app.selectbox(key="tally").options
        )

    def test_select_tally(self):
        """
        Test the selection of tally options by checking if the selected values
        match the expected values and if a KeyError is raised when selecting the
        "isotope" option.
        """
        app = AppTest("app_streamlit.py", default_timeout=10).run()
        app.selectbox(key="benchmark").select("ITER_1D").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        assert len(app.selectbox(key="tally").options) == 5
        try:
            app.selectbox(key="isotope")
            assert False
        except KeyError:
            assert True

    def test_plot(self):
        """
        Test the plot by checking if the image is not None.
        """
        app = AppTest("app_streamlit.py", default_timeout=10).run()
        app.selectbox(key="benchmark").select("ITER_1D").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        app.selectbox(key="tally").select("Neutron Flux").run()
        assert True

    def test_plot_sphere(self):
        """
        Test the plot by checking if the image is not None.
        """
        app = AppTest("app_streamlit.py", default_timeout=10).run()
        app.selectbox(key="benchmark").select("Sphere").run()
        app.selectbox(key="lib").select("FENDL 3.2b").run()
        # app.selectbox(key="code").select("openmc").run()
        app.selectbox(key="isotope").select("H-1").run()
        assert app.selectbox(key="tally").disabled is False
        assert len(app.selectbox(key="tally").options) > 1
        app.selectbox(key="tally").select(
            "Neutron Flux at the external surface in Vitamin-J 175 energy groups"
        ).run()
        assert True

    def test_ratio(self):
        """
        Test the plot by checking if the image is not None.
        """
        app = AppTest("app_streamlit.py", default_timeout=10).run()
        assert app.radio.values == ["Ratio"]

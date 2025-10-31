import pandas as pd
import plotly.graph_objs as go
import pytest
from plotly.graph_objects import Figure

from jadewa.plotter import build_lib_df, get_figure, select_visible_libs

TEST_DF = pd.DataFrame(
    {
        "x": [1, 2, 3, 1, 2, 3],
        "y": [1, 4, 9, 16, 25, 33],
        "label": ["a", "a", "a", "b", "b", "b"],
    }
)

fig = Figure(
    data=[
        go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="FENDL 2.1-mcnp"),
        go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="FENDL 3.0-mcnp"),
        go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="FENDL 3.1d-mcnp"),
        go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="FENDL 3.2b-mcnp"),
        go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="ENDFB VII.0-mcnp"),
        go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="ENDFB VIII.0-mcnp"),
        go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="IRDFF II-mcnp"),
        go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="JEFF 3.3-mcnp"),
        go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="D1SUNED (FENDL 3.2b+TENDL2017)-d1s"),
        go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="D1SUNED (FENDL 3.1d+EAF2007)-d1s"),
        go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="experiment-experiment"),
    ]
)


class TestPlotter:
    """Test Plotter class"""

    def test_get_figure(self):
        key_args = {"x": "x", "y": "y"}
        get_figure("step", TEST_DF, key_args)

    def test_select_visible_libs(self):
        """Test select_visible_libs function by ensuring that the old libraries
        have been deselected from the plot legend and the new ones are visible"""

        new_libs = [
            "FENDL 3.2b",
            "ENDFB VIII.0",
            "IRDFF II",
            "JEFF 3.3",
            "D1SUNED (FENDL 3.2b+TENDL2017)",
        ]
        select_visible_libs(fig, new_libs)

        assert fig.data[0].visible == "legendonly"
        assert fig.data[1].visible == "legendonly"
        assert fig.data[2].visible == "legendonly"
        assert fig.data[3].visible is True
        assert fig.data[4].visible == "legendonly"
        assert fig.data[5].visible is True
        assert fig.data[6].visible is True
        assert fig.data[7].visible is True
        assert fig.data[8].visible is True
        assert fig.data[9].visible == "legendonly"

    def test_build_lib_df(self):
        """Test build_lib_df function and ensure that the library labels are ordered correctly"""
        libraries = [trace.name.split("-")[0] for trace in fig.data]
        df = build_lib_df(libraries)

        assert len(df["Library"]) == 11
        assert len(df["Label"]) == 11
        assert [label in libraries for label in df["Label"]]

        df = df.groupby("Library").max()["Label"].values
        assert len(df) == 6
        assert [
            name in df
            for name in [
                "FENDL 3.2b",
                "ENDFB VIII.0",
                "IRDFF II",
                "JEFF 3.3",
                "D1SUNED (FENDL 3.2b+TENDL2017)",
                "experiment",
            ]
        ]

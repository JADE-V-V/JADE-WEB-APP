import pandas as pd
import plotly.graph_objs as go
import pytest
from plotly.graph_objects import Figure

from jadewa.plotter import _deselect_old_libs, get_figure

TEST_DF = pd.DataFrame(
    {
        "x": [1, 2, 3, 1, 2, 3],
        "y": [1, 4, 9, 16, 25, 33],
        "label": ["a", "a", "a", "b", "b", "b"],
    }
)


class TestPlotter:
    """Test Plotter class"""

    def test_get_figure(self):
        key_args = {"x": "x", "y": "y"}
        get_figure("step", TEST_DF, key_args)

    def test_deselect_old_libs(self):
        """Test _deselect_old_libs function and ensure that the old libraries
        have been deselected from the plot legend and the new ones are visible"""

        fig = Figure()
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="FENDL 2.1c-mcnp"))
        fig.add_trace(go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="FENDL 3.0-mcnp"))
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="FENDL 3.1d-mcnp"))
        fig.add_trace(go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="FENDL 3.2b-mcnp"))
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="ENDFB VII.0-mcnp"))
        fig.add_trace(go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="ENDFB VIII.0-mcnp"))
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="IRDFF II-mcnp"))
        fig.add_trace(go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="JEFF 3.3-mcnp"))
        fig.add_trace(
            go.Scatter(
                x=[1, 2, 3], y=[4, 5, 6], name="D1SUNED (FENDL 3.2b+TENDL2017)-d1s"
            )
        )
        fig.add_trace(
            go.Bar(x=[1, 2, 3], y=[4, 5, 6], name="D1SUNED (FENDL 3.1d+EAF2007)-d1s")
        )
        fig.add_trace(
            go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name="experiment-experiment")
        )

        _deselect_old_libs(fig)

        assert fig.data[0].visible == "legendonly"
        assert fig.data[1].visible == "legendonly"
        assert fig.data[2].visible == "legendonly"
        assert fig.data[3].visible is None
        assert fig.data[4].visible == "legendonly"
        assert fig.data[5].visible is None
        assert fig.data[6].visible is None
        assert fig.data[7].visible is None
        assert fig.data[8].visible is None
        assert fig.data[9].visible == "legendonly"

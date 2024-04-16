import pytest
from jadewa.plotter import get_figure
import pandas as pd


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

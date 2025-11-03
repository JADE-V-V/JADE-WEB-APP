import pandas as pd
import pytest

from jadewa.utils import (
    find_dict_depth,
    get_info_dfs,
    safe_add_ctg_to_dict,
    sorting_func,
    string_ints_converter,
)


class TestUtils:
    """Test the utility functions"""

    def test_sorting_func(self):
        """Test the sorting_func function with only material strings"""
        options = [
            "98254_Cf-254",
            "1002_H-2",
            "M901_Polyethylene-(non-borated)",
            "30068_Zn-68",
        ]
        # Expected: materials sorted by number, then isotopes sorted by number
        sorted_options = sorted(options, key=sorting_func)
        assert sorted_options == [
            "M901_Polyethylene-(non-borated)",
            "1002_H-2",
            "30068_Zn-68",
            "98254_Cf-254",
        ]

    def test_string_ints_converter(self):
        """Test the string_ints_converter function"""
        df = pd.DataFrame(
            [
                {"A": "1", "B": 1},
                {"A": "4.0", "B": 1},
                {"A": 1.0, "B": 1},
                {"A": "a string", "B": 1},
            ]
        )
        df = string_ints_converter(df, "A")
        expected = ["1", "4", "1", "a string"]
        for i, value in enumerate(df["A"].values):
            assert value == expected[i]

        # check that if it is numerin nothing is touched
        df = pd.DataFrame(
            [
                {"A": 1, "B": 1},
                {"A": 4.0, "B": 1},
            ]
        )
        df = string_ints_converter(df, "A")
        for value in df["A"].values:
            assert not isinstance(value, str)

    @pytest.mark.parametrize(
        ["dictionary", "expected_nested"],
        [
            [{"B": "A", "S": {"C": "D"}}, 2],
            [{}, 1],
            [{"B": "C"}, 1],
        ],
    )
    def test_find_dict_depth(self, dictionary, expected_nested):
        """Test the find_dict_depth function"""
        assert find_dict_depth(dictionary) == expected_nested

    def test_safe_add_ctg_to_dict(self):
        """Test the safe_add_ctg_to_dict function"""
        dictionary = {}
        safe_add_ctg_to_dict(dictionary, ["A", "B", "C"], "D")
        assert dictionary["A"]["B"]["C"] == ["D"]

        dictionary = {"A": {"B": {"C": ["D"]}}}
        safe_add_ctg_to_dict(dictionary, ["A", "B", "C"], "E")
        assert dictionary["A"]["B"]["C"] == ["D", "E"]

        safe_add_ctg_to_dict(dictionary, ["A", "B", "X"], "E")
        assert dictionary["A"]["B"]["X"] == ["E"]
        assert list(dictionary["A"]["B"].keys()) == ["C", "X"]

    def test_get_info_dfs(self):
        """Test the get_info_dfs function"""
        # Create a simple metadata DataFrame
        data = [
            {"benchmark_name": "B1", "library": "L1", "code": "C1", "Available": True},
            {"benchmark_name": "B1", "library": "L2", "code": "C1", "Available": True},
            {"benchmark_name": "B2", "library": "L1", "code": "C2", "Available": False},
            {"benchmark_name": "B3", "library": "L3", "code": "d1s", "Available": True},
        ]
        df = pd.DataFrame(data)
        sorted_df, df_sddr, df_no_sddr = get_info_dfs(df)
        # Check that sorted_df is a DataFrame and has the correct index
        assert isinstance(sorted_df, pd.DataFrame)
        assert list(sorted_df.index.names) == ["benchmark_name", "library", "code"]
        # Check that df_sddr and df_no_sddr are DataFrames
        assert isinstance(df_sddr, pd.DataFrame)
        assert isinstance(df_no_sddr, pd.DataFrame)

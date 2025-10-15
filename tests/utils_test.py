import pandas as pd
import pytest

from jadewa.utils import (
    find_dict_depth,
    get_mat_iso_code,
    get_pretty_mat_iso_names,
    safe_add_ctg_to_dict,
    string_ints_converter,
)


class TestUtils:
    """Test the utility functions"""

    def test_get_pretty_mat_iso_names(self):
        """Test the get_pretty_mat_iso_names function"""
        names = ["10001", "1001", "M900"]
        pretty_names = get_pretty_mat_iso_names(names)
        assert pretty_names == ["Natural Silicon", "H-1", "Ne-1"]
        for pretty_name, code in zip(pretty_names, names):
            assert get_mat_iso_code(pretty_name) == code

    def test_get_mat_iso_code(self):
        """Test the get_mat_iso_code function"""
        names = ["Natural Silicon", "H-1", "Ne-1"]
        codes = ["M900", "1001", "10001"]
        for name, code in zip(names, codes):
            assert get_mat_iso_code(name) == code

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

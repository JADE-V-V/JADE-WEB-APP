from jadewa.utils import (
    get_pretty_mat_iso_names,
    get_mat_iso_code,
    get_lib_suffix,
    get_pretty_lib_names,
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

    def test_get_pretty_lib_names(self):
        """Test the get_pretty_lib_names function"""
        names = ["21c", "30c", "31c"]
        pretty_names = get_pretty_lib_names(names)
        assert pretty_names == ["FENDL 2.1c", "FENDL 3.0", "FENDL 3.1d"]
        for pretty_name, code in zip(pretty_names, names):
            assert get_lib_suffix(pretty_name) == code

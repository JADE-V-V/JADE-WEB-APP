from jadewa.utils import get_pretty_mat_iso_names, get_mat_iso_code


class TestUtils:
    """Test the utility functions"""

    def test_get_pretty_mat_iso_names(self):
        """Test the get_pretty_mat_iso_names function"""
        names = ["mcnp10001", "mcnp1001", "mcnpM900"]
        pretty_names = get_pretty_mat_iso_names(names)
        assert pretty_names == ["Natural Silicon", "H-1", "Ne-1"]
        for pretty_name, code in zip(pretty_names, names):
            assert get_mat_iso_code(pretty_name) == code

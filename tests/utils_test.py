from jadewa.utils import get_pretty_mat_iso_names, get_mat_iso_code


class TestUtils:
    """Test the utility functions"""

    def test_get_pretty_mat_iso_names(self):
        """Test the get_pretty_mat_iso_names function"""
        names = ["mcnp1001", "M900"]
        pretty_names = get_pretty_mat_iso_names(names)
        assert pretty_names == ["H-1", "Natural Silicon"]
        for pretty_name, code in zip(pretty_names, names):
            assert get_mat_iso_code(pretty_name) == code

from jadewa.app import update_lib_dropdown


class TestApp:
    """Test applications callbacks"""

    def test_update_lib_dropdown(self, mocker):
        """Test update_lib_dropdown"""
        libraries = ["00c", "31c"]
        mocker.patch(
            "jadewa.app.status.get_libraries",
            return_value=libraries,
        )

        assert update_lib_dropdown("Sphere") == libraries

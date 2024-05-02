"""Custom errors for the web app
"""


class JsonSettingsError(Exception):
    """Exception raised due to an error in the json settings file."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

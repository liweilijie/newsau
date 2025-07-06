import importlib

class Settings:
    def __init__(self, module_name="settings"):
        """
        Load settings from the specified module.
        :param module_name: The name of the settings module (default: "settings").
        """
        self.settings_module = importlib.import_module(module_name)

    def get(self, name, default=None):
        """
        Get a single setting value.
        :param name: The setting name.
        :param default: The default value if the setting is not found.
        :return: The setting value or the default.
        """
        return getattr(self.settings_module, name, default)

    def getdict(self, name):
        """
        Get a setting as a dictionary.
        :param name: The setting name.
        :return: The dictionary value of the setting.
        :raises TypeError: If the setting is not a dictionary.
        """
        value = self.get(name)
        if isinstance(value, dict):
            return value
        raise TypeError(f"Setting '{name}' is not a dictionary")

    def getbool(self, name, default=False):
        """
        Get a boolean setting.
        :param name: The setting name.
        :param default: The default value if not found.
        :return: Boolean representation of the setting.
        """
        value = self.get(name, default)
        return bool(value)

    def getint(self, name, default=0):
        """
        Get an integer setting.
        :param name: The setting name.
        :param default: The default integer value.
        :return: Integer representation of the setting.
        """
        value = self.get(name, default)
        return int(value)

    def keys(self):
        """
        Get all setting names (only uppercase variables).
        :return: A list of setting names.
        """
        return [attr for attr in dir(self.settings_module) if attr.isupper()]

    def items(self):
        """
        Get all settings as a dictionary.
        :return: A dictionary containing all settings.
        """
        return {key: self.get(key) for key in self.keys()}
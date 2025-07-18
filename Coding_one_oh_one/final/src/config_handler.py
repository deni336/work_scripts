# src/config_handler.py

import configparser
import os
import sys
import getpass

DEFAULT_CONFIG = {
    'Logging': {
        'path': 'logs/',
        'loglevel': 'INFO'
    },
    'Database': {
        'dbpath': 'index.db',
    },
    'Application': {
       'mode': 'cli',  # 'cli' or 'gui'
    }
}

def get_default_config_path():
    user = getpass.getuser()
    base_dir = os.path.join(os.path.expanduser("~"), "ToDoList")
    config_file = os.path.join(base_dir, "config.ini")
    return config_file

def get_default_base_path():
    user = getpass.getuser()
    base_dir = os.path.join(os.path.expanduser("~"), "ToDoList")
    return base_dir

class ConfigHandler:
    def __init__(self, config_file=None):
        self.config_file = config_file or get_default_config_path()
        self.config = configparser.ConfigParser()

        if not os.path.exists(self.config_file):
            self._write_default_config()
        else:
            self.config.read(self.config_file)
            self._ensure_all_defaults_exist()

    def _write_default_config(self):
        self.config.read_dict(DEFAULT_CONFIG)
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        print(f"Created default config at {self.config_file}")

    def _ensure_all_defaults_exist(self):
        updated = False
        for section, options in DEFAULT_CONFIG.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
                updated = True
            for key, val in options.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, val)
                    updated = True
        if updated:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            print("Config updated with missing defaults.")

    def as_dict(self) -> dict:
        """
        Return the entire configuration as a nested dict:
        {
            'Section1': {'optionA': 'valueA', 'optionB': 'valueB', …},
            'Section2': { … },
            …
        }
        """
        result = {}
        for section in self.config.sections():
            # config.items(section) returns a list of (option, value)
            result[section] = dict(self.config.items(section))
        return result

    def get(self, section, option, fallback=None):
        try:
            return self.config.get(section, option, fallback=fallback).strip(',').strip()
        except configparser.NoOptionError:
            return fallback

    def getint(self, section, option, fallback=None):
        try:
            return self.config.getint(section, option, fallback=fallback)
        except (ValueError, configparser.NoOptionError):
            return fallback

    def getfloat(self, section, option, fallback=None):
        try:
            return self.config.getfloat(section, option, fallback=fallback)
        except (ValueError, configparser.NoOptionError):
            return fallback

    def set(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def set_float(self, section, option, value):
        if not isinstance(value, float):
            raise ValueError("Value must be a float.")
        self.set(section, option, str(value))

    def set_config(self, config_data):
        for section, options in config_data.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for option, value in options.items():
                self.config.set(section, option, str(value))
        with open(self.config_file, 'w') as f:
            self.config.write(f)
import json
import os
import sys

CONFIG_FILE = 'config.json'

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_config():
    """Loads configuration from config.json."""
    config_path = resource_path(CONFIG_FILE)
    if not os.path.exists(config_path):
        # Fallback for dev environment if not found in PyInstaller temp
        if os.path.exists(CONFIG_FILE):
             config_path = CONFIG_FILE
        else:
            raise FileNotFoundError(f"Configuration file '{CONFIG_FILE}' not found. Please copy 'config.example.json' to '{CONFIG_FILE}' and configure it.")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing '{CONFIG_FILE}': {e}")
    except Exception as e:
         raise Exception(f"Unexpected error loading config: {e}")

def get_service_account_path(config):
    """Resolves the service account file path from config."""
    path = config.get('service_account_file', 'service_account.json')
    # If absolute, return as is. If relative, make it relative to the executable/script location
    if os.path.isabs(path):
        return path
    return resource_path(path)

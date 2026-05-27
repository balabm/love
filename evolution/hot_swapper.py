import importlib
import sys
import logging

def reload_module(module_path_string: str) -> bool:
    try:
        if module_path_string in sys.modules:
            importlib.reload(sys.modules[module_path_string])
        else:
            importlib.import_module(module_path_string)
        return True
    except Exception as e:
        logging.error(f"Failed to reload {module_path_string}: {e}")
        return False

import importlib
from typing import Any


def get_class(module_path: str, class_name: str) -> Any:
    """
    Dynamically imports a class from a given module path.
    """
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ModuleNotFoundError, AttributeError) as e:
        raise ImportError(f"Failed to import class '{class_name}' from module '{module_path}': {e}")

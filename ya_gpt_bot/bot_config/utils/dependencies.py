"""Dependency-related utilities are defined here."""
import importlib


def load_class(class_full_name: str):
    """Load class by its full-name.

    >>> load_class("math.sqrt")
    <built-in function sqrt>
    """
    module_path, class_name = class_full_name.rsplit(".", 1)
    module = importlib.import_module(module_path)
    if hasattr(module, class_name):
        return getattr(module, class_name)
    raise ImportError(f"Could not import {class_full_name} class")

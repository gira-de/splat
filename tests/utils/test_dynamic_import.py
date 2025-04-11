import unittest
from unittest.mock import MagicMock, patch

from splat.utils.plugin_initializer.dynamic_import import get_class


class TestDynamicImport(unittest.TestCase):
    @patch("splat.utils.plugin_initializer.dynamic_import.importlib.import_module")
    def test_get_class_imports_valid_class_successfully(self, mock_import_module: MagicMock) -> None:
        # Setup
        mock_module = MagicMock()
        mock_class = MagicMock()
        mock_import_module.return_value = mock_module
        mock_module.SomeClass = mock_class

        # Test valid module and class
        result = get_class("some.module", "SomeClass")
        mock_import_module.assert_called_once_with("some.module")
        self.assertEqual(result, mock_class)

    @patch("splat.utils.plugin_initializer.dynamic_import.importlib.import_module")
    def test_get_class_raises_module_not_found_error_for_invalid_module(self, mock_import_module: MagicMock) -> None:
        # Setup to raise ModuleNotFoundError
        mock_import_module.side_effect = ModuleNotFoundError("No module named 'invalid.module'")

        # Test invalid module path
        with self.assertRaises(ImportError):
            get_class("invalid.module", "SomeClass")
        mock_import_module.assert_called_once_with("invalid.module")

    @patch("splat.utils.plugin_initializer.dynamic_import.importlib.import_module")
    def test_get_class_raises_attribute_error_for_invalid_class(self, mock_import_module: MagicMock) -> None:
        # Setup
        mock_module = MagicMock()
        mock_import_module.return_value = mock_module

        # Ensure the class does not exist in the module
        del mock_module.SomeClass

        # Test valid module but invalid class name
        with self.assertRaises(ImportError):
            get_class("some.module", "SomeClass")
        mock_import_module.assert_called_once_with("some.module")

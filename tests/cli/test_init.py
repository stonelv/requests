"""
Tests for __init__.py module.
"""

import pytest
from requests.cli import main
from requests.cli.__init__ import __all__


class TestCLIInit:
    """Test cases for CLI module initialization."""
    
    def test_main_function_import(self):
        """Test that main function can be imported."""
        # Should not raise any import errors
        from requests.cli import main as imported_main
        assert imported_main is not None
        assert callable(imported_main)
    
    def test___all___contains_main(self):
        """Test that __all__ list contains main function."""
        assert "main" in __all__
        assert len(__all__) == 1  # Only main should be exported
    
    def test_module_docstring(self):
        """Test that module has docstring."""
        import requests.cli
        assert requests.cli.__doc__ is not None
        assert "rhttp CLI tool" in requests.cli.__doc__
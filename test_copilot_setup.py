#!/usr/bin/env python3
"""
Test script to verify .gitattributes configuration for Copilot PR access.

This script verifies that data files are properly marked as linguist-generated
to prevent them from bloating PR diffs and affecting Copilot's ability to
access PR metadata.
"""

import subprocess
import sys
from pathlib import Path


def check_gitattributes(filepath: str, expected_value: str = "true") -> tuple[bool, str]:
    """Check if a file has the linguist-generated attribute set.
    
    Returns:
        tuple: (success: bool, message: str) indicating if the check passed and details
    """
    try:
        result = subprocess.run(
            ["git", "check-attr", "linguist-generated", filepath],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        # Expected format: "filepath: linguist-generated: value"
        parts = output.split(": ")
        if len(parts) == 3:
            actual_value = parts[2]
            success = actual_value == expected_value
            msg = f"actual={actual_value}" if not success else ""
            return success, msg
        return False, f"unexpected format: {output}"
    except subprocess.CalledProcessError as e:
        return False, f"git error: {e.stderr}"
    except Exception as e:
        return False, f"error: {str(e)}"


def main():
    """Run tests to verify gitattributes configuration."""
    print("Testing .gitattributes configuration for Copilot PR access...")
    print("=" * 70)
    
    tests = [
        ("data/test.html", "true", "Data HTML files should be linguist-generated"),
        ("data/index.json", "true", "Data JSON files should be linguist-generated"),
        ("test_urls.txt", "true", "Test URL files should be linguist-generated"),
        (".gitattributes", "unspecified", "Config files should not be linguist-generated"),
        ("README.md", "unspecified", "Documentation should not be linguist-generated"),
    ]
    
    passed = 0
    failed = 0
    
    for filepath, expected, description in tests:
        result, message = check_gitattributes(filepath, expected)
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {description}")
        print(f"       File: {filepath} (expected: {expected})")
        if message:
            print(f"       Info: {message}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Please check .gitattributes configuration.")
        return 1
    else:
        print("\n✅ All tests passed! Copilot should now be able to access PR diffs.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Test cases for rhttp config_loader module."""
import unittest
import tempfile
import os
import yaml
from requests.cli.config_loader import load_config, interpolate_variables


class TestConfigLoader(unittest.TestCase):
    """Test cases for config_loader module functions."""

    def test_load_config_basic(self):
        """Test loading a basic configuration file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'requests': [
                    {'url': 'http://example.com'},
                    {'url': 'http://example.org'}
                ]
            }, f)

        # Load config
        config = load_config(f.name)

        # Assertions
        self.assertIn('requests', config)
        self.assertEqual(len(config['requests']), 2)
        self.assertEqual(config['requests'][0]['url'], 'http://example.com')
        self.assertEqual(config['requests'][1]['url'], 'http://example.org')

        # Cleanup
        os.unlink(f.name)

    def test_load_config_with_variables(self):
        """Test loading a configuration file with variables."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'variables': {
                    'base_url': 'http://example.com',
                    'api_version': 'v1'
                },
                'requests': [
                    {'url': '${base_url}/api/${api_version}/users'},
                    {'url': '${base_url}/api/${api_version}/posts'}
                ]
            }, f)

        # Load config
        config = load_config(f.name)

        # Assertions
        self.assertIn('variables', config)
        self.assertEqual(config['variables']['base_url'], 'http://example.com')
        self.assertEqual(config['variables']['api_version'], 'v1')
        self.assertIn('requests', config)
        self.assertEqual(len(config['requests']), 2)

        # Cleanup
        os.unlink(f.name)

    def test_interpolate_variables(self):
        """Test interpolating variables in requests."""
        config = {
            'variables': {
                'base_url': 'http://example.com',
                'api_version': 'v1',
                'token': 'abc123'
            },
            'requests': [
                {
                    'method': 'GET',
                    'url': '${base_url}/api/${api_version}/users',
                    'headers': {
                        'Authorization': 'Bearer ${token}'
                    }
                },
                {
                    'method': 'POST',
                    'url': '${base_url}/api/${api_version}/posts',
                    'json': {
                        'title': 'Test Post',
                        'content': 'This is a test post for ${api_version}'
                    }
                }
            ]
        }

        # Interpolate variables
        interpolated_requests = interpolate_variables(config)

        # Assertions
        self.assertEqual(len(interpolated_requests), 2)
        
        # First request
        req1 = interpolated_requests[0]
        self.assertEqual(req1['method'], 'GET')
        self.assertEqual(req1['url'], 'http://example.com/api/v1/users')
        self.assertEqual(req1['headers']['Authorization'], 'Bearer abc123')
        
        # Second request
        req2 = interpolated_requests[1]
        self.assertEqual(req2['method'], 'POST')
        self.assertEqual(req2['url'], 'http://example.com/api/v1/posts')
        self.assertEqual(req2['json']['content'], 'This is a test post for v1')

    def test_interpolate_variables_missing(self):
        """Test interpolating variables when some are missing."""
        config = {
            'variables': {
                'base_url': 'http://example.com'
            },
            'requests': [
                {
                    'url': '${base_url}/api/${api_version}/users'
                }
            ]
        }

        # Interpolate variables
        interpolated_requests = interpolate_variables(config)

        # Assertions
        self.assertEqual(len(interpolated_requests), 1)
        req = interpolated_requests[0]
        self.assertEqual(req['url'], 'http://example.com/api//users')  # Empty string for missing variable

    def test_load_config_missing_requests(self):
        """Test loading a configuration file missing requests list."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'variables': {
                    'base_url': 'http://example.com'
                }
            }, f)

        # Load config should raise ValueError
        with self.assertRaises(ValueError):
            load_config(f.name)

        # Cleanup
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()

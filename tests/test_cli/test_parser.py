# -*- coding: utf-8 -*-
"""Test cases for rhttp parser module."""
import argparse
import sys
import unittest
from requests.cli.parser import create_parser, parse_args, parse_headers, parse_auth


class TestParser(unittest.TestCase):
    """Test cases for parser module functions."""

    def test_create_parser(self):
        """Test that parser is created with correct arguments."""
        parser = create_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        
        # Check common arguments
        self.assertIn('url', [action.dest for action in parser._actions])
        self.assertIn('method', [action.dest for action in parser._actions])
        self.assertIn('header', [action.dest for action in parser._actions])
        self.assertIn('data', [action.dest for action in parser._actions])
        self.assertIn('json', [action.dest for action in parser._actions])
        self.assertIn('file', [action.dest for action in parser._actions])
        self.assertIn('auth', [action.dest for action in parser._actions])
        self.assertIn('bearer', [action.dest for action in parser._actions])
        self.assertIn('timeout', [action.dest for action in parser._actions])
        self.assertIn('retries', [action.dest for action in parser._actions])
        self.assertIn('retry_backoff', [action.dest for action in parser._actions])
        self.assertIn('save', [action.dest for action in parser._actions])
        self.assertIn('show', [action.dest for action in parser._actions])
        self.assertIn('color', [action.dest for action in parser._actions])
        
        # Check batch argument
        self.assertIn('batch', [action.dest for action in parser._actions])

    def test_parse_args_single_request(self):
        """Test parsing arguments for single request mode."""
        test_args = [
            'http://example.com',
            '-X', 'POST',
            '-H', 'Content-Type: application/json',
            '-H', 'Authorization: Bearer token123',
            '--data', 'param1=value1&param2=value2',
            '--json', '{"key": "value"}',
            '--file', 'test.txt',
            '--auth', 'user:pass',
            '--bearer', 'token456',
            '--timeout', '10',
            '--retries', '3',
            '--retry-backoff', '2',
            '--save', 'response.txt',
            '--show', 'all',
            '--no-color'
        ]
        args = parse_args(test_args)
        
        self.assertEqual(args.url, 'http://example.com')
        self.assertEqual(args.method, 'POST')
        self.assertEqual(args.header, ['Content-Type: application/json', 'Authorization: Bearer token123'])
        self.assertEqual(args.data, 'param1=value1&param2=value2')
        self.assertEqual(args.json, '{"key": "value"}')
        self.assertEqual(args.file, 'test.txt')
        self.assertEqual(args.auth, 'user:pass')
        self.assertEqual(args.bearer, 'token456')
        self.assertEqual(args.timeout, 10.0)
        self.assertEqual(args.retries, 3)
        self.assertEqual(args.retry_backoff, 2.0)
        self.assertEqual(args.save, 'response.txt')
        self.assertEqual(args.show, 'all')
        self.assertEqual(args.color, False)
        self.assertIsNone(args.batch)

    def test_parse_args_batch_mode(self):
        """Test parsing arguments for batch mode."""
        test_args = ['--batch', 'config.yaml', '--timeout', '5']
        args = parse_args(test_args)
        
        self.assertIsNone(args.url)
        self.assertEqual(args.batch, 'config.yaml')
        self.assertEqual(args.timeout, 5.0)

    def test_parse_headers(self):
        """Test parsing headers from list of strings."""
        header_list = [
            'Content-Type: application/json',
            'Authorization: Bearer token123',
            'User-Agent: rhttp/1.0'
        ]
        headers = parse_headers(header_list)
        
        self.assertEqual(headers, {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token123',
            'User-Agent': 'rhttp/1.0'
        })

    def test_parse_headers_invalid(self):
        """Test parsing headers with invalid format."""
        header_list = [
            'InvalidHeader',
            'Content-Type: application/json'
        ]
        headers = parse_headers(header_list)
        
        self.assertEqual(headers, {
            'Content-Type': 'application/json'
        })

    def test_parse_auth(self):
        """Test parsing authentication string."""
        # With password
        auth_str = 'user:pass'
        user, password = parse_auth(auth_str)
        self.assertEqual(user, 'user')
        self.assertEqual(password, 'pass')
        
        # Without password
        auth_str = 'user'
        user, password = parse_auth(auth_str)
        self.assertEqual(user, 'user')
        self.assertEqual(password, '')


if __name__ == '__main__':
    unittest.main()

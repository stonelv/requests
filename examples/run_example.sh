#!/bin/bash

# Example script to run reqcheck

# Basic usage: Check URLs and export to CSV
python3 -m reqcheck --urls examples/urls.txt --output results.csv

# Advanced usage: Check URLs with custom headers and export to JSON
python3 -m reqcheck --urls examples/urls.txt --output results.json --headers examples/headers.json --verbose

# Download mode: Save responses to downloads directory
python3 -m reqcheck --urls examples/urls.txt --download --download-dir downloads --concurrency 5
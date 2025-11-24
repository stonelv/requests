import sys
import os
print("Current working directory:", os.getcwd())
print("Python path:", sys.path)

# Try importing TimingAdapter and check its module
import requests.timing.adapter
print("requests.timing.adapter module path:", requests.timing.adapter.__file__)
from requests.timing import TimingAdapter
print("TimingAdapter module:", TimingAdapter.__module__)
print("TimingAdapter class:", TimingAdapter)
print("TimingAdapter attributes:", dir(TimingAdapter))

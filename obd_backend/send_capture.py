import json, sys
from capture import post_capture

with open(sys.argv[1]) as f:
    post_capture(json.load(f))
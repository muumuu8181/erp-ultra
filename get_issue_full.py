import urllib.request
import json
import sys

try:
    url = "https://api.github.com/repos/muumuu8181/erp-ultra/issues/7"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print(data['body'])
except Exception as e:
    print(f"Error fetching issue: {e}", file=sys.stderr)

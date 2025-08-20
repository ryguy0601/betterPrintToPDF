import json
import sys
from customSiteCode import *

# Print JSON to stdout so .NET can capture it
print(json.dumps(sites))
sys.stdout.flush()

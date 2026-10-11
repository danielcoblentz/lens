import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# the lambdas are deployed as separate zips, so each function directory is its
# own import root rather than a package.
for function_dir in ("LlamaParse", "LlamaQuery"):
    sys.path.insert(0, os.path.join(BACKEND_DIR, function_dir))

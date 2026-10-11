import importlib.util
import os
import sys

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# the lambdas are deployed as separate zips, so each function directory is its
# own import root rather than a package
for function_dir in ("LlamaParse", "LlamaQuery"):
    sys.path.insert(0, os.path.join(BACKEND_DIR, function_dir))


@pytest.fixture
def load_handler(monkeypatch):
    """load a function's lambda_function module with the env vars it reads at import

    every function has a module named lambda_function, so each one is loaded by
    path under its own name instead of through sys.path
    """
    def load(function_dir, **env):
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        for name, value in env.items():
            monkeypatch.setenv(name, value)

        path = os.path.join(BACKEND_DIR, function_dir, "lambda_function.py")
        spec = importlib.util.spec_from_file_location(f"{function_dir.lower()}_handler", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return load

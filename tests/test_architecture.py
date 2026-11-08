"""The one rule that lets five people work in parallel: modules share ONLY the contract.
No module may import another module. Shared helpers must not import modules either."""
import ast
import os

import pytest

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lumasync")
MODULES = ["m1_audio", "m2_lighting", "m3_rhythm", "m4_superposition", "m5_recognition"]


def imports_of(path):
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module


@pytest.mark.parametrize("mod", MODULES)
def test_module_imports_no_other_module(mod):
    folder = os.path.join(ROOT, mod)
    for fn in os.listdir(folder):
        if fn.endswith(".py"):
            for name in imports_of(os.path.join(folder, fn)):
                for other in MODULES:
                    if other != mod:
                        assert other not in name, f"{mod}/{fn} imports {name}"


@pytest.mark.parametrize("fn", ["contract.py", "fakes.py", "audiofile.py"])
def test_shared_files_import_no_module(fn):
    for name in imports_of(os.path.join(ROOT, fn)):
        assert not any(m in name for m in MODULES), f"{fn} imports {name}"

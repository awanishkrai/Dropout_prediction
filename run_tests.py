
import pytest
import sys
import os

# Redirect stdout/stderr to a file
with open("test_results.log", "w", encoding="utf-8") as f:
    sys.stdout = f
    sys.stderr = f
    
    print("Running tests...")
    retcode = pytest.main(["-v", "tests"])
    print(f"Tests finished with code: {retcode}")

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

print("Done. Check test_results.log")

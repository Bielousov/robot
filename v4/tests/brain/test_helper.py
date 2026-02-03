import sys
import os
from pathlib import Path

def setup_test_env():
    """
    Ensures the project root is in sys.path regardless of 
    where the test script is executed from.
    """
    # Navigate from v4/tests/test_helper.py -> v4 -> root
    # Adjust '.parent' count based on where you place this helper
    project_root = Path(__file__).resolve().parent.parent.parent
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Change working directory to root so relative file loading works
    os.chdir(project_root)
    
    return project_root
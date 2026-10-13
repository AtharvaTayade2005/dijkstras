"""
main.py
-------
Entry point for the Dijkstra Network Explorer application.
Run with:
    python main.py
"""

import sys
import os

# Add local directory to path to ensure clean imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui_main import launch

if __name__ == "__main__":
    launch()

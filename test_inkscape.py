#!/usr/bin/env python3
"""
Simple test script to detect Inkscape installation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from inkscape_mcp.inkscape_detector import InkscapeDetector

def main():
    detector = InkscapeDetector()
    path = detector.detect_inkscape_installation()

    if path:
        print(f"✅ Inkscape found at: {path}")

        # Test if it's actually executable
        import subprocess
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Inkscape version: {result.stdout.strip()}")
            else:
                print(f"❌ Failed to get version: {result.stderr}")
        except Exception as e:
            print(f"❌ Failed to run Inkscape: {e}")
    else:
        print("❌ Inkscape not found")
        print("Please install Inkscape from: https://inkscape.org/")

if __name__ == "__main__":
    main()
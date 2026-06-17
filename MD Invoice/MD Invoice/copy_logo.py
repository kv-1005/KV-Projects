#!/usr/bin/env python3
"""
Script to copy the MD logo to the uploads directory
"""

import shutil
import os

# Copy the logo file
source = "md logo.jpg"
destination = "static/uploads/md_logo.jpg"

try:
    shutil.copy2(source, destination)
    print(f"✓ Logo copied successfully from {source} to {destination}")
except FileNotFoundError:
    print(f"❌ Source file {source} not found")
except Exception as e:
    print(f"❌ Error copying logo: {e}")

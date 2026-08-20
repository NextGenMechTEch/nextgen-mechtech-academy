#!/usr/bin/env python3
"""
Standalone database initialization script.
Run this to create tables and seed initial data.

Usage:
    python init_database.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database.init_db import initialize_database

if __name__ == "__main__":
    print("Initializing NextGen MechTech Academy database...")
    initialize_database()
    print("\nDone! You can now run: streamlit run app.py")
    print("\nAdmin Login:")
    print("   Email:    support.nextgenmechtech@gmail.com")
    print("   Password: Admin@123")
    print("\nIMPORTANT: Change the admin password after first login.")

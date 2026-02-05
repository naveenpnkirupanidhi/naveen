"""
WSGI entry point for production deployment (Render, etc.)
Imports the Flask app from portfolio/app.py
"""

import sys
import os

# Ensure both root and portfolio directories are importable
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'portfolio'))

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

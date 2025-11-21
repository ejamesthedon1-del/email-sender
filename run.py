#!/usr/bin/env python3
"""
Run the Email Outreach Platform web application
"""
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_ENV') == 'development'
    print(f"\n{'='*60}")
    print(f"Email Outreach Platform")
    print(f"Server running at: http://localhost:{port}")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=port, debug=debug)


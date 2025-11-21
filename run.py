#!/usr/bin/env python3
"""
Run the Email Outreach Platform web application
"""
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '127.0.0.1')
    debug = os.getenv('FLASK_ENV') == 'development'
    print(f"\n{'='*60}")
    print(f"Email Outreach Platform")
    print(f"Server running at: http://{host}:{port}")
    print(f"{'='*60}\n")
    app.run(host=host, port=port, debug=debug)


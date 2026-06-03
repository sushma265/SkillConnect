"""
SkillConnect – Application Entry Point
=========================================
Starts the Flask + SocketIO development server.

Usage:
    python run.py

For production, use gunicorn with eventlet:
    gunicorn run:app --worker-class eventlet -w 1 --bind 0.0.0.0:5000
"""

import eventlet
eventlet.monkey_patch()

from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
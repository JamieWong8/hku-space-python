#!/usr/bin/env python3
"""
Simple Flask Test App
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Flask Test App Running!</h1><p>Port 5000 is working correctly.</p>'

if __name__ == '__main__':
    print("Starting simple Flask test app...")
    print("Navigate to http://localhost:5000 to test")
    app.run(
        debug=False,
        host='127.0.0.1',
        port=5000,
        threaded=True,
        use_reloader=False
    )
from flask import Flask, render_template
import os
import socket

app = Flask(__name__)

@app.route('/')
def home():
    hostname = socket.gethostname()
    return render_template('index.html', hostname=hostname)

@app.route('/health')
def health():
    return {'status': 'healthy', 'version': '1.0'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
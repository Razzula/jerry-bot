import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """TODO"""

    payload = request.json
    if payload['action'] == 'push':
        # Pull updates from the repository
        subprocess.run(['run.sh'], check=True)
        os._exit(0)
    else:
        return jsonify({'message': 'Unsupported action'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

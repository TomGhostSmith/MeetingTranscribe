from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS, cross_origin
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enables CORS for all routes

# Folder where your video files (.m3u8, .ts, etc.) are located
VIDEO_DIR = "/Data/Video/test"

@cross_origin(methods=["GET"])
@app.route("/file/<path:filename>")
def serve_file(filename):
    return send_from_directory(VIDEO_DIR, filename)

@cross_origin(methods=["GET"])
@app.route("/api/getScript/<path:filename>", methods=["GET"])
def echo_api(filename):
    results = []
    prevStart = 0
    prevText = None
    with open(f"{VIDEO_DIR}/{filename}.script") as fp:
        for line in fp:
            s, t= line.strip().split('\t', 1)
            thisStart = float(t)
            if (prevText):
                results.append([prevText, prevStart, thisStart])
            prevText = s
            prevStart = thisStart
    results.append([prevText, prevStart, prevStart + 100])
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088, debug=True)

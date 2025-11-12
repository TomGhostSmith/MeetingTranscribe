from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS, cross_origin
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enables CORS for all routes

# Folder where your video files (.m3u8, .ts, etc.) are located
# VIDEO_DIR = "/Data/Video/test"
VIDEO_DIR = "/Data/Video/day1/day1-1"

@cross_origin(methods=["GET"])
@app.route("/file/<path:filename>")
def serve_file(filename):
    return send_from_directory(VIDEO_DIR, filename)

@cross_origin(methods=["GET"])
@app.route("/api/getScript/<path:filename>", methods=["GET"])
def echo_api(filename):
    results = []
    segment = []
    speaker = None
    prevStart = 0
    prevText = None
    insertSpeaker = None
    with open(f"{VIDEO_DIR}/{filename}.script") as fp:
    # with open(f"working/test.script") as fp:
        for line in fp:
            if ('\t' not in line):
                insertSpeaker = line.strip()
                continue
            # s, t= line.strip().split('\t', 1)
            s, t, e= line.strip().split('\t')
            thisStart = float(t)
            if (prevText):
                segment.append([prevText, prevStart, thisStart])
            if (insertSpeaker):
                if (segment):
                    results.append([speaker, segment])
                    segment = []
                speaker = insertSpeaker
                insertSpeaker = None
            prevText = s
            prevStart = thisStart
    segment.append([prevText, prevStart, prevStart + 100])
    results.append([speaker, segment])
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088, debug=True)

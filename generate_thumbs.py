from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json

app = Flask(__name__)
THUMB_FOLDER = 'static/thumbnails'
THUMBMAP_PATH = 'thumbmap.json'

@app.route("/admin")
def admin():
    if not os.path.exists(THUMBMAP_PATH):
        with open(THUMBMAP_PATH, 'w') as f:
            json.dump({}, f)

    with open(THUMBMAP_PATH, 'r') as f:
        thumbmap = json.load(f)

    return render_template("admin.html", json_map=thumbmap, os=os)


@app.route("/upload-thumb", methods=["POST"])
def upload_thumb():
    file = request.files.get("file")
    if file and file.filename.endswith(".jpg"):
        filepath = os.path.join(THUMB_FOLDER, file.filename)
        file.save(filepath)
        return redirect(url_for("admin"))
    return "Invalid file", 400


@app.route("/delete-thumb/<filename>", methods=["POST"])
def delete_thumb(filename):
    try:
        os.remove(os.path.join(THUMB_FOLDER, filename))
        return redirect(url_for("admin"))
    except:
        return "Failed to delete", 500
    
@app.route("/update-map", methods=["POST"])
def update_map():
    data = request.get_json()
    with open(THUMBMAP_PATH, 'w') as f:
        json.dump(data, f, indent=4)
    return jsonify({"status": "ok"})


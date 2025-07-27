from flask import Flask, render_template, send_from_directory, abort
import os
import json
import difflib
import re

app = Flask(__name__)

VIDEO_DIR = "static/video"  # ✅ Update to your correct path
THUMB_DIR = "static/thumbnails"
VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".avi")
DEFAULT_THUMB = "/static/default.jpg"

def clean_title(name):
    name = os.path.splitext(name)[0]
    name = re.sub(r'[^a-zA-Z0-9\s]', ' ', name)
    name = re.sub(r'\b(1080p|720p|hd|hdrip|dvdrip|bluray|tamilprint|hindi|english|telugu)\b', '', name, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', name).strip().lower()

def load_json_map():
    if os.path.exists("thumbmap.json"):
        with open("thumbmap.json") as f:
            return {k.lower(): v for k, v in json.load(f).items()}
    return {}

def get_thumbnail_map():
    thumbs = {}
    for f in os.listdir(THUMB_DIR):
        if f.lower().endswith(".jpg"):
            title = clean_title(f)
            thumbs[title] = f"/static/thumbnails/{f}"
    return thumbs

def match_thumbnail(title, thumb_map, json_map):
    for key, val in json_map.items():
        if key in title:
            path = f"{THUMB_DIR}/{val}"
            if os.path.exists(path):
                return path.replace("static", "/static")
    for key in thumb_map:
        if key in title:
            return thumb_map[key]
    match = difflib.get_close_matches(title, thumb_map.keys(), n=1, cutoff=0.6)
    return thumb_map[match[0]] if match else DEFAULT_THUMB

def categorize_file(folder, filename):
    name = filename.lower()
    if "anime" in folder.lower() or "anime" in name:
        return "Anime"
    if "movie" in folder.lower() or "movie" in name:
        return "Movies"
    return "Others"

def get_all_content():
    categorized = {"Movies": [], "Series": [], "Anime": [], "Others": []}
    thumb_map = get_thumbnail_map()
    json_map = load_json_map()

    for category_folder in os.listdir(VIDEO_DIR):
        category_path = os.path.join(VIDEO_DIR, category_folder)
        if not os.path.isdir(category_path):
            continue

        for root, _, files in os.walk(category_path):
            rel_path = os.path.relpath(root, VIDEO_DIR).replace("\\", "/")
            folder_name = os.path.basename(root).lower()
            video_files = [f for f in files if f.lower().endswith(VIDEO_EXTS)]

            if not video_files:
                continue

            # ✅ Handle Series folders (inside Series/)
            if category_folder.lower() == "series" and root != category_path:
                title = folder_name.title()
                thumb = match_thumbnail(folder_name, thumb_map, json_map)
                link = f"/series/{folder_name}"
                categorized["Series"].append({
                    "title": title,
                    "thumb": thumb,
                    "link": link
                })
            else:
                for file in video_files:
                    file_path = os.path.join(rel_path, file).replace("\\", "/")
                    title = clean_title(file).title()
                    thumb = match_thumbnail(title.lower(), thumb_map, json_map)

                    # 🧠 Use folder name to categorize
                    if category_folder.lower() == "movies":
                        cat = "Movies"
                    elif category_folder.lower() == "animes":
                        cat = "Anime"
                    elif category_folder.lower() == "others":
                        cat = "Others"
                    else:
                        cat = categorize_file(root, file)

                    link = f"/watch/{file_path}"
                    categorized[cat].append({
                        "title": title,
                        "thumb": thumb,
                        "link": link
                    })

    return categorized

@app.route('/')
def index():
    return render_template("index.html", categorized=get_all_content())

@app.route("/series/<series_name>")
def series_page(series_name):
    full_path = os.path.join(VIDEO_DIR, "Series", series_name)
    if not os.path.isdir(full_path):
        abort(404)

    episodes = []
    thumb_map = get_thumbnail_map()
    json_map = load_json_map()
    for f in sorted(os.listdir(full_path)):
        if f.lower().endswith(VIDEO_EXTS):
            clean = clean_title(f).title()
            episodes.append({
                "title": clean,
                "file": f
            })
    thumb = match_thumbnail(series_name, thumb_map, json_map)
    return render_template("series.html", name=series_name.title(), episodes=episodes, thumb=thumb)

@app.route("/watch/<path:filename>")
def watch_video(filename):
    filepath = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(filepath):
        return "Video not found", 404

    title = clean_title(os.path.basename(filename)).title()
    return render_template("watch_single.html", title=title, video_path=filename)

@app.route('/video/<path:filename>')
def video(filename):
    return send_from_directory(VIDEO_DIR, filename, as_attachment=False)

@app.route("/movies")
def movies_page():
    categorized = get_all_content()
    return render_template("category.html", title="Movies", items=categorized["Movies"])

@app.route("/series")
def series_list_page():
    categorized = get_all_content()
    return render_template("category.html", title="Series", items=categorized["Series"])

@app.route("/anime")
def anime_page():
    categorized = get_all_content()
    return render_template("category.html", title="Anime", items=categorized["Anime"])

@app.route("/recent")
def recent_page():
    categorized = get_all_content()
    recent = []
    for cat in categorized.values():
        recent.extend(cat)
    recent = sorted(recent, key=lambda x: x['title'], reverse=True)[:30]  # Customize this
    return render_template("category.html", title="Recently Updated", items=recent)

@app.route("/admin")
def admin_page():
    categorized = get_all_content()
    return render_template("admin.html", title="Admin", items=categorized["Admin"])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)




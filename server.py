from flask import Flask, render_template, request, redirect, url_for
from slugify import slugify
from datetime import date
from uuid import uuid4
import os, json
import subprocess


app = Flask(__name__)


def git_commit_and_push(message: str):
    subprocess.run(["git", "add", "posts", "assets/images"], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(BASE_DIR, "posts")
IMAGES_DIR = os.path.join(BASE_DIR, "assets/images")

INDEX_JSON = os.path.join(POSTS_DIR, "index.json")
LATEST_JSON = os.path.join(POSTS_DIR, "latest.json")

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        post_id = str(uuid4())
        title = request.form["title"]
        description = request.form["description"]
        content = request.form["content"]
        slug = slugify(request.form["slug"] or title)
        pinned = request.form.get("pinned") == "on"

        img = request.files.get("image")
        image_path = ""

        if img:
            ext = os.path.splitext(img.filename)[1]
            img_name = f"{slug}{ext}"
            img.save(os.path.join(IMAGES_DIR, img_name))
            image_path = f"/assets/images/{img_name}"

        today = date.today().isoformat()
        filename = f"{today}@{post_id}.md"

        md = f"""---
id: "{post_id}"
filename: "{filename}"
title: "{title}"
slug: "{slug}"
description: "{description}"
date: "{today}"
image: "{image_path}"
pinned: {str(pinned).lower()}
---

{content}
"""

        with open(os.path.join(POSTS_DIR, filename), "w", encoding="utf-8") as f:
            f.write(md)

        post_meta = {
            "id": post_id,
            "filename": filename,
            "title": title,
            "slug": slug,
            "description": description,
            "date": today,
            "image": image_path,
            "pinned": pinned
        }

        index = load_json(INDEX_JSON)
        index.insert(0, post_meta)
        save_json(INDEX_JSON, index)

        pinned_posts = [p for p in index if p["pinned"]]
        normal_posts = [p for p in index if not p["pinned"]]

        latest = (pinned_posts + normal_posts)[:3]
        save_json(LATEST_JSON, latest)

        commit_msg = f"(auto) new post added: {filename}"
        git_commit_and_push(commit_msg)

        return redirect(url_for("created"))

    return render_template("admin.html")

@app.route("/created")
def created():
    return "created."

if __name__ == "__main__":
    app.run(debug=True)

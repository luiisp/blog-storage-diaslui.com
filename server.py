from flask import Flask, render_template, request, redirect, url_for
from slugify import slugify
from datetime import date
import os
import json
import uuid
import subprocess

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

POSTS_DIR = os.path.join(BASE_DIR, "posts")
IMAGES_DIR = os.path.join(BASE_DIR, "assets/images")
INDEXES_DIR = os.path.join(BASE_DIR, "indexes")

POSTS_INDEX = os.path.join(INDEXES_DIR, "posts.json")
PINNED_INDEX = os.path.join(INDEXES_DIR, "pinned.json")
LATEST_INDEX = os.path.join(INDEXES_DIR, "latest.json")

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(INDEXES_DIR, exist_ok=True)



def git_commit_and_push(message: str):
    subprocess.run(["git", "add", "posts", "assets/images"], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)

def load_posts_index():
    if not os.path.exists(POSTS_INDEX):
        return []
    with open(POSTS_INDEX, "r", encoding="utf-8") as f:
        return json.load(f)


def save_posts_index(posts):
    with open(POSTS_INDEX, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


def rebuild_derived_indexes(posts):
    pinned = [p for p in posts if p.get("pinned")]
    with open(PINNED_INDEX, "w", encoding="utf-8") as f:
        json.dump(pinned, f, indent=2, ensure_ascii=False)

    latest = sorted(posts, key=lambda p: p["date"], reverse=True)[:3]
    with open(LATEST_INDEX, "w", encoding="utf-8") as f:
        json.dump(latest, f, indent=2, ensure_ascii=False)

@app.route("/", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        content = request.form["content"]
        pinned = request.form.get("pinned") == "on"

        slug = slugify(request.form.get("slug") or title)
        post_id = str(uuid.uuid4())
        today = date.today().isoformat()

        year, month, _ = today.split("-")

        post_dir = os.path.join(POSTS_DIR, year, month)
        os.makedirs(post_dir, exist_ok=True)

        img = request.files.get("image")
        image_path = ""

        if img:
            img_name = f"{slug}{os.path.splitext(img.filename)[1]}"
            img.save(os.path.join(IMAGES_DIR, img_name))
            image_path = f"/assets/images/{img_name}"

        md_filename = f"{slug}.md"
        md_path = os.path.join(post_dir, md_filename)

        md = f"""---
id: "{post_id}"
title: "{title}"
slug: "{slug}"
description: "{description}"
date: "{today}"
image: "{image_path}"
pinned: {str(pinned).lower()}
---

{content}
"""

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)

        posts = load_posts_index()

        posts.append({
            "id": post_id,
            "title": title,
            "slug": slug,
            "description": description,
            "date": today,
            "image": image_path,
            "pinned": pinned,
            "path": f"/posts/{year}/{month}/{md_filename}"
        })

        save_posts_index(posts)
        rebuild_derived_indexes(posts)
        git_commit_and_push(f"(auto) Add new post: {title}")
        return redirect(url_for("created"))

    return render_template("admin.html")

@app.route("/created")
def created():
    return "Post created successfully!"


if __name__ == "__main__":
    app.run(debug=True)

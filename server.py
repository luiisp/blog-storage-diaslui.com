from flask import Flask, render_template, request, redirect, url_for
from slugify import slugify
from datetime import date
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(BASE_DIR, "posts")
IMAGES_DIR = os.path.join(BASE_DIR, "assets/images")

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        content = request.form["content"]
        slug = slugify(request.form["slug"] or title)

        img = request.files.get("image")
        image_path = ""

        if img:
            img_name = f"{slug}{os.path.splitext(img.filename)[1]}"
            img.save(os.path.join(IMAGES_DIR, img_name))
            image_path = f"/assets/images/{img_name}"

        today = date.today().isoformat()
        filename = f"{today}\{title}\{img_name}.md" 

        md = f"""
---
title: "{title}"
slug: "{slug}"
description: "{description}"
date: {today}
image: "{image_path}"
---

{content}
                """

        with open(os.path.join(POSTS_DIR, filename), "w", encoding="utf-8") as f:
            f.write(md)
        
        return redirect(url_for("created"))

    return render_template("admin.html")

@app.route("/created")
def created():
    exit()
    return "Post created successfully!,  closing server."

if __name__ == "__main__":
    app.run(debug=True)

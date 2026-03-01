#!/usr/bin/env python3
"""Fetch latest blog posts from tabularis.dev JSON and update README.md."""

import json
import re
import urllib.request
from datetime import datetime


LATEST_POSTS_URL = "https://tabularis.dev/latest-posts.json"
README_PATH = "README.md"
MAX_POSTS = 5
IMG_WIDTH = 120

START_MARKER = "<!-- BLOG-POSTS:START -->"
END_MARKER = "<!-- BLOG-POSTS:END -->"


def fetch_json(url):
    """Fetch JSON from a URL and return parsed Python object."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read()
    return json.loads(content.decode("utf-8"))


def parse_date_to_datetime(value):
    """Parse various date formats to YYYY-MM-DD HH:MM; fallback to original string."""
    if not value:
        return ""

    value = str(value).strip()

    formats = (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    )

    # Remove timezone if present
    cleaned = value.replace("Z", "")
    if "+" in cleaned:
        cleaned = cleaned.split("+", 1)[0]

    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass

    return value


def generate_blog_section(posts):
    """Generate the markdown section for blog posts as a table."""
    if not posts:
        return f"{START_MARKER}\n*No blog posts found.*\n{END_MARKER}"

    posts = posts[:MAX_POSTS]

    lines = [START_MARKER]
    lines.append("")
    lines.append("| Preview | Title | Published |")
    lines.append("|---|---|---|")

    for post in posts:
        title = (post.get("title") or "").strip()
        url = (post.get("url") or "").strip()
        image = (post.get("image") or "").strip()
        date = parse_date_to_datetime(post.get("date"))

        # Image clickable → article
        if image and url:
            img_cell = f'[<img src="{image}" alt="{title}" width="{IMG_WIDTH}" />]({url})'
        else:
            img_cell = ""

        title_cell = f"[{title}]({url})" if title and url else (title or url)

        lines.append(f"| {img_cell} | {title_cell} | {date} |")

    lines.append("")
    lines.append(
        f"*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*"
    )
    lines.append(END_MARKER)

    return "\n".join(lines)


def update_readme(blog_section):
    """Update README.md with the blog posts section."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL,
    )

    if pattern.search(content):
        new_content = pattern.sub(blog_section, content)
    else:
        new_content = (
            content.rstrip("\n")
            + "\n\n"
            + blog_section
            + "\n"
        )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    try:
        posts = fetch_json(LATEST_POSTS_URL)
    except Exception as e:
        print(f"Error: could not fetch latest posts JSON: {e}")
        return

    if not isinstance(posts, list) or not posts:
        print("No blog posts found in JSON.")
        return

    blog_section = generate_blog_section(posts)
    update_readme(blog_section)
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()

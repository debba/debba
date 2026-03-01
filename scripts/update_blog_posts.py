#!/usr/bin/env python3
"""Fetch blog posts from tabularis.dev sitemap and update README.md."""

import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime


SITEMAP_URLS = [
    "https://tabularis.dev/sitemap.xml",
    "https://tabularis.dev/sitemap-0.xml",
]
BLOG_PATH_PREFIX = "/blog/"
README_PATH = "README.md"

START_MARKER = "<!-- BLOG-POSTS:START -->"
END_MARKER = "<!-- BLOG-POSTS:END -->"


def fetch_sitemap(url):
    """Fetch and parse a sitemap XML, returning a list of blog post URLs."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read()
    return content


def extract_blog_urls_from_sitemap(xml_content):
    """Extract blog URLs from sitemap XML content.

    Handles both sitemap index files and regular sitemaps.
    """
    root = ET.fromstring(xml_content)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Check if this is a sitemap index (contains other sitemaps)
    sitemap_locs = root.findall(".//s:sitemap/s:loc", ns)
    if sitemap_locs:
        blog_urls = []
        for loc in sitemap_locs:
            try:
                child_xml = fetch_sitemap(loc.text)
                blog_urls.extend(extract_blog_urls_from_sitemap(child_xml))
            except Exception as e:
                print(f"Warning: failed to fetch child sitemap {loc.text}: {e}")
        return blog_urls

    # Regular sitemap: extract <url><loc> entries
    urls = []
    for url_elem in root.findall(".//s:url", ns):
        loc = url_elem.find("s:loc", ns)
        if loc is not None and BLOG_PATH_PREFIX in loc.text:
            lastmod = url_elem.find("s:lastmod", ns)
            urls.append({
                "url": loc.text,
                "lastmod": lastmod.text if lastmod is not None else None,
            })

    return urls


def url_to_title(url):
    """Convert a blog URL slug to a readable title."""
    slug = url.rstrip("/").split("/")[-1]
    title = slug.replace("-", " ").title()
    return title


def generate_blog_section(posts):
    """Generate the markdown section for blog posts."""
    if not posts:
        return f"{START_MARKER}\n*No blog posts found.*\n{END_MARKER}"

    # Sort by lastmod (newest first) if available, otherwise by URL
    posts.sort(key=lambda p: p.get("lastmod") or "", reverse=True)

    lines = [START_MARKER]
    for post in posts:
        title = url_to_title(post["url"])
        url = post["url"]
        lines.append(f"- [{title}]({url})")
    lines.append("")
    lines.append(f"*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*")
    lines.append(END_MARKER)

    return "\n".join(lines)


def update_readme(blog_section):
    """Update README.md with the blog posts section."""
    with open(README_PATH, "r") as f:
        content = f.read()

    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL,
    )

    if pattern.search(content):
        new_content = pattern.sub(blog_section, content)
    else:
        new_content = content.rstrip("\n") + "\n\n### Latest Blog Posts\n\n" + blog_section + "\n"

    with open(README_PATH, "w") as f:
        f.write(new_content)


def main():
    blog_posts = []

    for sitemap_url in SITEMAP_URLS:
        try:
            print(f"Fetching sitemap: {sitemap_url}")
            xml_content = fetch_sitemap(sitemap_url)
            blog_posts = extract_blog_urls_from_sitemap(xml_content)
            if blog_posts:
                print(f"Found {len(blog_posts)} blog posts from {sitemap_url}")
                break
        except Exception as e:
            print(f"Warning: could not fetch {sitemap_url}: {e}")

    if not blog_posts:
        print("No blog posts found from any sitemap source.")
        return

    blog_section = generate_blog_section(blog_posts)
    update_readme(blog_section)
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the whole site:

    python3 tools/build.py

1. index.html from archive.csv and album-covers.csv
2. every project page
3. redirects for retired URLs, the 404 page, sitemap.xml and llms.txt
"""
from pathlib import Path

import build_archive
import build_pages
from build_archive import FONT_LINKS
from sitedata import REDIRECTS, ROOT, write_llms, write_redirects, write_sitemap

NOT_FOUND = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex">
    <title>Page Not Found, David Drake</title>
    {FONT_LINKS.replace('href="ledger.css"', 'href="/ledger.css"')}
</head>
<body>
    <main class="ledger page">
        <header>
            <p class="crumb"><a href="/">Archive</a></p>
            <h1>Page Not Found</h1>
        </header>
        <p class="prose">That page no longer exists. It may have been part of an earlier version of this site.</p>
    </main>
</body>
</html>
'''


def build():
    build_archive.build()
    build_pages.build()
    write_redirects()
    (ROOT / "404.html").write_text(NOT_FOUND)

    pages = ["index.html"] + sorted(
        str(p.relative_to(ROOT)) for folder in ("film", "music-video", "album-art", "photography")
        for p in (ROOT / folder).glob("*.html") if str(p.relative_to(ROOT)) not in REDIRECTS)
    write_sitemap(pages)
    write_llms(pages)
    print(f"Sitemap and llms.txt list {len(pages)} pages; {len(REDIRECTS)} redirects written")


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Build the archive list in index.html from archive.csv.

Edit archive.csv (one row per item) or album-covers.csv (one row per
release, grouped into sections), then run:
    python3 tools/build_archive.py

Columns: date, title, source, url, category, type, status
- date: YYYY, YYYY-MM or YYYY-MM-DD. Only the year is shown; the full date sorts.
- title: wrap text in *asterisks* for italics.
- source: publication, festival or venue, shown before the title.
- category: drives the show/hide checkboxes.

album-covers.csv columns: section, date, artist, release, format, label
- Each section becomes one "Album Art" row, dated by its latest release.
"""
import csv
import html
import re
from pathlib import Path

from sitedata import BASE, clean_head, item_list

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "archive.csv"
COVERS_CSV = ROOT / "album-covers.csv"
PAGE = ROOT / "index.html"

# Each group is one line of checkboxes. Both start ticked.
GROUPS = [
    ("Projects", ["Feature Film", "Short Film", "Music Video", "Photography", "Album Art", "Short Story", "Novel"]),
    ("Footnotes", ["Screening", "Exhibition", "Award", "Talk", "Role", "Press"]),
]
SHOWN_AT_START = {"Projects", "Footnotes"}

FONT_LINKS = '''<link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="ledger.css">'''

CONTACT = '''        <section class="contact">
            <h2>Contact</h2>
            <p>US: The Gersh Agency, Alana Ford, <a href="mailto:aduthie@gersh.com">aduthie@gersh.com</a>, +1 (310) 887 3717</p>
            <p>UK: Braintrust, Sam Bank, <a href="mailto:sam@braintrust.tv">sam@braintrust.tv</a>, +44 7788 266832</p>
            <p>UK: Braintrust, Helene Sifre, <a href="mailto:helene@braintrust.tv">helene@braintrust.tv</a>, +44 7930 337758</p>
        </section>'''

SCRIPT = '''    <script>
    (function () {
        var list = document.querySelector('.ledger-rows');
        var rows = Array.prototype.slice.call(list.children);
        var buttons = document.querySelectorAll('.sort');
        var state = { key: 'date', dir: -1 };

        function sort() {
            rows.sort(function (a, b) {
                if (state.key === 'date') {
                    // Within a year, projects always come before the second group.
                    var ya = a.dataset.date.slice(0, 4), yb = b.dataset.date.slice(0, 4);
                    if (ya !== yb) return (ya > yb ? 1 : -1) * state.dir;
                    if (a.dataset.group !== b.dataset.group) return a.dataset.group - b.dataset.group;
                }
                var x = a.dataset[state.key], y = b.dataset[state.key];
                if (x === y) return (b.dataset.date > a.dataset.date) ? 1 : -1;
                return (x > y ? 1 : -1) * state.dir;
            });
            rows.forEach(function (r) { list.appendChild(r); });
            buttons.forEach(function (b) {
                var on = b.dataset.key === state.key;
                b.setAttribute('aria-sort', on ? (state.dir > 0 ? 'ascending' : 'descending') : 'none');
            });
        }

        buttons.forEach(function (b) {
            b.addEventListener('click', function () {
                if (state.key === b.dataset.key) state.dir = -state.dir;
                else { state.key = b.dataset.key; state.dir = b.dataset.key === 'date' ? -1 : 1; }
                sort();
            });
        });

        var boxes = document.querySelectorAll('.filters input:not(.group-toggle)');
        function filter() {
            var on = {};
            boxes.forEach(function (c) { on[c.value] = c.checked; });
            rows.forEach(function (r) { r.hidden = !on[r.dataset.category]; });
        }
        boxes.forEach(function (c) { c.addEventListener('change', filter); });

        // The group name ticks or unticks its whole line.
        document.querySelectorAll('.filter-line').forEach(function (line) {
            var all = line.querySelector('.group-toggle');
            var items = line.querySelectorAll('input:not(.group-toggle)');
            function sync() {
                var on = Array.prototype.filter.call(items, function (c) { return c.checked; }).length;
                all.checked = on === items.length;
                all.indeterminate = on > 0 && on < items.length;
            }
            all.addEventListener('change', function () {
                items.forEach(function (c) { c.checked = all.checked; });
                filter();
            });
            items.forEach(function (c) { c.addEventListener('change', sync); });
            sync();
        });

        sort();
        filter();
    })();
    </script>'''


def esc(text):
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", html.escape(text, quote=False))


def sort_text(text):
    return re.sub(r"[*]", "", text).lower()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", sort_text(text).replace("'", "")).strip("-")


def album_sections():
    """Group album-covers.csv into one archive item per section."""
    if not COVERS_CSV.exists():
        return []
    with COVERS_CSV.open(newline="") as f:
        releases = list(csv.DictReader(f))
    sections = {}
    for r in releases:
        sections.setdefault(r["section"], []).append(r)
    items = []
    for name, rels in sections.items():
        latest = max(r["date"] for r in rels)
        items.append({
            "date": latest, "title": name, "source": "", "url": f"album-art/{slug(name)}.html",
            "category": "Album Art", "type": "album art", "status": "released",
            "project": "", "releases": rels,
        })
    return items


def load_items():
    with CSV.open(newline="") as f:
        return list(csv.DictReader(f)) + album_sections()



def build():
    items = load_items()

    used = {i["category"] for i in items}
    grouped = [(name, [c for c in cats if c in used]) for name, cats in GROUPS]
    leftover = sorted(used - {c for _, cats in GROUPS for c in cats})
    if leftover:
        grouped[-1][1].extend(leftover)

    lines = []
    for name, cats in grouped:
        checked = " checked" if name in SHOWN_AT_START else ""
        boxes = "\n".join(
            f'                <label><input type="checkbox" value="{html.escape(c)}"{checked}> {html.escape(c)} '
            f'<span class="count">{sum(i["category"] == c for i in items)}</span></label>'
            for c in cats
        )
        lines.append(f'''            <div class="filter-line">
                <label class="filter-name"><input type="checkbox" class="group-toggle"{checked}> {name}</label>
{boxes}
            </div>''')
    filters = "\n".join(lines)

    group_of = {c: n for n, (_, cats) in enumerate(grouped) for c in cats}

    rows = []
    for i in items:
        title = esc(i["title"])
        if i["url"]:
            external = i["url"].startswith("http")
            target = ' target="_blank" rel="noopener noreferrer"' if external else ""
            title = f'<a href="{html.escape(i["url"])}"{target}>{title}</a>'
        if i["source"]:
            title = f'{esc(i["source"])}, {title}'
        full_title = f'{i["source"]}, {i["title"]}' if i["source"] else i["title"]
        rows.append(
            f'            <li data-date="{html.escape(i["date"])}" data-title="{html.escape(sort_text(full_title))}" '
            f'data-type="{html.escape(i["type"])}" data-status="{html.escape(i["status"])}" '
            f'data-category="{html.escape(i["category"])}" data-group="{group_of[i["category"]]}"'
            f'{" class=\"fn\"" if group_of[i["category"]] else ""}>'
            f'<span class="c date">{html.escape(i["date"][:4])}</span>'
            f'<span class="c title"><span class="t">{title}</span></span>'
            f'<span class="c type"><span class="t">{html.escape(i["type"]).title().replace("Q&Amp;A", "Q&amp;A")}</span></span>'
            f'<span class="c status"><span class="t">{html.escape(i["status"]).title()}</span></span></li>'
        )

    body = f'''<body>
    <main class="ledger">
        <header>
            <h1>Archive</h1>
            <p>David Drake (b. 1986, New York) is a self-taught American writer, director, and photographer based in Norwich, UK.</p>
        </header>

{CONTACT}

        <div class="filters">
{filters}
        </div>

        <div class="ledger-head" role="presentation">
            <button class="sort c date" data-key="date">Date</button>
            <button class="sort c title" data-key="title">Title</button>
            <button class="sort c type" data-key="type">Type</button>
            <button class="sort c status" data-key="status">Status</button>
        </div>
        <ol class="ledger-rows">
{chr(10).join(rows)}
        </ol>
    </main>
{SCRIPT}
</body>'''

    page = PAGE.read_text()
    page = re.sub(r'<link rel="preconnect" href="https://fonts.googleapis.com">.*?<link rel="stylesheet" href="[^"]+\.css">',
                  lambda m: FONT_LINKS, page, count=1, flags=re.S)
    page = re.sub(r"<body>.*</body>", lambda m: body, page, flags=re.S)
    projects = [(re.sub(r"\*", "", i["title"]),
                 BASE + i["url"] if i["url"] and not i["url"].startswith("http") else i["url"], i["date"][:4])
                for i in sorted(items, key=lambda i: i["date"], reverse=True) if group_of[i["category"]] == 0]
    head, rest = page.split("</head>", 1)
    page = clean_head(head + "</head>", "", "David Drake, Archive", [item_list("Projects", projects)]) + rest
    PAGE.write_text(page)
    print(f"Built {len(items)} items into {PAGE.name}")


if __name__ == "__main__":
    build()

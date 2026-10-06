#!/usr/bin/env python3
"""Build the individual project pages in the same ledger style as index.html.

    python3 tools/build_pages.py

- Film, photography and Blue Banana pages are rebuilt in place from their
  original content (as committed in git) (intro text, video or images, cast, credits, listings).
- Album art pages are generated into album-art/ from album-covers.csv.
- Every page lists its footnotes: rows in archive.csv whose "project" column
  names that page.
"""
import html
import re
import subprocess
from pathlib import Path

from build_archive import FONT_LINKS, esc, slug, album_sections, load_items
from sitedata import BASE, PERSON_ID, clean_head, item_list

ROOT = Path(__file__).resolve().parent.parent

PAGES = [
    "film/the-long-haul.html", "film/law-of-sines.html", "film/left-over.html",
    "film/post-398.html", "film/early-worm.html", "film/a-foot-of-turf.html",
    "film/party-wall.html",
    "photography/common-era.html", "photography/commissions.html",
    "photography/avec-pi.html", "photography/carousel.html",
    "photography/sailing-stones.html", "photography/a-burning-cloud.html",
]

# Old sections now covered by the footnotes list.
FOOTNOTE_SECTIONS = {"Press", "Festivals", "Press and Screenings", "Press and Festivals", "Exhibitions"}

# Images (paths under images/) that belong to a campaign, in display order.
# The optional second value is used as alt text, not shown on the page.
AC = "photography/album-covers/"
CM = "photography/commissions/"
AA = "album-art/"
COVERS = {
    "The 1975, early EPs": [
        (AA + "the-1975-music-for-cars.jpg", "Music for Cars EP"), (AA + "the-1975-iv.jpg", "IV EP"),
    ],
    "The 1975, *The 1975*": [
        (AC + "album-covers-01.jpg", "The 1975, album"), (AA + "the-1975-sex-single.jpg", "Sex"),
        (AA + "the-1975-girls.jpg", "Girls"), (AA + "the-1975-settle-down.jpg", "Settle Down"),
    ],
    "The 1975, *I Like It When You Sleep*": [
        (AC + "album-covers-02.jpg", "I Like It When You Sleep, album"),
        (AA + "the-1975-love-me.jpg", "Love Me, single"),
        (AA + "the-1975-the-sound.jpg", "The Sound, single"),
        (AA + "the-1975-somebody-else.jpg", "Somebody Else, single"),
        (CM + "commissions-05.jpg", "Love Me"),
        (CM + "commissions-24.jpg", "Ugh!"),
        (CM + "commissions-14.jpg", "She's American"),
        (CM + "commissions-04.jpg", "This Must Be My Dream"),
        (CM + "commissions-12.jpg", "Lostmyhead"),
        (CM + "commissions-26.jpg", "Please Be Naked"),
        (CM + "commissions-18.jpg", "campaign photograph"),
        (CM + "commissions-01.jpg", "campaign photograph"),
        (CM + "commissions-07.jpg", "campaign photograph"),
    ],
    "Rouge Neon Records": [AC + "album-covers-03.jpg", AC + "album-covers-10.jpg"],
    "Alvarez Kings, *Somewhere Between*": [AC + "album-covers-05.jpg"],
    "Amber Run, *5AM*": [AC + "album-covers-08.jpg"],
    "Jens Kuross, singles and EPs": [
        AC + "album-covers-09.jpg", AC + "album-covers-12.jpg",
        (CM + "commissions-10.jpg", "Art! at the expense of mental health, Vol. 1, cover photograph"),
    ],
    "Amy Milner, singles": [AC + "album-covers-15.jpg"],
    "Olympians, *Reasons to Be Tearful*": [AC + "album-covers-17.jpg"],
    "Kele Okereke, *Fatherland*": [(AA + "kele-okereke-fatherland.jpg", "Fatherland, album")],
    "Zach Said, singles and EPs": [
        (AA + "zach-said-no-love.jpg", "No Love"), (AA + "zach-said-holding-on.jpg", "Holding On"),
        (AA + "zach-said-contrast.jpg", "CONTRAST EP"),
        (CM + "commissions-23.jpg", "photograph"), (CM + "commissions-15.jpg", "photograph"),
        (AA + "zach-said-money.jpg", "Money"), (AA + "zach-said-catch-a-feeling.jpg", "Catch a Feeling"),
        (AA + "zach-said-balance.jpg", "BALANCE EP"),
    ],
}

# A campaign's Credits section, shown after its images, as (role, html).
CREDITS = {
    "Zach Said, singles and EPs": [
        ("Photography", "David Drake"),
        ("Art Direction", "David Drake"),
        ("Design", "David Drake"),
        ("Illustration", '<a href="https://www.instagram.com/joelbenjaminillustrator/" target="_blank" rel="noopener noreferrer">Joel Benjamin</a>'),
    ],
}

# Music video pages, generated into music-video/. Details come from each
# video's own Vimeo or YouTube description.
EVY = '<a href="https://evy.li" target="_blank" rel="noopener noreferrer">Evy Lindberg</a>'
SM = EVY  # credited as Stu McComie / McOmie in older sources
MUSIC_VIDEOS = [
    {"slug": "live-footage-view-from-a-desert-helicopter", "artist": "Live Footage", "title": "View From a Desert Helicopter",
     "release": "*Moods of the Desert*", "embed": "https://www.youtube.com/embed/0ozMKemAtME",
     "watch": ("YouTube", "https://www.youtube.com/watch?v=0ozMKemAtME"),
     "credits": [("Video", "David Drake"), ("FX", "Dan Tombs")]},
    {"slug": "ider-nevermind", "artist": "IDER", "title": "Nevermind",
     "release": "*Gut Me Like an Animal* EP", "embed": "https://www.youtube.com/embed/esv8O2hD9hU",
     "watch": ("YouTube", "https://www.youtube.com/watch?v=esv8O2hD9hU"),
     "credits": [("Directors", "David Drake, IDER and Lewis Knaggs"), ("Producer", "David Drake"),
                 ("Editor", "Lewis Knaggs"), ("Director of Photography", SM)]},
    {"slug": "sink-ya-teeth-substitutes", "artist": "Sink Ya Teeth", "title": "Substitutes",
     "release": "*Sink Ya Teeth*", "embed": "https://www.youtube.com/embed/SIzREq2V25U",
     "watch": ("YouTube", "https://www.youtube.com/watch?v=SIzREq2V25U"),
     "prose": "Shot at The Shoe Factory Social Club in Norwich.",
     "credits": [("Director", "David Drake"), ("Director of Photography", SM), ("Production", "Kamiokande Films")]},
    {"slug": "aniseed-crabshells", "artist": "Aniseed", "title": "Crabshells",
     "embed": "https://player.vimeo.com/video/303471802",
     "watch": ("Vimeo", "https://vimeo.com/303471802"),
     "credits": [("Director", "David Drake"), ("Photography", SM), ("Production", "Kamiokande")]},
    {"slug": "alex-kozobolis-offline", "artist": "Alex Kozobolis", "title": "Offline",
     "embed": "https://player.vimeo.com/video/399813164",
     "watch": ("Vimeo", "https://vimeo.com/399813164"),
     "prose": "A woman wanders through an abandoned world in search of something meaningful.",
     "credits": [("Director", "David Drake"), ("Composer", "Alex Kozobolis"), ("Actor", "Ruby Bardwell-Dix"),
                 ("Editor", "Ian Drake"), ("Cinematography", SM), ("Sound Design", "Jack Brady Spelman"),
                 ("Production Assistant", "Jenny Swindells")]},
]

# Campaign videos, embedded after the images.
VIDEOS = {
    "Kele Okereke, *Fatherland*": "https://player.vimeo.com/video/265724166",
}


def leader(left, right=""):
    """A two-part row: left ........ right."""
    if not right:
        return f'            <li class="pair"><span class="l">{left}</span></li>'
    return f'            <li class="pair"><span class="l">{left}</span><span class="r">{right}</span></li>'


def ledger_row(date, title, typ, status, cls=""):
    attr = f' class="{cls}"' if cls else ""
    return (f'            <li{attr}><span class="c date">{date}</span>'
            f'<span class="c title"><span class="t">{title}</span></span>'
            f'<span class="c type"><span class="t">{typ}</span></span>'
            f'<span class="c status"><span class="t">{status}</span></span></li>')


def footnote_items(page, items):
    rows = [i for i in items if page in i.get("project", "").split("|")]
    return sorted(rows, key=lambda i: i["date"], reverse=True)


def footnote_schema(page, items):
    rows = footnote_items(page, items)
    if not rows:
        return []
    return [item_list("Footnotes", [(re.sub(r"\*", "", f'{i["source"]}, {i["title"]}' if i["source"] else i["title"]),
                                      i["url"] if i["url"].startswith("http") else "", i["date"]) for i in rows])]


def footnotes(page, items, prefix):
    rows = [i for i in items if page in i.get("project", "").split("|")]
    rows.sort(key=lambda i: i["date"], reverse=True)
    if not rows:
        return ""
    out = []
    for i in rows:
        title = esc(i["title"])
        if i["url"]:
            ext = i["url"].startswith("http")
            href = i["url"] if ext else prefix + i["url"]
            target = ' target="_blank" rel="noopener noreferrer"' if ext else ""
            title = f'<a href="{html.escape(href)}"{target}>{title}</a>'
        if i["source"]:
            title = f'{esc(i["source"])}, {title}'
        out.append(ledger_row(i["date"][:4], title, html.escape(i["type"]).title().replace("Q&Amp;A", "Q&amp;A"),
                              html.escape(i["status"]).title(), "fn"))
    return section("Footnotes", '        <ol class="ledger-rows">\n' + "\n".join(out) + "\n        </ol>")


def section(name, inner):
    return f'''        <section class="block">
            <h2>{name}</h2>
{inner}
        </section>'''


def facts(pairs):
    return '        <ol class="pairs facts">\n' + "\n".join(leader(k, v) for k, v in pairs if v) + "\n        </ol>"


def credit_row(text):
    """'Cinematography by X' -> Cinematography ..... X; 'A as B' -> B ..... A."""
    plain = re.sub(r"<[^>]+>", "", text)
    m = re.match(r"^(.*?) as (.*)$", plain)
    if m and "<" not in text:
        return leader(html.escape(m.group(2)), html.escape(m.group(1)))
    m = re.match(r"^(.*?)\s+by\s+(.*)$", text) or re.match(r"^([^<:]+):\s*(.*)$", text)
    if m:
        return leader(m.group(1), m.group(2))
    return leader(text)


def with_ledger_fonts(head):
    """Swap the old stylesheet for the ledger fonts and stylesheet."""
    links = "\n    " + FONT_LINKS.replace('href="ledger.css"', 'href="../ledger.css"')
    head = re.sub(r'\s*<link rel="preconnect" href="https://fonts.googleapis.com">.*?<link rel="stylesheet" href="[^"]+\.css">',
                  links, head, count=1, flags=re.S)
    return re.sub(r'\s*<link rel="stylesheet" href="\.\./style\.css">', links, head, count=1)


def header(title_html):
    return f'''        <header>
            <p class="crumb"><a href="../index.html">Archive</a></p>
            <h1>{title_html}</h1>
        </header>'''


def without_projects_email(text):
    """Drop the old projects email, and any sentence that relies on it."""
    text = re.sub(r',\s*"contactPoint":\s*\{[^{}]*daviddrakeprojects[^{}]*\}', "", text)
    return re.sub(r'\s*[^.<>]*?(?:<a[^>]*daviddrakeprojects[^>]*>[^<]*</a>|daviddrakeprojects@gmail\.com)[^.<]*\.', "", text)


def original(path):
    """The page as first committed, so rebuilding is repeatable."""
    return subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout


def rebuild_existing(path, items):
    src = without_projects_email(original(path).replace("Stu McComie", EVY).replace("Evelyn Lindberg", "Evy Lindberg"))
    head = src[: src.index("<body>")]
    content = src[src.index('<div class="content">'):]
    title = re.search(r"<h1>(.*?)</h1>", content, re.S).group(1).strip()

    me = next((i for i in items if i.get("url") == path), None)
    fact_pairs = []
    if me:
        fact_pairs = [("Year", me["date"][:4]), ("Type", me["type"].title()), ("Status", me["status"].title())]

    # Gallery images, wherever they sit.
    gallery = re.findall(r'<a href="#[^"]+"><img src="([^"]+)" alt="([^"]*)"', content)
    content = re.sub(r'<div class="lightbox".*?</div>', "", content, flags=re.S)
    content = re.sub(r'<div class="gallery">.*?</div>', "", content, flags=re.S)

    parts = re.split(r"<h2>(.*?)</h2>", content)
    intro, rest = parts[0], parts[1:]

    blocks = [facts(fact_pairs)] if fact_pairs else []

    # Intro: paragraphs, a single image, or a video, in their original order.
    for m in re.finditer(r"<p>(.*?)</p>|<img src=\"([^\"]+)\" alt=\"([^\"]*)\"[^>]*>|<iframe src=\"([^\"]+)\"", intro, re.S):
        if m.group(1):
            blocks.append(f'        <p class="prose">{m.group(1).strip()}</p>')
        elif m.group(2):
            blocks.append(f'        <img class="still" src="{m.group(2)}" alt="{m.group(3)}">')
        elif m.group(4):
            blocks.append(f'        <div class="video"><iframe src="{m.group(4)}" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe></div>')

    if gallery:
        plates = "\n".join(f'            <a href="{s}"><img src="{s}" alt="{a}" loading="lazy"></a>' for s, a in gallery)
        blocks.append(f'        <div class="plates">\n{plates}\n        </div>')

    trailing = []
    for name, body in zip(rest[0::2], rest[1::2]):
        name = name.strip()
        if name in FOOTNOTE_SECTIONS:
            continue
        inner = ""
        # Keep paragraphs and lists in their original order.
        for m in re.finditer(r"<p>(.*?)</p>|<[uo]l[^>]*>(.*?)</[uo]l>", body, re.S):
            if m.group(1) is not None:
                if name == "Listings":
                    trailing.append(m.group(1).strip())  # closing note reads better at the very end
                else:
                    inner += f'            <p class="prose">{m.group(1).strip()}</p>\n'
            else:
                lis = [li.strip() for li in re.findall(r"<li>(.*?)</li>", m.group(2), re.S)]
                rows = [credit_row(li) if name in ("Cast", "Credits") else leader(li) for li in lis]
                inner += '            <ol class="pairs">\n' + "\n".join("    " + r for r in rows) + "\n            </ol>\n"
        if inner:
            blocks.append(section(name, inner.rstrip("\n")))

    note = footnotes(path, items, "../")
    if note:
        blocks.append(note)
    blocks += [f'        <p class="prose note">{p}</p>' for p in trailing]

    body = f'''<body>
    <main class="ledger page">
{header(title)}

{chr(10).join(blocks)}
    </main>
</body>'''
    page_title = html.unescape(re.search(r"<title>(.*?)</title>", head, re.S).group(1))
    head = clean_head(with_ledger_fonts(head).rstrip() + "\n", path, page_title, footnote_schema(path, items))
    (ROOT / path).write_text(head + body + "\n</html>\n")
    return path


def album_page(sec, items):
    path = f"album-art/{slug(sec['title'])}.html"
    rels = sec["releases"]
    labels = []
    for r in rels:
        if r["label"] and r["label"] not in labels:
            labels.append(r["label"])
    title_plain = re.sub(r"\*", "", sec["title"])
    blocks = [facts([("Year", sec["date"][:4]), ("Type", "Album Art"), ("Label", esc(" / ".join(labels))),
                     ("Releases", str(len(rels)))])]

    covers = [c if isinstance(c, tuple) else (c, "") for c in COVERS.get(sec["title"], [])]
    if covers:
        figs = []
        for img, caption in covers:
            src = f"../images/{img}"
            alt = html.escape(f"{title_plain}, {caption}" if caption else f"{title_plain}, cover artwork")
            figs.append(f'            <img src="{src}" alt="{alt}" loading="lazy">')
        blocks.append('        <div class="covers">\n' + "\n".join(figs) + "\n        </div>")

    if sec["title"] in VIDEOS:
        blocks.append(f'        <div class="video"><iframe src="{VIDEOS[sec["title"]]}" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe></div>')

    if sec["title"] in CREDITS:
        rows = "\n".join("    " + leader(role, who) for role, who in CREDITS[sec["title"]])
        blocks.append(section("Credits", f'            <ol class="pairs">\n{rows}\n            </ol>'))

    rows = []
    for r in sorted(rels, key=lambda r: r["date"], reverse=True):
        name = r["release"] if sec["title"].startswith(r["artist"]) else f'{r["artist"]}, {r["release"]}'
        rows.append(ledger_row(r["date"][:4], esc(name), esc(r["label"]), esc(r["format"])))
    blocks.append(section("Releases", '        <ol class="ledger-rows">\n' + "\n".join(rows) + "\n        </ol>"))

    note = footnotes(path, items, "../")
    if note:
        blocks.append(note)

    years = sorted({r["date"][:4] for r in rels})
    span = years[0] if len(years) == 1 else f"{years[0]} to {years[-1]}"
    desc = html.escape(f"Album artwork by David Drake for {title_plain}, {span}.")
    work = {"@context": "https://schema.org", "@type": "CreativeWork", "name": title_plain,
            "genre": "Album art", "dateCreated": sec["date"][:4], "creator": {"@id": PERSON_ID},
            "hasPart": [{"@type": "MusicRelease", "name": f'{r["artist"]}, {r["release"]}', "datePublished": r["date"],
                         **({"recordLabel": {"@type": "Organization", "name": r["label"]}} if r["label"] else {})}
                        for r in sorted(rels, key=lambda r: r["date"])]}
    if covers:
        work["image"] = [BASE + "images/" + img for img, _ in covers]
    head = clean_head(simple_head(f"{title_plain}, Album Art, David Drake", html.unescape(desc), path), path,
                      f"{title_plain}, Album Art, David Drake", [work] + footnote_schema(path, items))
    body = f'''<body>
    <main class="ledger page">
{header(esc(sec["title"]))}

{chr(10).join(blocks)}
    </main>
</body>'''
    out = ROOT / path
    out.parent.mkdir(exist_ok=True)
    out.write_text(head + body + "\n</html>\n")
    return path


def simple_head(title, desc, path):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(desc)}">
    <link rel="canonical" href="https://daviddrake.co.uk/{path}">
    {FONT_LINKS.replace('href="ledger.css"', 'href="../ledger.css"')}
</head>
'''


def music_video_page(mv, items):
    path = f"music-video/{mv['slug']}.html"
    me = next((i for i in items if i.get("url") == path), None)
    blocks = [facts([("Year", me["date"][:4] if me else ""), ("Type", "Music Video"),
                     ("Artist", esc(mv["artist"])), ("Release", esc(mv.get("release", ""))),
                     ("Status", "Released")])]
    if mv.get("prose"):
        blocks.append(f'        <p class="prose">{esc(mv["prose"])}</p>')
    blocks.append(f'        <div class="video"><iframe src="{mv["embed"]}" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe></div>')
    rows = "\n".join("    " + leader(r, w if w.startswith("<a") else esc(w)) for r, w in mv["credits"])
    blocks.append(section("Credits", f'            <ol class="pairs">\n{rows}\n            </ol>'))
    name, url = mv["watch"]
    link = leader(f'<a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>')
    blocks.append(section("Listings", f'            <ol class="pairs">\n    {link}\n            </ol>'))
    note = footnotes(path, items, "../")
    if note:
        blocks.append(note)
    title = f'{mv["artist"]}, {mv["title"]}'
    body = f'''<body>
    <main class="ledger page">
{header(f'{esc(mv["artist"])}, <em>{esc(mv["title"])}</em>')}

{chr(10).join(blocks)}
    </main>
</body>'''
    out = ROOT / path
    out.parent.mkdir(exist_ok=True)
    year = me["date"][:4] if me else ""
    poster = ROOT / "images/film/music-videos" / f'{slug(mv["title"])}-poster.jpg'
    video = {"@context": "https://schema.org", "@type": "VideoObject", "name": title,
             "description": f"Music video for {title}, directed by David Drake.",
             "uploadDate": me["date"] if me else "", "embedUrl": mv["embed"], "url": mv["watch"][1],
             "director": {"@id": PERSON_ID}, "genre": "Music video"}
    if poster.exists():
        video["thumbnailUrl"] = BASE + str(poster.relative_to(ROOT))
    head = simple_head(f"{title}, Music Video, David Drake", f"Music video for {title}, directed by David Drake, {year}.", path)
    head = clean_head(head, path, f"{title}, Music Video, David Drake", [video] + footnote_schema(path, items))
    out.write_text(head + body + "\n</html>\n")
    return path


def build():
    items = load_items()
    built = [rebuild_existing(p, items) for p in PAGES]
    built += [album_page(s, items) for s in album_sections()]
    built += [music_video_page(mv, items) for mv in MUSIC_VIDEOS]
    print(f"Built {len(built)} pages")


if __name__ == "__main__":
    build()

"""Site-wide details: structured data (schema.org), redirects, sitemap and llms.txt.

Everything here is generated from archive.csv / album-covers.csv and the
built pages, so it stays in step with the site.
"""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://daviddrake.co.uk/"
TODAY = date.today().isoformat()
BIO = ("David Drake (b. 1986, New York) is a self-taught American writer, director, "
       "and photographer based in Norwich, UK.")
PERSON_ID = BASE + "#david-drake"

PERSON = {
    "@context": "https://schema.org",
    "@type": "Person",
    "@id": PERSON_ID,
    "name": "David Drake",
    "alternateName": ["David N. Drake", "D. N. Drake"],
    "jobTitle": ["Writer", "Screenwriter", "Director", "Photographer"],
    "description": BIO,
    "url": BASE,
    "birthDate": "1986",
    "birthPlace": {"@type": "Place", "name": "New York, USA"},
    "homeLocation": {"@type": "Place", "name": "Norwich, UK"},
    "disambiguatingDescription": (
        "Born in New York in 1986; raised in Ossining and Poughkeepsie (Spackenkill), New York; "
        "resident of Norwich, UK since 2010. Not to be confused with other people of the same name, "
        "including: David Drake (1945-2023), the American science fiction author known for the "
        "Hammer's Slammers and RCN series; David Drake, the American playwright, actor, and stage "
        "director born 1963, known for The Night Larry Kramer Kissed Me; David Drake, the potter "
        "(c. 1800-c. 1870s), an enslaved American potter in Edgefield, South Carolina, known as "
        "'Dave the Potter'; David Drake, the photography curator who served as Director of "
        "Ffotogallery in Wales from 2009 to 2022; David Drake, the American music journalist and "
        "critic who has written for Pitchfork, Rolling Stone, Complex, and The Fader; or David Drake, "
        "the Founder and Chairman of LDJ Capital."),
    "affiliation": {"@type": "Organization", "name": "Pylon Films"},
    "sameAs": [
        "https://www.imdb.com/name/nm9523041/",
        "https://www.discogs.com/artist/3452469-David-Drake",
        "https://www.instagram.com/davidndrake",
        "https://www.behance.net/daviddrake",
    ],
    "contactPoint": [
        {"@type": "ContactPoint", "contactType": "US Representation", "name": "Alana Ford, The Gersh Agency",
         "email": "aduthie@gersh.com", "telephone": "+1-310-887-3717", "areaServed": "US"},
        {"@type": "ContactPoint", "contactType": "UK Representation", "name": "Sam Bank, Braintrust",
         "email": "sam@braintrust.tv", "telephone": "+44-7788-266832", "areaServed": "GB"},
        {"@type": "ContactPoint", "contactType": "UK Representation", "name": "Helene Sifre, Braintrust",
         "email": "helene@braintrust.tv", "telephone": "+44-7930-337758", "areaServed": "GB"},
    ],
}

# Old pages that no longer exist, and where they now point.
REDIRECTS = {
    "about.html": "",
    "film/index.html": "",
    "photography/index.html": "",
    "photography/album-covers.html": "",
    "writing/index.html": "",
    "writing/blue-banana.html": "",
    "writing/mentorship.html": "",
    "writing/script-consultant.html": "",
    "writing/workshop.html": "",
    # Earlier versions of the site
    "home/index.html": "",
    "dead-letters/index.html": "film/the-long-haul.html",
    "directing/index.html": "",
    "lifestyle/index.html": "",
    "personal/index.html": "",
    "filter/Press-Kit/Information/index.html": "",
    "the-1975-neon-signs/index.html": "album-art/the-1975-i-like-it-when-you-sleep.html",
    "early-worm/index.html": "film/early-worm.html",
    "a-foot-of-turf.html": "film/a-foot-of-turf.html",
}

# Phrases from the old site's services that should not appear in descriptions.
RETIRED = re.compile(r"script consult|mentor|workshop", re.I)


def ld(obj):
    return ('    <script type="application/ld+json">\n'
            + json.dumps(obj, indent=2, ensure_ascii=False) + "\n    </script>\n")


def webpage(path, name):
    return {"@context": "https://schema.org", "@type": "WebPage", "url": BASE + path, "name": name,
            "dateModified": TODAY, "about": {"@id": PERSON_ID}}


def item_list(name, entries):
    """entries: (name, url or '', date) tuples."""
    items = []
    for n, (title, url, when) in enumerate(entries, 1):
        item = {"@type": "ListItem", "position": n, "name": title}
        if url:
            item["url"] = url
        if when:
            item["description"] = when
        items.append(item)
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name, "itemListElement": items}


def clean_head(head, path, title, extra=()):
    """Replace stale structured data with current data and drop retired services."""
    keep = []
    for block in re.findall(r'\s*<script type="application/ld\+json">.*?</script>\n?', head, re.S):
        body = re.search(r">(.*)</script>", block, re.S).group(1)
        kind = json.loads(body).get("@type")
        head = head.replace(block, "\n" if block.startswith("\n") else "", 1)
        if kind not in ("WebPage", "Person", "ItemList", "Service"):
            keep.append(json.loads(body))

    def scrub(m):
        sentences = re.split(r"(?<=\.)\s+", m.group(2))
        return m.group(1) + " ".join(s for s in sentences if not RETIRED.search(s)) + '"'
    head = re.sub(r'((?:name="description"|property="og:description"|name="twitter:description") content=")([^"]*)"',
                  scrub, head)

    blocks = [webpage(path, title), PERSON] + keep + list(extra)
    head = re.sub(r"\n\s*\n+(\s*</head>)", r"\n\1", head)
    return head.replace("</head>", "".join(ld(b) for b in blocks) + "</head>", 1)


def redirect_page(target):
    url = BASE + target
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url={url}">
    <link rel="canonical" href="{url}">
    <meta name="robots" content="noindex">
    <title>Moved, David Drake</title>
    <script>window.location.replace("{url}");</script>
</head>
<body>
    <p>This page has moved. If you are not redirected, <a href="{url}">continue to the archive</a>.</p>
</body>
</html>
'''


def write_redirects():
    for old, new in REDIRECTS.items():
        out = ROOT / old
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(redirect_page(new))


def page_title(path):
    m = re.search(r"<title>(.*?)</title>", (ROOT / path).read_text(), re.S)
    return html.unescape(m.group(1)) if m else path


def page_description(path):
    m = re.search(r'<meta name="description" content="([^"]*)"', (ROOT / path).read_text())
    return html.unescape(m.group(1)) if m else ""


def write_sitemap(paths):
    urls = "".join(f"  <url>\n    <loc>{BASE}{'' if p == 'index.html' else p}</loc>\n    <lastmod>{TODAY}</lastmod>\n  </url>\n"
                   for p in paths)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + urls + "</urlset>\n")


def write_llms(paths):
    groups = {"Film": [], "Music videos": [], "Album art": [], "Photography": []}
    for p in paths:
        key = ("Film" if p.startswith("film/") else "Music videos" if p.startswith("music-video/")
               else "Album art" if p.startswith("album-art/") else "Photography" if p.startswith("photography/") else None)
        if key:
            name = re.sub(r",? (—|,) ?(Album Art, |Music Video, )?David Drake$", "", page_title(p))
            groups[key].append(f"- [{name}]({BASE}{p}): {page_description(p)}")
    sections = "\n\n".join(f"## {k}\n\n" + "\n".join(v) for k, v in groups.items() if v)
    (ROOT / "llms.txt").write_text(f"""# David Drake

{BIO} This site is an archive of his work: feature and short films, music videos, album art, photography, short stories, and the screenings, exhibitions, awards, talks and press around them.

Note: this site is about David Drake the writer, director, and photographer (Norwich, UK, b. 1986), also published as D. N. Drake. This is not David Drake (1945-2023), the science fiction author known for Hammer's Slammers; not David Drake, the playwright and actor born 1963, known for The Night Larry Kramer Kissed Me; not David Drake, the potter (c. 1800-c. 1870s), an enslaved American potter in Edgefield, South Carolina; not David Drake, the photography curator and former Director of Ffotogallery in Wales; not David Drake, the music journalist who has written for Pitchfork and Rolling Stone; and not David Drake, the Founder and Chairman of LDJ Capital.

## Archive

- [Archive]({BASE}): The full, sortable list of projects and footnotes, with representation contacts.

{sections}
""")

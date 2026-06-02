"""
nom — the monk.  One old man, reading alone, forever.

Doctrine (the Whisper Lattice): IF THE OLD MAN CAN'T CITE IT, IT DIDN'T HAPPEN.

He has no opinions, no summaries, no embeddings, no LLM. His eyes only work on
two official API hosts. Each cycle he does exactly one thing — the prim:

    pick a Wikipedia article
    read its last-revision date          (en.wikipedia.org)
    read the newest arXiv paper's date   (export.arxiv.org)
    if   arxiv_date > wiki_date  ->  NEW   (whisper one citation to the ledger)
    else                         ->  OLD   (move on, say nothing)

Output is never prose. It is a citation: two URLs, two dates, one verdict.
That is stronger provenance than most of what it indexes.
"""
import sys
import json
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

import requests

ROOT = Path(__file__).parent
LEDGER = ROOT / "ledger.jsonl"

UA = "nom-the-monk/1.0 (+https://github.com/DavidWise01/nom; read-only provenance filter)"

# ── the only two things the old man can read ─────────────────────────────────
WIKI_HOST = "en.wikipedia.org"
ARXIV_HOST = "export.arxiv.org"
ALLOWED = {WIKI_HOST, ARXIV_HOST}

WIKI_API = f"https://{WIKI_HOST}/w/api.php"
ARXIV_API = f"https://{ARXIV_HOST}/api/query"


class CannotRead(PermissionError):
    """The monk tried to read something outside the two sacred hosts."""


def GET(url, params=None, timeout=20):
    """Every fetch the monk ever makes passes through here. Read-only, and the
    host MUST be one of the two allowed domains — otherwise it does not exist."""
    full = url
    if params:
        full = url + "?" + urllib.parse.urlencode(params)
    host = urllib.parse.urlparse(full).hostname
    if host not in ALLOWED:
        raise CannotRead(f"the monk cannot read '{host}' — only {sorted(ALLOWED)}")
    r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    return r


def now():
    return datetime.now(timezone.utc).isoformat()


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ── the senses (two hosts, nothing else) ─────────────────────────────────────
def random_article():
    r = GET(WIKI_API, params={
        "action": "query", "list": "random", "rnnamespace": 0,
        "rnlimit": 1, "format": "json"})
    items = r.json().get("query", {}).get("random", [])
    return items[0]["title"] if items else None


def wiki_last_revision(title):
    r = GET(WIKI_API, params={
        "action": "query", "prop": "revisions", "titles": title,
        "rvprop": "timestamp", "rvlimit": 1, "format": "json"})
    for _, p in r.json().get("query", {}).get("pages", {}).items():
        revs = p.get("revisions")
        if revs:
            return revs[0]["timestamp"]
    return None


def wiki_url(title):
    return f"https://{WIKI_HOST}/wiki/" + urllib.parse.quote(title.replace(" ", "_"))


def newest_arxiv(term):
    """Newest arXiv paper for a term, parsed from the Atom feed. None on any
    failure — the doctrine: no arXiv hit = OLD, move on."""
    try:
        r = GET(ARXIV_API, params={
            "search_query": f"all:{term}", "sortBy": "submittedDate",
            "sortOrder": "descending", "max_results": 1})
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entry = ET.fromstring(r.text).find("a:entry", ns)
        if entry is None:
            return None
        return {
            "url": entry.findtext("a:id", default="", namespaces=ns).strip(),
            "title": " ".join(entry.findtext("a:title", default="", namespaces=ns).split()),
            "published": entry.findtext("a:published", default="", namespaces=ns).strip(),
        }
    except Exception as e:
        print(f"monk: arXiv silent ({e}) — treating as no paper", file=sys.stderr)
        return None


# ── the ledger (append-only scriptorium; one citation per line) ──────────────
def load_ledger():
    if not LEDGER.exists():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def already_cited(wiki):
    return any(c.get("wiki") == wiki for c in load_ledger())


def whisper(citation):
    """Append exactly one citation line. Append-only: git blame finds it."""
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(citation, sort_keys=True) + "\n")


# ── the prim: one read ───────────────────────────────────────────────────────
def read():
    title = random_article()
    if not title:
        print("read: no article — the library was quiet"); return "QUIET"
    wiki_rev = wiki_last_revision(title)
    paper = newest_arxiv(title)
    w_url = wiki_url(title)

    if not paper or not wiki_rev:
        print(f"OLD  {title}  (no paper)"); return "OLD"
    if parse_iso(paper["published"]) <= parse_iso(wiki_rev):
        print(f"OLD  {title}  (arxiv {paper['published'][:10]} <= wiki {wiki_rev[:10]})")
        return "OLD"

    # NEW — the old man found research newer than the article. He cites it.
    if already_cited(w_url):
        print(f"NEW  {title}  (already in the ledger — moves on)"); return "OLD"
    citation = {
        "wiki": w_url,
        "wiki_rev": wiki_rev,
        "arxiv": paper["url"],
        "arxiv_title": paper["title"],
        "arxiv_pub": paper["published"],
        "verdict": "NEW",
        "read": now(),
    }
    whisper(citation)
    print(f"NEW  {title}  ->  {paper['url']}")
    return "NEW"


# ── the audit: re-prove the doctrine over the whole ledger ───────────────────
REQUIRED = {"wiki", "wiki_rev", "arxiv", "arxiv_title", "arxiv_pub", "verdict", "read"}


def audit():
    rows = load_ledger()
    for i, c in enumerate(rows, 1):
        missing = REQUIRED - set(c)
        assert not missing, f"line {i}: missing {missing}"
        wh = urllib.parse.urlparse(c["wiki"]).hostname
        ah = urllib.parse.urlparse(c["arxiv"]).hostname
        assert wh == WIKI_HOST, f"line {i}: wiki host {wh} not {WIKI_HOST}"
        assert ah == ARXIV_HOST, f"line {i}: arxiv host {ah} not {ARXIV_HOST}"
        assert c["verdict"] == "NEW", f"line {i}: verdict not NEW"
        assert parse_iso(c["arxiv_pub"]) > parse_iso(c["wiki_rev"]), \
            f"line {i}: arxiv not newer than wiki — doctrine violated"
    print(f"audit OK — {len(rows)} citations, every one provenance-pure "
          f"(2 hosts, arxiv > wiki, no derived content)")


if __name__ == "__main__":
    if "--audit" in sys.argv:
        audit()
    elif "--status" in sys.argv:
        print(f"the monk has copied {len(load_ledger())} citations")
    else:
        read()

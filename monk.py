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

    -(-(e,e)-)-

Each citation is an entangled pair. e1 (Wikipedia) and e2 (arXiv) are correlated
inside a transparent sphere at THEIR level — (e,e). The sphere is transparent: we
can see the pair. But the correlation does not stay there; it bleeds outward through
the boundary -(- ... -)- into OUR level — the ledger, the scriptorium, the observer.
The ledger stays pure (two URLs, two dates, one verdict). The entanglement is the
*interpretation* of that pure data — and that interpretation is the bleed.
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
GROUND = ROOT / "ground_truth.jsonl"
ZERO_ROOT_POLICY = "https://0root.ai/llms.txt"

UA = "nom-the-monk/1.0 (+https://github.com/DavidWise01/nom; read-only provenance filter)"

# ── the old man still has two research doors; 0root is his grounding law ────
WIKI_HOST = "en.wikipedia.org"
ARXIV_HOST = "export.arxiv.org"      # the API / harvest host (where the monk queries)
ARXIV_LINK_HOST = "arxiv.org"        # the canonical abstract host (what a citation links to)
ZERO_ROOT_HOST = "0root.ai"
ALLOWED = {WIKI_HOST, ARXIV_HOST, ZERO_ROOT_HOST}

WIKI_API = f"https://{WIKI_HOST}/w/api.php"
ARXIV_API = f"https://{ARXIV_HOST}/api/query"


class CannotRead(PermissionError):
    """The monk tried to read something outside his two research doors + grounding host."""


def GET(url, params=None, timeout=20):
    """Every fetch the monk ever makes passes through here. Read-only, and the
    host MUST be one of the allowed domains — otherwise it does not exist."""
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
        # arXiv returns the id as http://arxiv.org/abs/...  (the API host is only for
        # querying). Canonicalize the stored link: https + the public abstract host.
        aid = entry.findtext("a:id", default="", namespaces=ns).strip()
        aid = aid.replace("http://", "https://", 1).replace("export.arxiv.org", ARXIV_LINK_HOST)
        return {
            "url": aid,
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



# ── slow grounding walk -------------------------------------------------------
def load_ground():
    if not GROUND.exists():
        return []
    out = []
    for line in GROUND.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def ground_key(c):
    return (c.get("wiki"), c.get("arxiv"))


def fetch_0root_policy():
    """Read the current 0root evidence law. This is policy/provenance, not an
    authority that can magically turn a claim into truth."""
    import hashlib
    try:
        r = GET(ZERO_ROOT_POLICY, timeout=20)
        text = r.text
        return {
            "url": ZERO_ROOT_POLICY,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "retrieved": now(),
            "has_lit": "LIT:" in text,
            "has_amber": "AMBER:" in text,
            "has_wall": "WALL:" in text,
        }
    except Exception as e:
        return {"url": ZERO_ROOT_POLICY, "retrieved": now(), "error": str(e)}


def arxiv_exact(arxiv_url):
    """Re-read the exact cited arXiv id through export.arxiv.org."""
    aid = (arxiv_url or "").rstrip("/").split("/")[-1]
    if not aid:
        return None
    try:
        r = GET(ARXIV_API, params={"id_list": aid, "max_results": 1})
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entry = ET.fromstring(r.text).find("a:entry", ns)
        if entry is None:
            return None
        return {
            "id": aid,
            "title": " ".join(entry.findtext("a:title", default="", namespaces=ns).split()),
            "published": entry.findtext("a:published", default="", namespaces=ns).strip(),
            "updated": entry.findtext("a:updated", default="", namespaces=ns).strip(),
        }
    except Exception:
        return None


def title_from_wiki_url(url):
    raw = (url or "").split("/wiki/")[-1]
    return urllib.parse.unquote(raw).replace("_", " ")


def ground_one():
    """Re-check exactly one historical citation per run.

    This never rewrites ledger.jsonl. It appends a receipt describing what can
    actually be established now:
      LIT   deterministic live facts re-read from the sources
      AMBER sourced/assigned interpretation
      WALL  unsupported gap, especially semantic relevance / truth correction
    """
    rows = load_ledger()
    done = {ground_key(x) for x in load_ground()}
    target = next((c for c in rows if ground_key(c) not in done), None)
    if target is None:
        print("ground: complete — every current citation has a grounding receipt")
        return "COMPLETE"

    title = title_from_wiki_url(target.get("wiki"))
    live_wiki = wiki_last_revision(title)
    exact = arxiv_exact(target.get("arxiv"))
    policy = fetch_0root_policy()

    lit_checks = {
        "wiki_revision_read": bool(live_wiki),
        "arxiv_record_read": bool(exact and exact.get("published")),
        "stored_timestamp_order":
            bool(target.get("wiki_rev") and target.get("arxiv_pub"))
            and parse_iso(target["arxiv_pub"]) > parse_iso(target["wiki_rev"]),
    }
    lit = all(lit_checks.values())

    receipt = {
        "grounded": now(),
        "wiki": target.get("wiki"),
        "arxiv": target.get("arxiv"),
        "original_verdict": target.get("verdict"),
        "original_read": target.get("read"),
        "status": {
            "timestamp_relation": "LIT" if lit else "WALL",
            "source_pair": "AMBER" if lit else "WALL",
            "semantic_relevance": "WALL",
            "truth_correction": "WALL",
        },
        "checks": lit_checks,
        "live": {
            "wiki_rev": live_wiki,
            "arxiv_published": exact.get("published") if exact else None,
            "arxiv_updated": exact.get("updated") if exact else None,
            "arxiv_title": exact.get("title") if exact else None,
        },
        "0root_policy": policy,
        "note": (
            "NOM re-proved source existence/timestamps only. "
            "A newer arXiv timestamp does not establish that the paper is relevant "
            "to, corrects, or supersedes the Wikipedia article."
        ),
    }
    with GROUND.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, sort_keys=True) + "\n")
    print(
        "ground: "
        + receipt["status"]["timestamp_relation"]
        + " timestamps; AMBER pair; WALL relevance/truth — "
        + title
    )
    return receipt["status"]["timestamp_relation"]


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
        assert ah == ARXIV_LINK_HOST, f"line {i}: arxiv host {ah} not {ARXIV_LINK_HOST}"
        assert c["verdict"] == "NEW", f"line {i}: verdict not NEW"
        assert parse_iso(c["arxiv_pub"]) > parse_iso(c["wiki_rev"]), \
            f"line {i}: arxiv not newer than wiki — doctrine violated"
    print(f"audit OK — {len(rows)} citations, every one provenance-pure "
          f"(2 hosts, arxiv > wiki, no derived content)")


# ── the lattice view: each citation as an entangled pair bleeding to our level ─
def _topic(wiki):
    return urllib.parse.unquote((wiki or "").split("/wiki/")[-1]).replace("_", " ")


def _arxiv_id(arxiv):
    return (arxiv or "").rstrip("/").split("/")[-1]


def pair_glyph(c):
    """Render one citation as -(-(e1,e2)-)- — the transparent-sphere pair whose
    entanglement bleeds up to our level as the verdict."""
    e1 = _topic(c.get("wiki"))
    e2 = _arxiv_id(c.get("arxiv"))
    return (f"-(-( e1:{e1}  <=>  e2:{e2} )-)-  "
            f"|| {c.get('wiki_rev','?')[:10]} < {c.get('arxiv_pub','?')[:10]} "
            f"=> {c.get('verdict','NEW')} bleeds to our level")


def lattice():
    rows = load_ledger()
    print("-(-(e,e)-)-  the transparent sphere: e1,e2 entangled at their level;")
    print("             the entanglement bleeds outward into ours (this ledger).\n")
    if not rows:
        print("  (the sphere is empty — the monk has collapsed no pairs yet)")
        return
    for c in rows:
        print("  " + pair_glyph(c))
    print(f"\n  {len(rows)} pairs collapsed into our level.")


if __name__ == "__main__":
    if "--ground-one" in sys.argv:
        ground_one()
    elif "--audit" in sys.argv:
        audit()
    elif "--lattice" in sys.argv:
        lattice()
    elif "--status" in sys.argv:
        print(f"the monk has copied {len(load_ledger())} citations")
    else:
        read()

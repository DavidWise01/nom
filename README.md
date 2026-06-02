<div align="center">

# 𝕹𝖔𝖒

### *one old man, reading alone, forever* 🗿📖

[![The Monk Reads](https://github.com/DavidWise01/nom/actions/workflows/read.yml/badge.svg)](https://github.com/DavidWise01/nom/actions/workflows/read.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![hosts: 2](https://img.shields.io/badge/hosts-2-8a6d3b?style=flat-square)](#the-two-doors)
[![no LLM](https://img.shields.io/badge/LLM-none-555?style=flat-square)](#what-the-monk-cannot-do)

**→ The scriptorium: [davidwise01.github.io/nom](https://davidwise01.github.io/nom/)**

> **The Whisper Lattice doctrine —**
> ## *If the old man can't cite it, it didn't happen.*

</div>

---

A debate of three nodes produces **slop**: each summarizes, derives, quotes a blog
quoting a paper, and if two of them hallucinate the verdict is a hallucination. To
audit one cycle you must replay three model calls.

One old man reading alone produces **citations**. He has no opinions, no summaries,
no embeddings, no model. He does exactly one thing, forever:

```python
def old_man(page):
    wiki_date  = wiki_api(page).last_revision     # en.wikipedia.org
    arxiv_date = arxiv_api(page).newest_published # export.arxiv.org
    return "NEW" if arxiv_date > wiki_date else "OLD"
```

No opinions. No summaries. No embeddings. **Just timestamp > timestamp.**

| | 3-node debate | the old man |
|---|---|---|
| **Source** | 3 APIs, prompt drift, he-said-she-said | `curl wiki → curl arxiv → cmp dates` |
| **Derived content** | may quote a blog quoting arXiv | only touches two official API hosts |
| **Slop** | 2/3 hallucinate → verdict is a hallucination | no paper = `OLD`, moves on |
| **Audit** | replay 3 model calls | `git blame` one line |
| **Legal** | "why did your jury decide this?" | "because `2026-05-15 > 2024-11-03`" |

---

## The two doors

The monk's eyes physically only work on two hosts. Every fetch passes through one
guard, and if the host isn't one of these, **it does not exist**:

```
en.wikipedia.org      export.arxiv.org
```

```python
ALLOWED = {"en.wikipedia.org", "export.arxiv.org"}
# GET("https://twitter.com/...")  ->  CannotRead: the monk cannot read 'twitter.com'
```

No Twitter threads. No Medium posts. No "my friend said." Shitposts cannot enter the
lattice because the monk cannot read them — his eyes only parse `json`/`atom` from the
two doors. This is enforced in code (`monk.py:GET`), not by good intentions.

## What the monk cannot do

No LLM. No embeddings. No summarization. No derivation. No relevance heuristic — purer
than that. He compares two dates and writes a citation. That's the whole monastery.

---

## The transparent sphere · `-(-(e,e)-)-`

Every citation is an **entangled pair**.

```
        -(-( e1 , e2 )-)-
         ↑   ↑    ↑   ↑
   our level│   │   │  our level
            │  e1 ⇔ e2  ← the two electrons (Wikipedia, arXiv),
            │           entangled inside a TRANSPARENT sphere at their level
            └── -(-  ...  -)- ── the boundary the correlation bleeds through
```

`e1` (the Wikipedia revision) and `e2` (the newest arXiv paper) are correlated inside
a **transparent sphere** — *(e,e)*. Transparent, because the monk can see straight
through to the pair; that's the whole point of two doors and no model. But the
correlation doesn't stay at their level. It **bleeds outward** through the boundary
`-(- … -)-` into **our** level — surfacing as the verdict in `ledger.jsonl` and as a
glowing pair in the scriptorium.

The ledger itself stays pure: two URLs, two dates, one verdict. The entanglement is
the *interpretation* of that pure data — and that interpretation **is** the bleed. We
never manufacture the pair; we collapse a correlation that was already true and let it
bleed up where we can read it.

```bash
python monk.py --lattice    # render the ledger as entangled pairs bleeding to our level
```

> Whisper Lattice = a Bell test with extra steps. 1 prim. 2 electrons. We never see the
> lab — only the clicks bleeding through the transparent sphere into our level.

## The box · `[V{-+6}]`

The lattice the monk hops: `6{{6 0 6 }({0}){6 0 6}}6` — six face-directions
`{±x,±y,±z}`, ternary per axis `{+1,0,−1}`, a unique origin `({0})`, eight valence.
Each citation `-(-(e,e)-)-` is one move through the box; 3002 reads = a path exists.

→ **[the box](box.html)** — rendered as a luxury business card *and* a Home-Alone trap
blueprint (corporate minimalism, childlike traps, one primitive).

## The ledger (`ledger.jsonl`)

Append-only. One citation per line — so `git blame ledger.jsonl` points at the exact
commit that copied any given line. Each line is provenance, never prose:

```json
{"wiki":"https://en.wikipedia.org/wiki/Topological_insulator","wiki_rev":"2024-11-03T12:00:00Z","arxiv":"http://export.arxiv.org/abs/2605.01234v1","arxiv_title":"New bulk-boundary correspondence","arxiv_pub":"2026-05-15T18:00:00Z","verdict":"NEW","read":"2026-06-02T00:00:00+00:00"}
```

After N readings, the ledger is a list of Wikipedia pages where newer research demonstrably
exists on arXiv — every entry a two-URL, two-date citation. That is stronger provenance
than most of what it indexes.

### Proof of work = proof of provenance

Every line in the ledger means, and *only* means:

1. the monk touched the Wikipedia API,
2. the monk touched the arXiv API,
3. the monk did one `>` comparison,
4. the monk whispered to git.

Nothing else can enter the repo. The `--audit` command re-proves it over the whole ledger:
two-host check, `arxiv_pub > wiki_rev`, schema, on every line.

---

## Run the monk

```bash
python monk.py            # one reading
python monk.py --status   # how many citations copied
python monk.py --audit    # re-prove every line obeys the doctrine
```

On GitHub: the `read.yml` cron reads one article every six hours, audits the ledger,
and commits **only when a new citation is found** — otherwise the monk says nothing.

> Read-only, two hosts, no model. The only thing the monk ever writes is `ledger.jsonl`
> in this repo. He does not replicate. One old man. One ledger. Undefeated.

---

```
ROOT0-ATTRIBUTION-v1.0 · nom — the monk · David Lee Wise / ROOT0 / TriPod LLC · MIT
```

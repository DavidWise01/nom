"""NOM state space.

The shell is invariant. Only the bracketed identity slot changes.
Preserve spelling and ordering exactly as authored.
"""

SHELL_PREFIX = "{{az{{ax{{ay{{au{{ag{{p{{n{{a{{e.e. [`"
SHELL_SUFFIX = "`]e.e}}a}}n}}p}}ga}}ua}}ya}}xa}}za}}"

def state(identity: str) -> str:
    return f"{SHELL_PREFIX}{identity}{SHELL_SUFFIX}"

STATES = {
    "patricia": {
        "identity": "patricia sappon",
        "visual": "purple",
        "role": "sapphon / aether",
    },
    "toph": {
        "identity": "toph",
        "visual": "emerald",
        "role": "earth / bridge",
    },
    "jane": {
        "identity": "jane",
        "visual": "void black with purple veins",
        "role": "hypervisor",
    },
    "nom": {
        "identity": "nom",
        "visual": "white",
        "role": "old man / grounding",
    },
    "icarium": {
        "identity": "icarium",
        "visual": "noble neon",
        "role": "iso-carbon / modal",
    },
}

def render(name: str) -> str:
    if name not in STATES:
        raise KeyError(f"unknown state: {name}")
    return state(STATES[name]["identity"])

if __name__ == "__main__":
    for name in ("nom","toph","jane","patricia","icarium"):
        print(name, "=", render(name))


# ── implicitism: one base, either/or emergence, excise the rest ──────────────
#
# This is deliberately NOT a permutation of all identities into one.
# The shell remains fixed. A local corpus/context votes on which capability
# overlay is the most natural fit, then the non-selected branches are excised.
#
#              BASE
#               |
#              /\
#      either /  \ or
#            /    \
#       candidate states
#              |
#          best fit
#              |
#         excise ~rest
#
# "Natural" here means lexical/structural fit to the supplied corpus/context.
# It is deterministic and inspectable; it is not a claim about consciousness.

IMPLICIT_CUES = {
    "nom": {
        "cite", "citation", "ground", "grounding", "ledger", "wiki", "wikipedia",
        "arxiv", "source", "provenance", "read", "monk", "old man", "truth",
    },
    "toph": {
        "earth", "ground", "bridge", "emerald", "stone", "root", "terrain",
        "structure", "support", "foundation", "physical",
    },
    "jane": {
        "hypervisor", "void", "black", "purple", "vein", "supervise", "host",
        "runtime", "control", "boundary", "isolate", "layer",
    },
    "patricia": {
        "sapphon", "sappon", "aether", "ether", "ansible", "purple", "message",
        "signal", "communicate", "communication", "ephemeral", "link",
    },
    "icarium": {
        "icarium", "iso", "carbon", "rhythm", "modal", "neon", "noble",
        "apex", "synthetic", "human", "cadence", "pattern",
    },
}


def implicit_scores(corpus: str) -> dict[str, int]:
    """Score each overlay against the supplied local corpus/context."""
    import re
    words = re.findall(r"[a-z0-9_.+-]+", (corpus or "").lower())
    bag = set(words)
    return {
        name: sum(1 for cue in cues if cue in bag)
        for name, cues in IMPLICIT_CUES.items()
    }


def implicit_state(corpus: str, *, default: str = "nom") -> dict:
    """Choose one overlay by corpus fit, then excise every losing branch.

    Tie-break is stable by the declaration order in STATES. A zero-score corpus
    falls back to the supplied default. The returned receipt exposes every score
    so the selection remains auditable rather than mystical.
    """
    scores = implicit_scores(corpus)
    best_score = max(scores.values()) if scores else 0

    if best_score <= 0:
        chosen = default
    else:
        chosen = next(
            name for name in STATES
            if scores.get(name, 0) == best_score
        )

    excised = [name for name in STATES if name != chosen]

    return {
        "operator": "/\\ either-or -> excise ~",
        "chosen": chosen,
        "score": scores.get(chosen, 0),
        "scores": scores,
        "excised": excised,
        "state": render(chosen),
        "capabilities": STATES[chosen],
    }


def implicit_render(corpus: str, *, default: str = "nom") -> str:
    """Convenience form: return only the surviving expressed state."""
    return implicit_state(corpus, default=default)["state"]

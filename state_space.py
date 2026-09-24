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

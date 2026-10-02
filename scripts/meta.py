"""Ezzcoins meta rating: how well a card plays in FC 27 Ultimate Team, estimated from its own stats.

Same formula as metaOf() in index.html (keep the two in step). For each position the card can play,
the six face stats are weighted by what matters in that role, then skill moves, weak foot and
PlayStyle+ add or subtract a little. The card's meta is its best position's score (1-99).
"""
import math

# Outfield weights for PAC, SHO, PAS, DRI, DEF, PHY; goalkeeper weights for DIV, HAN, KIC, REF, SPD, POS.
W = {
    "ST": (.30, .30, .05, .22, 0, .13), "CF": (.28, .26, .10, .28, 0, .08),
    "LW": (.33, .20, .12, .30, 0, .05), "RW": (.33, .20, .12, .30, 0, .05),
    "LM": (.32, .15, .18, .28, .02, .05), "RM": (.32, .15, .18, .28, .02, .05),
    "CAM": (.22, .20, .25, .30, 0, .03), "CM": (.18, .10, .28, .22, .10, .12),
    "CDM": (.18, 0, .20, .10, .30, .22), "CB": (.30, 0, .07, .03, .40, .20),
    "LB": (.33, 0, .15, .14, .26, .12), "RB": (.33, 0, .15, .14, .26, .12),
    "LWB": (.33, 0, .16, .16, .23, .12), "RWB": (.33, 0, .16, .16, .23, .12),
    "GK": (.27, .15, .03, .30, .05, .20),
}
# Calibration per position, so an average card rated 75+ scores its overall rating at its own position.
OFF = {"ST": 2.0, "CF": 1.5, "LW": -1.3, "RW": -1.3, "LM": .1, "RM": .1, "CAM": 1.0, "CM": 4.0, "CDM": 5.1,
       "CB": 5.9, "LB": 2.8, "RB": 2.8, "LWB": 2.8, "RWB": 2.8, "GK": .2}
# Points per star above (or below) 3 for skill moves and weak foot.
SMWF = {"ST": (1, 1), "CF": (1, 1), "LW": (1, 1), "RW": (1, 1), "LM": (1, 1), "RM": (1, 1), "CAM": (1, 1),
        "CM": (.6, .8), "CDM": (.3, .5), "LB": (.3, .5), "RB": (.3, .5), "LWB": (.4, .5), "RWB": (.4, .5), "CB": (0, .4), "GK": (0, 0)}
PS_STRONG = {"Quick Step+", "Rapid+", "Finesse Shot+", "Technical+", "Low Driven Shot+", "Power Shot+", "Trickster+",
             "Intercept+", "Anticipate+", "Jockey+", "Bruiser+", "Footwork+", "Far Reach+", "Deflector+", "Rush Out+"}
PS_MINOR = {"Dead Ball+", "Long Throw+", "Far Throw+"}


def positions(pos, alt):
    out = []
    for p in [pos] + str(alt or "").split(","):
        p = p.strip().upper()
        if p in W and p not in out:
            out.append(p)
    return out


def meta_at(p, s, sm, wf, ps):
    if any(v is None or v == "" for v in s):
        return None
    s = [float(v) for v in s]
    v = sum(w * x for w, x in zip(W[p], s)) + OFF[p]
    if p != "GK":
        if s[0] < 70 and W[p][0] >= .25:
            v -= (70 - s[0]) * .15
        a, b = SMWF[p]
        v += a * ((sm or 3) - 3) + b * ((wf or 3) - 3)
    for name in (t.strip() for t in str(ps or "").split(",")):
        if name:
            v += .5 if name in PS_MINOR else 2 if name in PS_STRONG else 1
    return max(1, min(99, int(math.floor(v + .5))))


def meta(pos, alt, s, sm, wf, ps=""):
    """{position: score} for every position the card plays, best first; {} without all six stats."""
    sc = {p: meta_at(p, s, sm, wf, ps) for p in positions(pos, alt)}
    sc = {p: v for p, v in sc.items() if v is not None}
    return dict(sorted(sc.items(), key=lambda kv: -kv[1]))

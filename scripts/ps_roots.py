#!/usr/bin/env python3
"""Enumerate possible bi- and triconsonantal Proto-Semitic roots under toggleable
phonotactic filters (after Greenberg 1950, McCarthy's OCP work).

Inventory: the 29 consonants of the Huehnergard/Kogan reconstruction, without
the optional emphatic velar fricative *ḫ̣.

Every filter is binary (on/off). `--json` dumps the inventory, filters and
results in a shape a browsing UI can consume directly.
"""
import argparse
import itertools
import json
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class C:
    sym: str      # conventional transliteration
    ipa: str
    cls: str      # place class used by the homorganicity filters
    group: str    # (place, manner) cell; members differ only in series
    series: str   # voiceless | voiced | emphatic | resonant


INVENTORY = [
    C("p", "p", "labial", "lab-stop", "voiceless"),
    C("b", "b", "labial", "lab-stop", "voiced"),
    C("m", "m", "labial", "lab-nasal", "resonant"),
    C("t", "t", "dental", "cor-stop", "voiceless"),
    C("d", "d", "dental", "cor-stop", "voiced"),
    C("ṭ", "tʼ", "dental", "cor-stop", "emphatic"),
    C("ṯ", "θ", "dental", "interdental", "voiceless"),
    C("ḏ", "ð", "dental", "interdental", "voiced"),
    C("ṯ̣", "θʼ", "dental", "interdental", "emphatic"),
    C("s", "s", "sibilant", "sibilant", "voiceless"),
    C("z", "z", "sibilant", "sibilant", "voiced"),
    C("ṣ", "sʼ", "sibilant", "sibilant", "emphatic"),
    C("š", "ʃ", "sibilant", "postalveolar", "voiceless"),
    C("ś", "ɬ", "sibilant", "lateral-fric", "voiceless"),
    C("ṣ́", "ɬʼ", "sibilant", "lateral-fric", "emphatic"),
    C("k", "k", "dorsal", "dorsal-stop", "voiceless"),
    C("g", "g", "dorsal", "dorsal-stop", "voiced"),
    C("q", "kʼ", "dorsal", "dorsal-stop", "emphatic"),
    C("ḫ", "x~χ", "dorsal", "dorsal-fric", "voiceless"),
    C("ǵ", "ɣ~ʁ", "dorsal", "dorsal-fric", "voiced"),
    C("ʔ", "ʔ", "guttural", "glottal-stop", "voiceless"),
    C("h", "h", "guttural", "glottal-fric", "voiceless"),
    C("ḥ", "ħ", "guttural", "pharyngeal", "voiceless"),
    C("ʕ", "ʕ", "guttural", "pharyngeal", "voiced"),
    C("n", "n", "liquid", "n", "resonant"),
    C("r", "r", "liquid", "r", "resonant"),
    C("l", "l", "liquid", "l", "resonant"),
    C("w", "w", "glide", "w", "resonant"),
    C("y", "j", "glide", "y", "resonant"),
]
assert len(INVENTORY) == 29

EMPHATIC = {c.sym for c in INVENTORY if c.series == "emphatic"}
BY_SYM = {c.sym: c for c in INVENTORY}


def same_cls(a, b, classes):
    return a.cls == b.cls and a.cls in classes


def adjacent(cs):
    return zip(cs, cs[1:])


def pairs(cs):
    return itertools.combinations(cs, 2)


def n_of(cs, pred):
    return sum(pred(x) for x in cs)


# Each filter: key -> (description, predicate(cs) -> True if the root is ALLOWED,
# root lengths it applies to). `cs` is a tuple of 2 or 3 consonants.
# Place classes the filters act on. `liquid` is only a class if its own filter
# is on, `glide` has its own filter, so the generic ones list neither.
PLACE = {"labial", "dental", "sibilant", "dorsal"}
BOTH = (2, 3)
FILTERS = {
    "no-c1c2-identical": (
        "C1 ≠ C2",
        lambda cs: cs[0] != cs[1], BOTH),
    "no-c2c3-identical": (
        "C2 ≠ C3 (bans geminate roots)",
        lambda cs: cs[1] != cs[2], (3,)),
    "no-c1c3-identical": (
        "C1 ≠ C3",
        lambda cs: cs[0] != cs[2], (3,)),
    "no-adjacent-homorganic": (
        "no same-place-class pair in adjacent positions (labial, dental, sibilant, dorsal)",
        lambda cs: not any(same_cls(x, y, PLACE) for x, y in adjacent(cs)), BOTH),
    "no-c1c3-homorganic": (
        "no same-place-class pair in C1–C3",
        lambda cs: not same_cls(cs[0], cs[2], PLACE), (3,)),
    "no-minimal-pair": (
        "no two consonants differing only in voicing/emphasis, in any position",
        lambda cs: not any(x.group == y.group and x != y for x, y in pairs(cs)), BOTH),
    "one-emphatic": (
        "at most one emphatic (ṭ q ṣ ṯ̣ ṣ́) per root",
        lambda cs: n_of(cs, lambda x: x.sym in EMPHATIC) <= 1, BOTH),
    "one-guttural": (
        "at most one guttural (ʔ h ḥ ʕ) per root",
        lambda cs: n_of(cs, lambda x: x.cls == "guttural") <= 1, BOTH),
    "one-glide": (
        "w and y do not both occur in a root",
        lambda cs: n_of(cs, lambda x: x.cls == "glide") <= 1, BOTH),
    "no-liquid-pair": (
        "n, r, l treated as one class: at most one per root (off by default; "
        "Arabic combines them freely)",
        lambda cs: n_of(cs, lambda x: x.cls == "liquid") <= 1, BOTH),
}
# Default state, following the discussion: C2=C3 and C1=C3 are attested, and
# liquids combine freely, so those start off.
DEFAULT_ON = [k for k in FILTERS
              if k not in ("no-c2c3-identical", "no-c1c3-identical", "no-liquid-pair")]


def roots(active, lengths=(3,)):
    for n in lengths:
        preds = [FILTERS[k][1] for k in active if n in FILTERS[k][2]]
        for t in itertools.product(INVENTORY, repeat=n):
            if all(p(t) for p in preds):
                yield t


def count(active, lengths=(3,)):
    return sum(1 for _ in roots(active, lengths))


def report(active, lengths):
    base = count([], lengths)
    shown = " + ".join(f"{len(INVENTORY)}^{n}" for n in lengths)
    print(f"Inventory: {len(INVENTORY)} consonants; unfiltered: {base:,} roots ({shown})\n")
    print(f"{'filter':<26}{'alone':>9}{'cumulative':>12}  (cumulative in listed order)")
    cum = []
    for k in active:
        cum.append(k)
        print(f"{k:<26}{count([k], lengths):>9,}{count(cum, lengths):>12,}")
    print(f"\nActive: {', '.join(active) or '(none)'}")
    n = count(active, lengths)
    print(f"Surviving roots: {n:,}  ({n / base:.1%} of {base:,})")
    if len(lengths) > 1:
        print("  " + ", ".join(f"{count(active, (m,)):,} with {m} consonants" for m in lengths))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--on", help="comma-separated filters to enable (replaces defaults)")
    ap.add_argument("--add", help="comma-separated filters to enable on top of defaults")
    ap.add_argument("--drop", help="comma-separated filters to disable from defaults")
    ap.add_argument("--all", action="store_true", help="enable every filter")
    ap.add_argument("--length", choices=["2", "3", "both"], default="both",
                    help="root length(s) to enumerate (default: both)")
    ap.add_argument("--list", action="store_true", help="list filters and exit")
    ap.add_argument("--show", type=int, metavar="N", help="print N surviving roots")
    ap.add_argument("--json", metavar="PATH", help="write inventory/filters/roots as JSON")
    args = ap.parse_args(argv)

    if args.list:
        for k, (desc, _, ns) in FILTERS.items():
            only = "" if ns == BOTH else " [3-consonant roots only]"
            print(f"{'*' if k in DEFAULT_ON else ' '} {k:<26}{desc}{only}")
        print("\n* = on by default")
        return
    split = lambda s: [x for x in (s or "").split(",") if x]
    active = list(FILTERS) if args.all else split(args.on) if args.on is not None else list(DEFAULT_ON)
    active += [k for k in split(args.add) if k not in active]
    active = [k for k in active if k not in split(args.drop)]
    bad = [k for k in active if k not in FILTERS]
    if bad:
        sys.exit(f"unknown filter(s): {', '.join(bad)} (try --list)")
    active.sort(key=list(FILTERS).index)

    lengths = BOTH if args.length == "both" else (int(args.length),)
    report(active, lengths)
    if args.show:
        print()
        for r in itertools.islice(roots(active, lengths), args.show):
            print("-".join(c.sym for c in r))
    if args.json:
        out = {
            "inventory": [vars(c) for c in INVENTORY],
            "filters": {k: {"description": d, "lengths": list(ns)} for k, (d, _, ns) in FILTERS.items()},
            "active": active,
            "lengths": list(lengths),
            "roots": ["-".join(c.sym for c in r) for r in roots(active, lengths)],
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

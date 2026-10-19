#!/usr/bin/env python3
"""Enumerate possible triconsonantal Proto-Semitic roots under toggleable
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


# Each filter: key -> (description, predicate(c1, c2, c3) -> True if root is ALLOWED)
# Place classes the filters act on. `liquid` is only a class if its own filter
# is on, `glide` has its own filter, so the generic ones list neither.
PLACE = {"labial", "dental", "sibilant", "dorsal"}
FILTERS = {
    "no-c1c2-identical": (
        "C1 ≠ C2",
        lambda a, b, c: a != b),
    "no-c2c3-identical": (
        "C2 ≠ C3 (bans geminate roots)",
        lambda a, b, c: b != c),
    "no-c1c3-identical": (
        "C1 ≠ C3",
        lambda a, b, c: a != c),
    "no-adjacent-homorganic": (
        "no same-place-class pair in C1–C2 or C2–C3 (labial, dental, sibilant, dorsal)",
        lambda a, b, c: not (same_cls(a, b, PLACE) or same_cls(b, c, PLACE))),
    "no-c1c3-homorganic": (
        "no same-place-class pair in C1–C3",
        lambda a, b, c: not same_cls(a, c, PLACE)),
    "no-minimal-pair": (
        "no two consonants differing only in voicing/emphasis, in any position",
        lambda a, b, c: not any(x.group == y.group and x != y
                                for x, y in ((a, b), (b, c), (a, c)))),
    "one-emphatic": (
        "at most one emphatic (ṭ q ṣ ṯ̣ ṣ́) per root",
        lambda a, b, c: sum(x.sym in EMPHATIC for x in (a, b, c)) <= 1),
    "one-guttural": (
        "at most one guttural (ʔ h ḥ ʕ) per root",
        lambda a, b, c: sum(x.cls == "guttural" for x in (a, b, c)) <= 1),
    "one-glide": (
        "w and y do not both occur in a root",
        lambda a, b, c: sum(x.cls == "glide" for x in (a, b, c)) <= 1),
    "no-liquid-pair": (
        "n, r, l treated as one class: at most one per root (off by default; "
        "Arabic combines them freely)",
        lambda a, b, c: sum(x.cls == "liquid" for x in (a, b, c)) <= 1),
}
# Default state, following the discussion: C2=C3 and C1=C3 are attested, and
# liquids combine freely, so those start off.
DEFAULT_ON = [k for k in FILTERS
              if k not in ("no-c2c3-identical", "no-c1c3-identical", "no-liquid-pair")]


def roots(active):
    preds = [FILTERS[k][1] for k in active]
    for t in itertools.product(INVENTORY, repeat=3):
        if all(p(*t) for p in preds):
            yield t


def count(active):
    return sum(1 for _ in roots(active))


def report(active):
    base = count([])
    print(f"Inventory: {len(INVENTORY)} consonants; unfiltered: {base:,} roots\n")
    print(f"{'filter':<26}{'alone':>9}{'cumulative':>12}  (cumulative in listed order)")
    cum = []
    for k in active:
        cum.append(k)
        print(f"{k:<26}{count([k]):>9,}{count(cum):>12,}")
    print(f"\nActive: {', '.join(active) or '(none)'}")
    n = count(active)
    print(f"Surviving roots: {n:,}  ({n / base:.1%} of {base:,})")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--on", help="comma-separated filters to enable (replaces defaults)")
    ap.add_argument("--add", help="comma-separated filters to enable on top of defaults")
    ap.add_argument("--drop", help="comma-separated filters to disable from defaults")
    ap.add_argument("--all", action="store_true", help="enable every filter")
    ap.add_argument("--list", action="store_true", help="list filters and exit")
    ap.add_argument("--show", type=int, metavar="N", help="print N surviving roots")
    ap.add_argument("--json", metavar="PATH", help="write inventory/filters/roots as JSON")
    args = ap.parse_args(argv)

    if args.list:
        for k, (desc, _) in FILTERS.items():
            print(f"{'*' if k in DEFAULT_ON else ' '} {k:<26}{desc}")
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

    report(active)
    if args.show:
        print()
        for r in itertools.islice(roots(active), args.show):
            print("".join(c.sym for c in r))
    if args.json:
        out = {
            "inventory": [vars(c) for c in INVENTORY],
            "filters": {k: d for k, (d, _) in FILTERS.items()},
            "active": active,
            "roots": ["".join(c.sym for c in r) for r in roots(active)],
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

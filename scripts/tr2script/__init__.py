"""Transliteration -> native script converters for the Semitic languages cited in the SED / SEDonline.
Each converter returns None when it cannot convert the input exactly (unknown letter, ambiguous vowel): it never guesses.
  ethiopic  Latin -> Ethiopic (inverse of Wiktionary's Module:Ethi-translit; snapshot in data/scripts/ethi_translit.json)
  abjad     consonantal Latin -> Hebrew/Aramaic, Syriac, Ugaritic, Phoenician, Old South Arabian

A form written with variants (optional material in brackets, šuš(š), mālē(ˀ); alternatives with a slash, mwt/myt) is converted
through same_spelling(): every reading is converted, and the result is used only when they all give the same script form.
Readings that differ in spelling ((a)dāmäsä, däm/dämät) are refused, as before.
"""
import itertools, re

def readings(form):
    """Every reading of a form with variants: each (...) group optional, and a slash splitting the whole form into alternatives.
    A form without either notation, or with spaces (prose such as "šḳy (aph.)" or "/reading/" glosses), is returned as is."""
    if " " in form or not re.search(r"[()/]", form):
        return [form]
    out = []
    for alt in form.split("/"):
        parts = re.split(r"\(([^()]*)\)", alt)                    # text, optional, text, optional, ...
        for pick in itertools.product(*[("", x) if i % 2 else (x,) for i, x in enumerate(parts)]):
            out.append("".join(pick))
    return out

def same_spelling(convert, form):
    """convert(form) if the form has one reading; with variants, the script form all readings share, or None."""
    rs = readings(form)
    if len(rs) == 1:
        return convert(rs[0])
    got = {convert(r) for r in rs}
    return got.pop() if len(got) == 1 else None


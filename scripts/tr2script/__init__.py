"""Transliteration -> native script converters for the Semitic languages cited in the SED / SEDonline.
Each converter returns None when it cannot convert the input exactly (unknown letter, ambiguous vowel): it never guesses.
  ethiopic  Latin -> Ethiopic (inverse of Wiktionary's Module:Ethi-translit; snapshot in data/scripts/ethi_translit.json)
  abjad     consonantal Latin -> Hebrew/Aramaic, Syriac, Ugaritic, Phoenician, Old South Arabian
"""

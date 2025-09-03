# Edge directionality mapping for graph traversal and sorting
EDGE_DIRECTION = {
    "parent-of": 5,         # downstream (from parent to child)
    "child-of": -5,         # upstream (from child to parent)
    "married-to": 0,        # neutral (peer)
    "descendant-of": -10,   # strong upstream (from descendant to ancestor)
    "ancestor-of": 10,      # strong downstream (from ancestor to descendant)
    # Add more edge types as needed
}
# associations_lang.py
# Language dictionary for the 'Associations' section header and related terms

ASSOCIATIONS_LANG = {
    "married-to": {
        "en": "married to",
        "hbo": "נשוי ל",
        "grc": "ἔγγαμος με"
    },
    "parent-of": {
        "en": "parent of",
        "hbo": "הורה של",
        "grc": "γονέας τοῦ"
    },
    "child-of": {
        "en": "child of",
        "hbo": "ילד של",
        "grc": "τέκνον τοῦ"
    },
    "resident-of": {
        "en": "resident of",
        "hbo": "תושב של",
        "grc": "κάτοικος τοῦ"
    },
    "member-of": {
        "en": "member of",
        "hbo": "חבר ב",
        "grc": "μέλος τοῦ"
    },
    "assisted": {
        "en": "assisted",
        "hbo": "עזר ל",
        "grc": "βοήθησε"
    },
    "name-shared-with": {
        "en": "name shared with",
        "hbo": "שם משותף עם",
        "grc": "ὄνομα κοινὸν με"
    },
    "ancestor-of": {
        "en": "ancestor of",
        "hbo": "אב קדמון של",
        "grc": "πρόγονος τοῦ"
    },
    "example-of": {
        "en": "example of",
        "hbo": "דוגמה ל",
        "grc": "παράδειγμα τοῦ"
    },
    "hid": {
        "en": "hid",
        "hbo": "הסתיר",
        "grc": "ἔκρυψε"
    }
}

ASSOCIATIONS_FAMILY = [
    "parent-of",
    "child-of",
    "sibling-of",
    "married-to",
    "descendant-of",
    "ancestor-of",
]

# Reciprocal edge mapping
RECIPROCALS = {
    "parent-of": "child-of",
    "child-of": "parent-of",
    "ancestor-of": "descendant-of",
    "descendant-of": "ancestor-of",
    "married-to": "married-to",
}

# Add more terms or languages as needed

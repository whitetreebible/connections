from enum import Enum

class EdgeType(Enum):
    # Family
    PARENT_OF = "parent-of"
    CHILD_OF = "child-of"
    ANCESTOR_OF = "ancestor-of"
    DESCENDANT_OF = "descendant-of"
    MARRIED_TO = "married-to"
    RELATED_TO = "related-to"        # general kinship--only use if no closer relationship cited directly

    # Social / Political
    MEMBER_OF = "member-of"
    LEADER_OF = "leader-of"
    LED_BY = "led-by"
    ALLY_OF = "ally-of"
    ENEMY_OF = "enemy-of"
    CONTEMPORARY_OF = "contemporary-of"
    ORIGIN_OF = "origin-of"                 # founder /source of a people/group/role
    ASSOCIATED_WITH = "associated-with"     # functional or vocational link (looser than "resident-of")

    # Geographic
    RESIDENT_OF = "resident-of"
    VISITED = "visited"           # Temporary residence, travel to a place
    BORN_IN = "born-in"           # Place of birth
    DIED_IN = "died-in"           # Place of death
    BURIED_IN = "buried-in"       # Place of burial
    NEAR = "near"                 # Geographic proximity

    # Vocational / Functional
    ROLE_AS = "role-as"
    WORKED_WITH = "worked-with"     # Symmetric, mutual ongoing vocational or ministry partnership
    ASSISTED = "assisted"           # Asymmetrical, temporary or situational

    # Action-based (Event/Interaction)
    TAUGHT = "taught"               # Asymmetrical, e.g. teacher → student
    LEARNED_FROM = "learned-from"   # Asymmetrical, e.g. student → teacher
    SENT = "sent"                   # Asymmetrical, sender → sent person
    RECEIVED_FROM = "received-from" # Asymmetrical, recipient → sender
    GAVE_TO = "gave-to"             # Asymmetrical, giver → receiver
    BLESSED = "blessed"             # Asymmetrical, blesser → blessed
    CURSED = "cursed"               # Asymmetrical, curser → cursed
    ANOINTED = "anointed"           # Asymmetrical, anointer → anointed
    APPOINTED = "appointed"         # Asymmetrical, appointer → appointed
    JUDGED = "judged"               # Asymmetrical, judge → judged
    HEALED = "healed"               # Asymmetrical, healer → healed
    PERSECUTED = "persecuted"       # Asymmetrical, persecutor → persecuted
    SAVED = "saved"                 # Asymmetrical, savior → saved
    KILLED = "killed"               # Asymmetrical, killer → killed
    CREATED = "created"             # Asymmetrical, creator → created
    DEFEATED = "defeated"           # Asymmetrical, victor → defeated
    PROMISED = "promised"           # Asymmetrical, promiser → promised
    ATTACKED = "attacked"           # Asymmetrical, attacker → attacked
    LOVED = "loved"                 # Asymmetrical, lover → loved

    # Textual / Symbolic
    NAME_MATCHES = "name-matches"
    TYPE_OF = "type-of"
    ANTITYPE_OF = "antitype-of"
    EXAMPLE_OF = "example-of"
    MENTIONED_WITH = "mentioned-with"
    CITED = "cited"                     # Textual citation, e.g. NT citing OT, direct or indirect
    
    def __str__(self):
        return self.value
    
    def for_lang(self, lang: str = "en", capitalize = False) -> str:
        value = EDGE_TYPE_LANG_LABELS.get(lang, {}).get(self, self.value)
        if capitalize:
            value = value.capitalize()
        return value


class EdgeGroups(Enum):
    FAMILY = "family"
    SOCIAL = "social/political"
    GEOGRAPHIC = "geographic"
    VOCATIONAL = "vocational/functional"

    ACTION = "action/event"
    TEXTUAL = "textual/symbolic"

    def __str__(self):
        return self.value
    
    def for_lang(self, lang: str = "en", capitalize = False) -> str:
        value = EDGE_GROUPS_LANG_LABELS.get(lang, {}).get(self, self.value)
        if capitalize:
            value = value.capitalize()
        return value



# Groupings for filtering (charts, UI)
EDGE_GROUPS_ASSOCIATIONS = {
    EdgeGroups.FAMILY: {
        EdgeType.PARENT_OF,
        EdgeType.CHILD_OF,
        EdgeType.ANCESTOR_OF,
        EdgeType.DESCENDANT_OF,
        EdgeType.MARRIED_TO,
        EdgeType.RELATED_TO,
    },
    EdgeGroups.SOCIAL: {
        EdgeType.MEMBER_OF,
        EdgeType.LEADER_OF,
        EdgeType.LED_BY,
        EdgeType.ALLY_OF,
        EdgeType.ENEMY_OF,
        EdgeType.CONTEMPORARY_OF,
        EdgeType.ORIGIN_OF,
    },
    EdgeGroups.GEOGRAPHIC: {
        EdgeType.RESIDENT_OF,
        EdgeType.VISITED,
        EdgeType.BORN_IN,
        EdgeType.DIED_IN,
        EdgeType.BURIED_IN,
        EdgeType.NEAR,
    },
    EdgeGroups.VOCATIONAL: {
        EdgeType.ROLE_AS,
        EdgeType.WORKED_WITH,
        EdgeType.ASSISTED,
    },
    EdgeGroups.ACTION: {
        EdgeType.TAUGHT,
        EdgeType.LEARNED_FROM,
        EdgeType.SENT,
        EdgeType.RECEIVED_FROM,
        EdgeType.BLESSED,
        EdgeType.CURSED,
        EdgeType.ANOINTED,
        EdgeType.APPOINTED,
        EdgeType.JUDGED,
        EdgeType.HEALED,
        EdgeType.PERSECUTED,
        EdgeType.SAVED,
        EdgeType.KILLED,
        EdgeType.CREATED,
        EdgeType.DEFEATED,
        EdgeType.PROMISED,
        EdgeType.ATTACKED,
        EdgeType.LOVED,
    },
    EdgeGroups.TEXTUAL: {
        EdgeType.NAME_MATCHES,
        EdgeType.TYPE_OF,
        EdgeType.ANTITYPE_OF,
        EdgeType.EXAMPLE_OF,
        EdgeType.MENTIONED_WITH,
        EdgeType.ASSOCIATED_WITH,
    },
}



# Reciprocal mapping (bidirectional relationships)
RECIPROCALS = {
    EdgeType.PARENT_OF: EdgeType.CHILD_OF,
    EdgeType.CHILD_OF: EdgeType.PARENT_OF,
    EdgeType.ANCESTOR_OF: EdgeType.DESCENDANT_OF,
    EdgeType.DESCENDANT_OF: EdgeType.ANCESTOR_OF,
    EdgeType.LEADER_OF: EdgeType.LED_BY,
    EdgeType.LED_BY: EdgeType.LEADER_OF,
    EdgeType.RESIDENT_OF: EdgeType.ASSOCIATED_WITH,
    EdgeType.ALLY_OF: EdgeType.ALLY_OF,                 # symmetric
    EdgeType.ENEMY_OF: EdgeType.ENEMY_OF,               # symmetric
    EdgeType.MARRIED_TO: EdgeType.MARRIED_TO,           # symmetric
    EdgeType.CONTEMPORARY_OF: EdgeType.CONTEMPORARY_OF, # symmetric
    EdgeType.WORKED_WITH: EdgeType.WORKED_WITH,         # symmetric
    EdgeType.NAME_MATCHES: EdgeType.NAME_MATCHES,       # symmetric
    EdgeType.MENTIONED_WITH: EdgeType.MENTIONED_WITH,   # symmetric
}



# Localized labels (example: English, Hebrew, Spanish, etc.)
EDGE_TYPE_LANG_LABELS = {
    "en": {
        # Family
        EdgeType.PARENT_OF: "parent of",
        EdgeType.CHILD_OF: "child of",
        EdgeType.ANCESTOR_OF: "ancestor of",
        EdgeType.DESCENDANT_OF: "descendant of",
        EdgeType.MARRIED_TO: "married to",
        EdgeType.RELATED_TO: "related to",
        # Social / Political
        EdgeType.MEMBER_OF: "member of",
        EdgeType.LEADER_OF: "leader of",
        EdgeType.LED_BY: "led by",
        EdgeType.ALLY_OF: "ally of",
        EdgeType.ENEMY_OF: "enemy of",
        EdgeType.CONTEMPORARY_OF: "contemporary of",
        EdgeType.ORIGIN_OF: "origin of",
        EdgeType.ASSOCIATED_WITH: "associated with",
        EdgeType.BLESSED: "blessed",
        EdgeType.CURSED: "cursed",
        # Geographic
        EdgeType.RESIDENT_OF: "resident of",
        EdgeType.VISITED: "visited",
        EdgeType.BORN_IN: "born in",
        EdgeType.DIED_IN: "died in",
        EdgeType.BURIED_IN: "buried in",
        # Vocational / Functional
        EdgeType.ROLE_AS: "role as",
        EdgeType.WORKED_WITH: "worked with",
        EdgeType.ASSISTED: "assisted",
        EdgeType.CREATED: "created",
        # Textual / Symbolic
        EdgeType.NAME_MATCHES: "name matches",
        EdgeType.TYPE_OF: "type of",
        EdgeType.ANTITYPE_OF: "antitype of",
        EdgeType.EXAMPLE_OF: "example of",
        EdgeType.MENTIONED_WITH: "mentioned with",
        EdgeType.CITED: "cited",
    },
    "es": {
        # Family
        EdgeType.PARENT_OF: "padre/madre de",
        EdgeType.CHILD_OF: "hijo/hija de",
        EdgeType.ANCESTOR_OF: "antepasado de",
        EdgeType.DESCENDANT_OF: "descendiente de",
        EdgeType.MARRIED_TO: "casado con",
        EdgeType.RELATED_TO: "relacionado con",
        # Social / Political
        EdgeType.MEMBER_OF: "miembro de",
        EdgeType.LEADER_OF: "líder de",
        EdgeType.LED_BY: "liderado por",
        EdgeType.ALLY_OF: "aliado de",
        EdgeType.ENEMY_OF: "enemigo de",
        EdgeType.CONTEMPORARY_OF: "contemporáneo de",
        EdgeType.ORIGIN_OF: "origen de",
        EdgeType.ASSOCIATED_WITH: "asociado con",
        EdgeType.BLESSED: "bendito",
        EdgeType.CURSED: "maldito",
        # Geographic
        EdgeType.RESIDENT_OF: "residente de",
        EdgeType.VISITED: "visitado",
        EdgeType.BORN_IN: "nacido en",
        EdgeType.DIED_IN: "fallecido en",
        EdgeType.BURIED_IN: "enterrado en",
        # Vocational / Functional
        EdgeType.ROLE_AS: "rol como",
        EdgeType.WORKED_WITH: "trabajó con",
        EdgeType.ASSISTED: "asistió a",
        # Textual / Symbolic
        EdgeType.NAME_MATCHES: "nombre coincide con",
        EdgeType.TYPE_OF: "tipo de",
        EdgeType.ANTITYPE_OF: "antitipo de",
        EdgeType.EXAMPLE_OF: "ejemplo de",
        EdgeType.MENTIONED_WITH: "mencionado con",
        EdgeType.CITED: "citó",
        EdgeType.CREATED: "creód",
    }
}


EDGE_GROUPS_LANG_LABELS = {
    "en": {
        EdgeGroups.FAMILY: "family",
        EdgeGroups.SOCIAL: "social / political",
        EdgeGroups.GEOGRAPHIC: "geographic",
        EdgeGroups.VOCATIONAL: "vocational / functional",
        EdgeGroups.ACTION: "action / event",
        EdgeGroups.TEXTUAL: "textual / symbolic",
    },
    "es": {
        EdgeGroups.FAMILY: "familia",
        EdgeGroups.SOCIAL: "social / político",
        EdgeGroups.GEOGRAPHIC: "geográfico",
        EdgeGroups.VOCATIONAL: "vocacional / funcional",
        EdgeGroups.ACTION: "acción / evento",
        EdgeGroups.TEXTUAL: "textual / simbólico",
    }
}
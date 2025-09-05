# Schema

This document describes the structure of the YAML files used in the **Bible Atlas** project. Each file represents a “page” (person, place, theme, or concept) and contains multilingual content, references, edges, and footnotes.

---

## Top-Level Structure

```yaml
id: <unique_identifier>        # A unique ID for the node/page
type: <type>                  # Type of node: person, place, theme, etc.
names:                        # Multilingual names for the node
description: <text>           # Multilingual description (main text)
edges:                        # List of connections to other nodes
footnotes:                    # List of footnotes and scholarly references
```

# Fields

## id
Type: string
Description: Unique identifier for the page. Should be lowercase and use underscores to separate words. Example: rahab.

## type
Type: string
Description: The type of node. Examples: person, place, theme.

## names
Type: dictionary
Description: Names of the node in different languages.
Example:
names:
  he: רָחָב          # Ancient Hebrew
  grc: Ῥαὰβ        # Ancient Greek
  en: Rahab         # English
  id: Rahab         # Indonesian

## description
Type: string (multiline)
Description: Main narrative for the page, supports inline links to other pages and Bible references.
Syntax:
Link to another node/page: [[node_id]]
Link to a Bible verse: [[bible:Book Chapter:Verse]]
Inline footnote reference: [^footnote_id]
Example:
```
description: |
  Rahab was a [[canaanite]] woman in [[jericho]] who hid the [[israelite]] spies sent by [[bible:Joshua 2]]. 
  Scholars note that she should not be confused with the [[rahab_monster]] mentioned in [[bible:Psalm 89:10]] and [[bible:Job 26:12]]. [^hamilton_handbook]
```

## edges
Type: list of dictionaries
Description: Connections to other nodes/pages, representing relationships, affiliations, actions, or examples.
Fields:
target → The ID of the connected node/page.
type → The type of connection (e.g., resident-of, ancestor-of, married-to).
refs → List of references related to this edge; can include Bible links [[bible:Book Chapter:Verse]] or footnote references [^footnote_id].
Example:
```
edges:
  - target: jericho
    type: resident-of
    refs:
      - "bible:Joshua 2"
      - "footnote:hamilton_handbook"
```

## footnotes
Type: dictionary
Description: Stores all footnotes and academic/extrabiblical references for the node.
Fields:
id → Unique key for the footnote (used in the description or edges as [^id])
type → Type of footnote (academic, extra-biblical, etc.)
text → Multilingual dictionary of the footnote text.
Example:
```
footnotes:
  hamilton_handbook:
    type: academic
    text:
      en: "'To retain the traditional understanding of zonah as “prostitute,” ...' (Victor P. Hamilton, Handbook on the Historical Books, 2001, 22.)"
      id: "'Untuk mempertahankan pemahaman tradisional zonah sebagai “pelacur,” ...' (Victor P. Hamilton, Buku Panduan Kitab Sejarah, 2001, 22.)"
```

## Notes on Best Practices
Localization:
Use consistent language codes: en for English, id for Indonesian, he for ancient Hebrew, grc for ancient Greek.
Include footnotes in multiple languages when possible.

References:
Use [[bible:Book Chapter:Verse]] for Bible references.
Use [^\<footnote_id>] for academic, scholarly, or extra-biblical sources.

Edges:
All edges should point to other node IDs, not plain text.
Include references for edges to capture scholarly context or scriptural support.
ID Disambiguation:
Keep IDs unique and descriptive. Example: person/rahab vs creature/rahab.
Extensibility:
Future expansion may include additional languages, edge types, or node types.
Footnotes and edges allow you to centralize translation and reference management.

# Schema
Here is the schema for the nodes in the yaml network to connect a piece of information into the web of people, places, and themes in the Bible.

```yml
# Node Schema Template for Bible Atlas (Edges-only relationships, disambiguated IDs)

id: unique_node_id   # BEST PRACTICE: make this descriptive to disambiguate similar names, e.g., "ahab_king_of_israel" vs "ahab_father_of_jehu"
type: person          # person | tribe | place | theme

names:
  hebrew: ""
  greek: ""
  english: ""

refs:
  bib: []         # compact refs, e.g., ["Joshua 2:1-21", "Matthew 1:5"]
  extra_bib: []   # long-form refs
  academic: []         # long-form refs


description: |   # main wiki-style paragraph(s), supports [[id]] links
  "Insert full paragraph describing the node here, referencing other nodes using [[node_id]]."

# Notes as an array, allowing multiple contributors or perspectives
notes: 
  - "Example note 1"
  - "Example note 2"

# Flags as an array of strings, recommended options: tentative, disputed, mythic, apocryphal
flags: []

# Connections to other nodes
edges:
  - target: ""         # id of target node
    type: ""           # nature of connection, e.g., "father-of", "tribe-of", "maybe-same"
    strength: strong   # strong | weak
    refs:
      bib: []
      extra_bib: []
      academic: []


```


## Notes for Contributors
- id must be unique across all nodes.
- type determines the folder generated in docs/ (person, tribe, place, theme).
- edges can point to any other node by id. Multiple edges allowed.
- strength: use strong for clear, canonical connections; weak for uncertain or indirect connections.
- flags help with disambiguation or marking nodes that may require special handling in graphs.
- group is optional but useful for tribes, families, or thematic clusters.

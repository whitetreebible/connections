# Connections

**Connections** is an open, relational knowledge base of biblical figures, places, tribes, and themes. It combines structured YAML data with automatically generated factsheets and graph visualizations to help scholars, students, and enthusiasts explore the Bible in a new way.

## Features

- **Node Factsheets**: Each person, place, or concept has a structured page with references, relationships, and disambiguation notes.
- **Graph Visualizations**: Explore genealogies, tribal affiliations, and thematic connections using Mermaid/Cytoscape graphs.
- **Multi-language Support**: Hebrew, Greek, and English names included for canonical figures.
- **Static Site**: Built with MkDocs and served via GitHub Pages for offline-friendly access.
- **Open Contribution**: YAML-based nodes and edges allow peer-reviewed contributions via GitHub.

## Repo Structure
```sh
whitetreebible/connections/
├── data/ # YAML nodes (and edges)
├── docs/ # Generated and static Markdown pages (factsheets & graphs)
├── connections/ # Python build/validation scripts
├── mkdocs.yml # MkDocs configuration
├── pyproject.toml # UV requirements and dependency management
└── README.md
```

## Getting Started
See [Contribution docs](docs/devs/contributing.md)

## Commands

```sh
source .venv/bin/activate
tom import  # import csv to yml files
tom yml    # import yml to db
tom md      # generate md files from yml & db
tom serve   # serve mkdocs locally
tom test    # run whatever unit tests there are
tom lint    # run python linter... when it exists
tom clean   # delete old crud so you can start over
tom deploy  # deploy generated mkdocs to prod
```

## Example input
From this section in the Bible (Ruth 1:1-5):

> 1 And it happened in the days when ⌊the judges ruled⌋, there was a famine in the land, and a man from Bethlehem of Judah went ⌊to reside⌋ in the countryside of Moab—he and his wife and his two sons. 2 And the name of the man was Elimelech, and the name of his wife was Naomi, and the names of his two sons were Mahlon and Kilion. They were Ephrathites from Bethlehem in Judah. And they went to the countryside of Moab and remained there. 
> 3 But Elimelech the husband of Naomi died and she was left behind with ⌊her two sons⌋. 4 And ⌊they took⌋ for themselves Moabite wives. The name of the one was Orpah and the name of the other was Ruth. And they lived there about ten years. 5 But ⌊both⌋ Mahlon and Kilion died, and the woman was left without her two sons and without her husband. 

We create this relationship table:
```csv
s_type,s_name,edge_type,t_type,t_name,ref_bible,ref_footnote_anchor,ref_footnote_text
person,Elimelech,mentioned-with,event,plague,Ruth 1:1
person,Elimelech,married-to,person,Naomi,Ruth 1:1-2
person,Elimelech,resident-of,place,Bethlehem,Ruth 1:1-2
place,Bethlehem,member-of,place,Judah,Ruth 1:1
person,Elimelech,visited,place,Moab,Ruth 1:1
person,Naomi,visited,place,Moab,Ruth 1:1
person,Mahlon,visited,place,Moab,Ruth 1:1
person,Kilion,visited,place,Moab,Ruth 1:1
person,Elimelech,parent-of,person,Mahlon,Ruth 1:2
person,Elimelech,parent-of,person,Kilion,Ruth 1:2
person,Naomi,parent-of,person,Mahlon,Ruth 1:2
person,Naomi,parent-of,person,Kilion,Ruth 1:2
person,Mahlon,child-of,person,Elimelech,Ruth 1:2
person,Mahlon,child-of,person,Naomi,Ruth 1:2
person,Kilion,child-of,person,Elimelech,Ruth 1:2
person,Kilion,child-of,person,Naomi,Ruth 1:2
person,Elimelech,died-in,place,Moab,Ruth 1:3
person,Mahlon,married-to,person,Orpah,Ruth 1:4,death_ordering,"In my imagination, Elimelech was alive for the marriage of his son, but the text does not say that explicitly, infact, it seems to indicate he was not involved in the marriage of his sons to foreign women. (Robert Whiting, 2025)."
person,Orpah,married-to,person,Mahlon,Ruth 1:4,death_ordering,"10 years of marriage without children may indicate infertility for both [[person/orpah]] and [[person/ruth]] (Robert Whiting, 2025)."
person,Kilion,married-to,person,Ruth,Ruth 1:4,death_ordering,"In my imagination, Elimelech was alive for the marriage of his son, but the text does not say that explicitly, infact, it seems to indicate he was not involved in the marriage of his sons to foreign women. (Robert Whiting, 2025)."
person,Ruth,married-to,person,Kilion,Ruth 1:4,death_ordering,"10 years of marriage without children may indicate infertility for both [[person/orpah]] and [[person/ruth]] (Robert Whiting, 2025)."
person,Mahlon,died-in,place,Moab,Ruth 1:5
person,Kilion,died-in,place,Moab,Ruth 1:5
```
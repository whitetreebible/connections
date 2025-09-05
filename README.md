# Bible Atlas

**Bible Atlas** is an open, relational knowledge base of biblical figures, places, tribes, and themes. It combines structured YAML data with automatically generated factsheets and graph visualizations to help scholars, students, and enthusiasts explore the Bible in a new way.

## Features

- **Node Factsheets**: Each person, place, or concept has a structured page with references, relationships, and disambiguation notes.
- **Graph Visualizations**: Explore genealogies, tribal affiliations, and thematic connections using Mermaid/Cytoscape graphs.
- **Multi-language Support**: Hebrew, Greek, and English names included for canonical figures.
- **Static Site**: Built with MkDocs and served via GitHub Pages for offline-friendly access.
- **Open Contribution**: YAML-based nodes and edges allow peer-reviewed contributions via GitHub.

## Repo Structure
```sh
bible-atlas/
├── data/ # YAML nodes (and edges)
├── docs/ # Generated Markdown factsheets & graphs
├── scripts/ # Python build/validation scripts
├── mkdocs.yml # MkDocs configuration
├── pyproject.toml # UV requirements and dependency management
└── README.md
```

## Getting Started
See [Contribution docs](docs/devs/contributing.md)


## ToDo List
- make the Mermaid charts easier to read/traverse
- create a way to heal/suggest missing reciprocal links


```
make import_yaml
ls data/person
python bible-atlas/import_external.py tmp/mt1_import.csv
make import_yaml
make generate
make serve

rm data/person/*
git restore data/person/rahab.yml data/person/salmon.yml data/person/boaz.yml
```
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
treebible/connections/
├── data/ # YAML nodes (and edges)
├── docs/ # Generated and static Markdown pages (factsheets & graphs)
├── connections/ # Python build/validation scripts
├── mkdocs.yml # MkDocs configuration
├── pyproject.toml # UV requirements and dependency management
└── README.md
```

## Getting Started
See [Contribution docs](docs/devs/contributing.md)


## ToDo List
- identify a good way to add incrementally instead of rebuilding everything. versions on nodes?
- transition away from makefile, I need a better script runner framework
- create a way to heal/suggest missing reciprocal links
- testing refactor
  - md_generator.py: Refactor to allow passing in a DB or data, and separate graph formatting from DB access.
  - import_yaml.py: Refactor to allow passing in a DB, and separate YAML parsing from DB writing.
  - sqlite_db.py: Consider a repository pattern or interface for DB access, so it can be mocked.
  - EdgeModel/NodeModel: Ensure all logic can be tested with plain Python objects.

```
make import_yaml
python -m bible_atlas.import_external tmp/mt1_import.csv
make import_yaml
make generate
make serve

rm data/person/*
git restore data/person/rahab.yml data/person/salmon.yml data/person/boaz.yml
```
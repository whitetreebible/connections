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
tom yaml    # import yml to db
tom md      # generate md files from yml & db
tom serve   # serve mkdocs locally
tom test    # run whatever unit tests there are
tom lint    # run python linter... when it exists
tom clean   # delete old crud so you can start over
tom deploy  # deploy generated mkdocs to prod
```
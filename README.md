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

1. **Clone the repo**
```sh
git clone https://github.com/whitetreelexicon/bible-atlas.git
cd bible-atlas
```

2. **Install dependencies**
If you don't have it, [install UV first](https://docs.astral.sh/uv/getting-started/installation/)
```sh
uv install
source .venv/bin/activate
```

3. **Serve the web**
```sh
mkdocs serve
```

4. **Deploy the web**
```sh
mkdocs gh-deploy
```
This will build the static site and push it to the gh-pages branch where Github Pages is serving.

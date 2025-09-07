import os
from whitetreebible.connections.md_generator import MdGenerator, MdFormatters
from whitetreebible.connections.models.node_model import NodeModel
from whitetreebible.connections.sqlite_db import SqliteDB

def test_md_generator_creates_md_file_for_boaz(tmp_path):
    # Arrange: create a mock Boaz node
    node_data = {
        "id": "boaz",
        "type": "person",
        "name": {"en": "Boaz"},
        "description": {"en": "A prominent man."}
    }
    node = NodeModel(node_data)
    db = SqliteDB(os.path.join(tmp_path, "test.db"))
    db.insert_node(node, lang="en")
    gen = MdGenerator(db=db, data_dir=str(tmp_path), docs_dir=str(tmp_path))
    # Act: generate markdown
    md_path = os.path.join(tmp_path, "boaz.md")
    content = gen.run_formatters(node, "en")
    with open(md_path, "w") as f:
        f.write(content)
    # Assert: file exists and contains expected content
    with open(md_path) as f:
        out = f.read()
    assert "Boaz" in out
    assert "A prominent man." in out
    db.close()

def test_md_generator_with_association_and_mermaid(tmp_path):
    # Arrange: create Boaz and Rahab with an association
    boaz_data = {
        "id": "boaz",
        "type": "person",
        "name": {"en": "Boaz"},
        "description": {"en": "A prominent man."},
        "edges": [
            {"target": "person/rahab", "type": "married-to"}
        ]
    }
    rahab_data = {
        "id": "rahab",
        "type": "person",
        "name": {"en": "Rahab"},
        "description": {"en": "A woman of Jericho."}
    }
    boaz = NodeModel(boaz_data)
    rahab = NodeModel(rahab_data)
    db = SqliteDB(os.path.join(tmp_path, "test.db"))
    db.insert_node(boaz, lang="en")
    db.insert_node(rahab, lang="en")
    # Insert edge manually if needed by your schema
    db.conn.execute(
        "INSERT INTO edges (source, target, type) VALUES (?, ?, ?)",
        ("person/boaz", "person/rahab", "married-to")
    )
    db.conn.commit()
    gen = MdGenerator(db=db, data_dir=str(tmp_path), docs_dir=str(tmp_path))
    # Act: generate markdown
    content = gen.run_formatters(boaz, "en")
    # Assert: associations and mermaid graph are present
    assert "Rahab" in content
    assert "married" in content.lower()
    assert "mermaid" in content
    # Should have a symmetrical edge (e.g., <--> or -- or both directions)
    assert "<-->|married to|" in content
    db.close()

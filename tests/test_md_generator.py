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

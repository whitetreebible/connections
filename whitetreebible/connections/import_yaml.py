from whitetreebible.connections.logger import log
from whitetreebible.connections.models.node_model import NodeModelCollection
from whitetreebible.connections.settings import DB_PATH, DATA_DIR, SUPPORTED_LANGS
from whitetreebible.connections.sqlite_db import SqliteDB
from tqdm import tqdm
import os

def import_yaml(db: SqliteDB, data_dir: str, clear_existing: bool = True):
    collection = NodeModelCollection(data_dir)
    # delete old db
    if os.path.exists(DB_PATH) and clear_existing:
        os.remove(DB_PATH)
        log.info(f"Deleted old database at {DB_PATH}.")
    db = SqliteDB(DB_PATH)
    nodes = collection.get_nodes()
    log.info(f"Importing {len(nodes)} nodes from {DATA_DIR} into {DB_PATH}...")
    edges = 0
    for node in tqdm(nodes, desc="Importing nodes"):
        for lang in SUPPORTED_LANGS:
            db.insert_node(node=node, lang=lang)
        for edge in node.edges:
            db.insert_edge(source_type=node.type, source_id=node.id, edge=edge)
            edges += 1
    log.info(f"Imported {len(nodes)} nodes and {edges} edges into {DB_PATH}.")



def main():
    db = SqliteDB(DB_PATH)
    import_yaml(db=db, data_dir=DATA_DIR)
    db.close()


    
if __name__ == "__main__":
    main()

import os
from node_model import NodeModelCollection
from sqlite_atlas_db import SqliteAtlasDB
from settings import DB_PATH, DATA_DIR, SUPPORTED_LANGS
from tqdm import tqdm
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def main():
    collection = NodeModelCollection(DATA_DIR)
    # delete old db
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        log.info(f"Deleted old database at {DB_PATH}.")
    db = SqliteAtlasDB(DB_PATH)
    nodes = collection.get_nodes()
    log.info(f"Importing {len(nodes)} nodes from {DATA_DIR} into {DB_PATH}...")
    edges = 0
    for node in tqdm(nodes, desc="Importing nodes"):
        for lang in SUPPORTED_LANGS:
            db.insert_node(node=node, lang=lang)
        for edge in node.edges:
            db.insert_edge(source_type=node.type, source_id=node.id, edge=edge)
            edges += 1
    db.close()
    log.info(f"Imported {len(nodes)} nodes and {edges} edges into {DB_PATH}.")

    
if __name__ == "__main__":
    main()

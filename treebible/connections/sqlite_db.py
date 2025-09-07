import sqlite3
from treebible.connections.models.node_model import NodeModel, NodeModelCollection
from treebible.connections.models.edge_model import EdgeModel
from treebible.connections.models.edge_type import EdgeType
from treebible.connections.settings import SUPPORTED_LANGS, DB_PATH, DATA_DIR
import os

class SqliteDB:
    
    def __init__(self, db_path=DB_PATH):
        # if the db path does not exist, create it
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path))
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def traverse_edges(self, start_node_link: str, direction: str = "both", types: list[EdgeType] = None, max_depth: int = None) -> set[EdgeModel]:
        """
        Recursively get all edges from or to start_id within a list of types up to max_depth.
        direction: 'out', 'in', or 'both'
        types: list of edge types to include (None or ['*'] for all)
        max_depth: int or None for infinite
        Returns a set of (source, target, type)
        """
        visited_nodes = set()
        collected_edges = set()
        queue = [(start_node_link, 0)]
        while queue:
            current_id, depth = queue.pop(0)
            if max_depth is not None and depth > max_depth:
                continue
            if (current_id, depth) in visited_nodes:
                continue
            visited_nodes.add((current_id, depth))
            # Outgoing edges
            if direction in ("out", "both"):
                cur = self.conn.cursor()
                if types:
                    types_arr = [t.value if isinstance(t, EdgeType) else t for t in types]
                    q = "SELECT source, target, type FROM edges WHERE source = ? AND type IN ({})".format(
                        ",".join(["?" for _ in types])
                    )
                    cur.execute(q, (current_id, *types_arr))
                else:
                    cur.execute("SELECT source, target, type FROM edges WHERE source = ?", (current_id,))
                for row in cur.fetchall():
                    edge = EdgeModel.from_row(row)
                    if edge not in collected_edges:
                        collected_edges.add(edge)
                        queue.append((edge.target, depth + 1))
            # Incoming edges
            if direction in ("in", "both"):
                cur = self.conn.cursor()
                if types:
                    types_arr = [t.value if isinstance(t, EdgeType) else t for t in types]
                    q = "SELECT source, target, type FROM edges WHERE target = ? AND type IN ({})".format(
                        ",".join(["?" for _ in types])
                    )
                    cur.execute(q, (current_id, *types_arr))
                else:
                    cur.execute("SELECT source, target, type FROM edges WHERE target = ?", (current_id,))
                for row in cur.fetchall():
                    edge = EdgeModel.from_row(row)
                    if edge not in collected_edges:
                        collected_edges.add(edge)
                        queue.append((edge.source, depth + 1))
        return collected_edges
    
    
    def select_name(self, node_type: str, node_id: str, lang: str = "en") -> str:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT name FROM nodes WHERE id = ? AND type = ? AND lang = ?",
            (node_id, node_type, lang)
        )
        row = cur.fetchone()
        return row[0] if row else None

    def select_edges(self, node_id: str) -> list:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT source, target, type FROM edges WHERE source = ?",
            (node_id,)
        )
        return cur.fetchall()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT,
                type TEXT,
                lang TEXT,
                name TEXT,
                name_disambiguous TEXT,
                PRIMARY KEY (id, type, lang)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                target TEXT,
                type TEXT
            )
        ''')
        self.conn.commit()

    def insert_node(self, node: NodeModel, lang="en"):
        name = node.name.get(lang, next(iter(node.name.values()), node.id))
        self.conn.execute(
            "INSERT OR REPLACE INTO nodes (id, type, lang, name, name_disambiguous) VALUES (?, ?, ?, ?, ?)",
            (node.id, node.type, lang, name, node.name_disambiguous.get(lang))
        )
        self.conn.commit()

    def insert_edge(self, source_type: str, source_id: str, edge: EdgeModel):
        self.conn.execute(
            "INSERT INTO edges (source, target, type) VALUES (?, ?, ?)",
            (f"{source_type}/{source_id}", edge.target, edge.type.value)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    # Example usage: collect all nodes/edges and insert into DB
    collector = NodeModelCollection(DATA_DIR)
    db = SqliteDB(DB_PATH)
    for node in collector.get_nodes():
        for lang in SUPPORTED_LANGS:
            db.insert_node(node, lang=lang)
        for edge in node.edges:
            db.insert_edge(node.type, node.id, edge)
    db.close()

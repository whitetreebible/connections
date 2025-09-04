from sqlite_atlas_db import SqliteAtlasDB
"""
Script to process a CSV with columns: node_type, source, target, edge_type.
For each row, verifies that source and target nodes exist (creates if missing),
adds the specified edge, and adds a reciprocal edge if appropriate.

Usage:
    python import_external.py <edges.csv>
CSV example:
    person, Seth, Enos, parent-of
    person, Enos, Seth, child-of
"""
import sys
import csv
from node_model import NodeModel, EdgeModel
from associations import RECIPROCALS
import os
import inquirer
from logger import log


def lookup_similar_nodes(node_type: str, name: str) -> list:
    """
    Try to find similar nodes by name using the DB if available, else scan YAML files.
    Returns a list of (id, type, name, name_disambiguous) dicts.
    """
    results = []
    # Try DB first
    try:
        db = SqliteAtlasDB()
        cur = db.conn.cursor()
        # Case-insensitive substring match
        cur.execute("SELECT id, type, name, name_disambiguous FROM nodes WHERE type = ? AND LOWER(name) LIKE ?", (node_type, f"%{name.lower()}%"))
        for row in cur.fetchall():
            results.append({"id": row[0], "type": row[1], "name": row[2], "name_disambiguous": row[3]})
    except Exception:
        db = None
    # Fallback: scan YAML files
    if not results:
        data_dir = os.path.join(DATA_DIR, node_type.lower())
        if os.path.exists(data_dir):
            for fname in os.listdir(data_dir):
                if fname.endswith('.yml') or fname.endswith('.yaml'):
                    path = os.path.join(data_dir, fname)
                    try:
                        node = NodeModel.from_yaml_file(path)
                        n_en = node.name.get('en', '').lower()
                        n_disamb = node.name_disambiguous.get('en', '') if hasattr(node, 'name_disambiguous') else ''
                        if name.lower() in n_en or name.lower() in n_disamb.lower():
                            results.append({"id": node.id, "type": node.type, "name": n_en, "name_disambiguous": n_disamb})
                    except Exception:
                        continue
    return results




DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))

def get_node_yaml_path(node_type, node_id):
    # Assumes node_type is pluralized as folder, id is filename
    folder = node_type.lower()
    return os.path.join(DATA_DIR, folder, f"{node_id}.yml")



# def get_or_create_node(node_type: str, name: str, bible_ref: str, context: str) -> tuple[NodeModel, str]:
#     # Look for similar nodes
#     matches = lookup_similar_nodes(node_type, name)
#     node_id = name.lower()
#     if matches:
#         choices = []
#         for m in matches:
#             label = f"{m['type']}/{m['id']}"
#             if m.get('name_disambiguous'):
#                 label += f" {m['name_disambiguous']}"
#             choices.append((label, m['id']))
#         if name.lower() in [m['name'].lower() for m in matches]:
#             node_id = f"{node_id}_{bible_ref.lower().replace(' ', '_').replace(':', '_')}"
#         choices.append((f"Create new: {node_type}/{node_id}", None))
#         answer = inquirer.list_input(f"Which {name} is in {bible_ref} ({context})?", choices=choices)
#         if answer:
#             # Load the selected node
#             if answer in [m['id'] for m in matches]:
#                 node_id = answer
#                 yaml_path = get_node_yaml_path(node_type, node_id)
#                 node = NodeModel.from_yaml_file(yaml_path)
#                 return node, yaml_path
#     # Default: create new node
#     yaml_path = get_node_yaml_path(node_type, node_id)
#     node = NodeModel({"id": node_id, "type": node_type, "name": {"en": name}, "edges": []})
#     log.info(f"Creating new node: {node_type}/{node_id}")
#     return node, yaml_path

# Cache for disambiguation prompts: {(node_type, name, bible_ref): node_id}
_disambig_cache = {}

def get_or_create_node(node_type: str, name: str, bible_ref: str, context: str) -> tuple[NodeModel, str]:
    cache_key = (node_type, name, bible_ref)
    if cache_key in _disambig_cache:
        node_id = _disambig_cache[cache_key]
        yaml_path = get_node_yaml_path(node_type, node_id)
        node = NodeModel.from_yaml_file(yaml_path) if os.path.exists(yaml_path) else NodeModel({"id": node_id, "type": node_type, "name": {"en": name}, "edges": []})
        return node, yaml_path
    # Look for similar nodes
    matches = lookup_similar_nodes(node_type, name)
    node_id = name.lower()
    if matches:
        choices = []
        for m in matches:
            label = f"{m['type']}/{m['id']}"
            if m.get('name_disambiguous'):
                label = f"{m['name_disambiguous']}"
            choices.append((label, m['id']))
        if name.lower() in [m['name'].lower() for m in matches]:
            node_id = f"{node_id}_{bible_ref.lower().replace(' ', '_').replace(':', '_')}"
        choices.append((f"Create new: {node_type}/{node_id}", None))
        answer = inquirer.list_input(f"Which {name} is in {bible_ref} ({context})?", choices=choices)
        if answer:
            # Load the selected node
            if answer in [m['id'] for m in matches]:
                node_id = answer
                _disambig_cache[cache_key] = node_id
                yaml_path = get_node_yaml_path(node_type, node_id)
                node = NodeModel.from_yaml_file(yaml_path)
                return node, yaml_path
    # Default: create new node
    _disambig_cache[cache_key] = node_id
    yaml_path = get_node_yaml_path(node_type, node_id)
    node = NodeModel({"id": node_id, "type": node_type, "name": {"en": name}, "edges": []})
    log.info(f"New node: {node_type}/{node_id}")
    return node, yaml_path



def main():
    if len(sys.argv) < 2:
        print("Usage: python import_external.py <edges.csv>")
        sys.exit(1)
    file_path = sys.argv[1]
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=["node_type", "source", "target", "edge_type", "bible_ref"])
        for row in reader:
            # skip header
            if row["node_type"] == "node_type":
                continue
            node_type = row["node_type"].strip()
            source = row["source"].strip()
            target = row["target"].strip()
            edge_type = row["edge_type"].strip()
            bible_ref = row["bible_ref"].strip()
            
            # Get or create source and target nodes 
            source_node, source_path = get_or_create_node(node_type, source, bible_ref, context=f"{source} {edge_type} {target}")
            target_node, target_path = get_or_create_node(node_type, target, bible_ref, context=f"{source} {edge_type} {target}")
            edge_ref = f"bible:{bible_ref}"
            # Check for existing edge in source_node
            found = False
            for edge in source_node.edges:
                if edge.target == target_node.link and edge.type == edge_type:
                    if edge_ref not in edge.refs:
                        edge.refs.append(edge_ref)
                    found = True
                    break
            if not found:
                edge_data = {"target": target_node.link, "type": edge_type, "weight": 1.0, "refs": [edge_ref]}
                source_node.edges.append(EdgeModel(edge_data))
            # Add reciprocal edge if defined
            if edge_type in RECIPROCALS:
                reciprocal = RECIPROCALS[edge_type]
                recip_found = False
                for edge in target_node.edges:
                    if edge.target == source_node.link and edge.type == reciprocal:
                        if edge_ref not in edge.refs:
                            edge.refs.append(edge_ref)
                        recip_found = True
                        break
                if not recip_found:
                    recip_edge_data = {"target": source_node.link, "type": reciprocal, "weight": 1.0, "refs": [edge_ref]}
                    target_node.edges.append(EdgeModel(recip_edge_data))
            # Save updated YAML
            source_str = source_node.to_yaml()
            target_str = target_node.to_yaml()
            log.info(f"New edge: {source_node.link} {edge_type} {target_node.link}")
            # write updated YAML back to files
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(source_str)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(target_str)
    print("Nodes and edges updated in YAML files from CSV.")

if __name__ == "__main__":
    main()

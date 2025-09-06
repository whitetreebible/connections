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
from bible_atlas.sqlite_db import SqliteDB
import sys
import csv
from .models.node_model import NodeModel, EdgeModel
from .models.edge_type import EdgeType, RECIPROCALS
import os
import inquirer
from logger import log


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))

_disambig_cache = {}


def lookup_similar_nodes(node_type: str, name: str) -> list:
    """
    Try to find similar nodes by name using the DB if available, else scan YAML files.
    Returns a list of (id, type, name, name_disambiguous) dicts.
    If name_disambiguous is empty, construct it from name and first edge, or fallback to type/id.
    """
    results = []
    # Try DB first
    try:
        db = SqliteDB()
        cur = db.conn.cursor()
        # Case-insensitive substring match
        cur.execute("SELECT id, type, name FROM nodes WHERE type = ? AND LOWER(name) LIKE ?", (node_type, f"%{name.lower()}%"))
        for row in cur.fetchall():
            node_id, ntype, n_en = row[0], row[1], row[2]
            # Try to get name_disambiguous from YAML if possible
            yaml_path = get_node_yaml_path(ntype, node_id)
            n_disamb = ''
            if os.path.exists(yaml_path):
                try:
                    node = NodeModel.from_yaml_file(yaml_path)
                    n_disamb = node.name_disambiguous.get('en', '') if hasattr(node, 'name_disambiguous') else ''
                    if not n_disamb:
                        # Try to construct from first edge
                        if node.edges:
                            first_edge = node.edges[0]
                            n_disamb = format_disambiguous_from_edge(node_id, n_en, first_edge.type, first_edge.target)
                        else:
                            n_disamb = format_disambiguous_from_edge(node_id, n_en, '', '')
                except Exception:
                    n_disamb = n_en or f"{ntype}/{node_id}"
            else:
                n_disamb = n_en or f"{ntype}/{node_id}"
            results.append({"id": node_id, "type": ntype, "name": n_en, "name_disambiguous": n_disamb})
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
                        n_en = node.name.get('en', '')
                        n_disamb = node.name_disambiguous.get('en', '') if hasattr(node, 'name_disambiguous') else ''
                        if not n_disamb:
                            # Try to construct from first edge
                            if node.edges:
                                first_edge = node.edges[0]
                                n_disamb = format_disambiguous_from_edge(node.id, n_en, first_edge.type, first_edge.target)
                            else:
                                n_disamb = format_disambiguous_from_edge(node.id, n_en, '', '')
                        if name.lower() in n_en or name.lower() in n_disamb.lower():
                            results.append({"id": node.id, "type": node.type, "name": n_en, "name_disambiguous": n_disamb})
                    except Exception:
                        continue
    return results



def format_disambiguous_from_edge(node_id, name, edge_type:EdgeType, edge_target) -> str:
    if not name:
        name = node_id.capitalize()
    if not edge_type:
        return name
    # split the edge_target on '/' and take last part
    edge_type = edge_type.replace('-', ' ')
    if '/' in edge_target:
        edge_target = edge_target.split('/')[-1]
    edge_target = edge_target.replace('-', ' ').capitalize()
    return f"{name} ({edge_type} {edge_target})"



def get_node_yaml_path(node_type, node_id):
    """Helper to get the YAML file path for a node by type and id."""
    data_dir = os.path.join(DATA_DIR, node_type.lower())
    for ext in ('.yml', '.yaml'):
        path = os.path.join(data_dir, f"{node_id}{ext}")
        if os.path.exists(path):
            return path
    return os.path.join(data_dir, f"{node_id}.yml")



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
        choices.append((f"Create new: {name} ({node_type}/{node_id})", None))
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
            readable_edge = edge_type.replace('-', ' ')
            context = f"{source} {readable_edge} {target}"
            source_node, source_path = get_or_create_node(node_type, source, bible_ref, context=context)
            target_node, target_path = get_or_create_node(node_type, target, bible_ref, context=context)
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
                edge_data = {"target": target_node.link, "type": edge_type, "refs": [edge_ref]}
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
                    recip_edge_data = {"target": source_node.link, "type": reciprocal, "refs": [edge_ref]}
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

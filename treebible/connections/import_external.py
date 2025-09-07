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
from treebible.connections.logger import log
from treebible.connections.models.edge_type import EdgeType, RECIPROCALS
from treebible.connections.models.node_model import NodeModel, EdgeModel
from treebible.connections.sqlite_db import SqliteDB
import csv
import inquirer
import os
import sys


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))

_disambig_cache = {}


def lookup_similar_nodes(node_type: str, name: str) -> list:
    """
    Try to find similar nodes by name using the DB if available, else scan YAML files.
    Returns a list of (id, type, name, name_disambiguous) dicts.
    If name_disambiguous is empty, construct it from name and first edge, or fallback to type/id.
    """
    results = []
    name_norm = name.strip().lower()
    seen_ids = set()
    # Always check DB
    try:
        db = SqliteDB()
        cur = db.conn.cursor()
        cur.execute("SELECT id, type, name FROM nodes WHERE type = ?", (node_type,))
        for row in cur.fetchall():
            node_id, ntype, n_en = row[0], row[1], row[2]
            node_id_norm = str(node_id).strip().lower()
            n_en_norm = str(n_en).strip().lower()
            if name_norm == node_id_norm or name_norm == n_en_norm:
                yaml_path = get_node_yaml_path(ntype, node_id)
                n_disamb = ''
                if os.path.exists(yaml_path):
                    try:
                        node = NodeModel.from_yaml_file(yaml_path)
                        n_disamb = node.name_disambiguous.get('en', '') if hasattr(node, 'name_disambiguous') else ''
                        if not n_disamb:
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
                seen_ids.add((ntype, node_id_norm))
    except Exception as e:
        log.warning(f"DB lookup failed: {e}")
    # Always check YAML files
    data_dir = os.path.join(DATA_DIR, node_type.lower())
    if os.path.exists(data_dir):
        for fname in os.listdir(data_dir):
            if fname.endswith('.yml') or fname.endswith('.yaml'):
                path = os.path.join(data_dir, fname)
                node_id_from_file = os.path.splitext(fname)[0].strip().lower()
                try:
                    node = NodeModel.from_yaml_file(path)
                    n_en = node.name.get('en', '')
                    n_en_norm = n_en.strip().lower()
                    n_disamb = node.name_disambiguous.get('en', '') if hasattr(node, 'name_disambiguous') else ''
                    if not n_disamb:
                        if node.edges:
                            first_edge = node.edges[0]
                            n_disamb = format_disambiguous_from_edge(node.id, n_en, first_edge.type, first_edge.target)
                        else:
                            n_disamb = format_disambiguous_from_edge(node.id, n_en, '', '')
                    # Match on filename or name_en
                    if (name_norm == node_id_from_file or name_norm == n_en_norm) and (node.type, node_id_from_file) not in seen_ids:
                        results.append({"id": node.id, "type": node.type, "name": n_en, "name_disambiguous": n_disamb})
                        seen_ids.add((node.type, node_id_from_file))
                except Exception as e:
                    log.warning(f"YAML lookup failed for {fname}: {e}")
    log.info(f"lookup_similar_nodes('{node_type}', '{name}') found {len(results)} matches: {[r['id'] for r in results]}")
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
    log.info(f"Looking up {node_type} named '{name}' found {len(matches)} matches.")
    node_id = name.lower()
    if matches:
        choices = []
        create_new_label = f"Create new: {name} ({node_type}/{node_id})"
        for m in matches:
            label = f"{m['type']}/{m['id']}"
            if m.get('name_disambiguous'):
                label = f"{m['name_disambiguous']}"
            choices.append((label, m['id']))
        choices.append((create_new_label, None))
        answer = inquirer.list_input(f"Which {name} is in {bible_ref} ({context})?", choices=choices)
        # Robustly detect 'Create new' selection (None or label string)
        if answer in [m['id'] for m in matches]:
            node_id = answer
            _disambig_cache[cache_key] = node_id
            yaml_path = get_node_yaml_path(node_type, node_id)
            node = NodeModel.from_yaml_file(yaml_path)
            return node, yaml_path
        if answer is None or (isinstance(answer, str) and answer.startswith('Create new:')):
            default_id = f"{node_id}_{bible_ref.lower().replace(' ', '_').replace(':', '_')}"
            new_id = inquirer.text(message=f"Please provide a disambiguated id for new '{name}' in {node_type} (e.g., lamech_murderer):", default=default_id)
            if new_id:
                node_id = new_id.strip()
                _disambig_cache[cache_key] = node_id
            else:
                node_id = default_id
    # Default: create new node
    _disambig_cache[cache_key] = node_id
    yaml_path = get_node_yaml_path(node_type, node_id)
    # Set a meaningful disambiguated name if possible
    disamb = f"{name} ({context})" if context else name
    node = NodeModel({
        "id": node_id,
        "type": node_type,
        "name": {"en": name},
        "name_disambiguous": {"en": disamb},
        "edges": []
    })
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
            edge_type = EdgeType(row["edge_type"].strip())
            bible_ref = row["bible_ref"].strip()
            
            # Get or create source and target nodes 
            readable_edge = edge_type.for_lang(lang="en")
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
                    edge_type_val = edge.type.value if hasattr(edge.type, 'value') else edge.type
                    if edge.target == source_node.link and edge_type_val == reciprocal:
                        if edge_ref not in edge.refs:
                            edge.refs.append(edge_ref)
                        recip_found = True
                        break
                if not recip_found:
                    recip_edge_data = {"target": source_node.link, "type": reciprocal, "refs": [edge_ref]}
                    target_node.edges.append(EdgeModel(recip_edge_data))
            # Save updated YAML (write only once after all edge modifications)
            source_str = source_node.to_yaml()
            target_str = target_node.to_yaml()
            log.info(f"New edge: {source_node.link} {edge_type} {target_node.link}")
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(source_str)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(target_str)
    print("Nodes and edges updated in YAML files from CSV.")

if __name__ == "__main__":
    main()
